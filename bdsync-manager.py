#!/usr/bin/env python3

"""

Config file format:

    [DEFAULT]
    local_bdsync_bin = /usr/local/bin/bdsync
    remote_bdsync_bin = /usr/local/bin/bdsync
    connection_command = ssh -p 2200 foo@target
    target_patch_dir = /tmp
    bdsync_args = --hash=sha1

    [lvm-foo/example-root]
    source_path = /dev/lvm-foo/example-root
    target_path = backup/example-root
    lvm_snapshot_enabled = yes
    lvm_snapshot_size = 5G
    lvm_snapshot_name_suffix = _snapshot

"""

import argparse
import configparser
import datetime
import logging
import os
import re
import shlex
import subprocess
import tempfile
import time

LVM_SIZE_REGEX = re.compile(r"^[0-9]+[bBsSkKmMgGtTpPeE]?$")
TERMINAL_ENCODING = "utf-8"
BDSYNC_REMOTE_TARGET_MISSING_REGEX = re.compile(r"^get_rd_queue: EOF 6$", flags=re.MULTILINE)


class TaskProcessingError(Exception): pass


def load_settings(config):
    # load and validate settings
    settings = {}
    try:
        settings["local_bdsync_bin"] = config["local_bdsync_bin"]
        settings["remote_bdsync_bin"] = config["remote_bdsync_bin"]
        settings["bdsync_args"] = config.get("bdsync_args", None)
        settings["source_path"] = config["source_path"]
        settings["target_path"] = config["target_path"]
        settings["connection_command"] = config.get("connection_command", None)
        settings["target_patch_dir"] = config.get("target_patch_dir", None)
        lvm_snapshot_enabled = config.getboolean("lvm_snapshot_enabled", False)
        if lvm_snapshot_enabled:
            lvm_snapshot_size = config["lvm_snapshot_size"]
            if not LVM_SIZE_REGEX.match(lvm_snapshot_size):
                raise TaskProcessingError("Invalid LVM snapshot size (%s)" % lvm_snapshot_size)
            lvm_snapshot_name_suffix = config.get("lvm_snapshot_name_suffix", "_snapshot")
            settings["lvm"] = {
                    "snapshot_size": lvm_snapshot_size,
                    "snapshot_name_suffix": lvm_snapshot_name_suffix,
            }
    except configparser.NoOptionError as exc:
        raise TaskProcessingError("Missing a mandatory task option: %s" % str(exc))
    return settings


def validate_settings(settings):
    # validate input
    if not os.path.isfile(settings["local_bdsync_bin"]):
        raise TaskProcessingError("The local 'bdsync' binary was not found (%s)." % settings["local_bdsync_bin"])
    if not os.path.exists(settings["source_path"]):
        raise TaskProcessingError("The source device (source_path=%s) does not exist" % settings["source_path"])
    if not settings["connection_command"]:
        # local transfer
        if not os.path.exists(os.path.dirname(settings["target_path"])):
            raise TaskProcessingError("The directory of the local target (target_path=%s) does not exist" % \
                    settings["target_path"])
        if not os.path.isdir(settings["target_patch_dir"]):
            raise TaskProcessingError("The patch directory of the local target (target_patch_dir=%s) does not exist" % \
                    settings["target_patch_dir"])


def get_remote_tempfile(connection_command, target, directory):
    cmd_args = shlex.split(connection_command)
    cmd_args.append("mktemp --tmpdir=%s %s-XXXX.bdsync" % (shlex.quote(directory), shlex.quote(os.path.basename(target))))
    try:
        output = subprocess.check_output(cmd_args)
    except subprocess.CalledProcessError as exc:
        raise TaskProcessingError("Failed to generate remote temporary file: %s" % str(exc))
    # remove linebreaks from result
    return output.decode(TERMINAL_ENCODING).rstrip("\n\r")


def _get_pipe_output(pipe):
    return pipe.read().decode(pipe.encoding)


def sizeof_fmt(num, suffix='B'):
    # source: http://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def run_bdsync(source, target, target_patch_dir, connection_command, local_bdsync, remote_bdsync, bdsync_args):
    if connection_command:
        # prepend the connection command
        remote_command = "%s %s --server" % (connection_command, shlex.quote(remote_bdsync))
        remote_patch_file = get_remote_tempfile(connection_command, target, target_patch_dir)
        log.debug("Using remote temporary patch file: %s" % str(remote_patch_file))
        output_command_args = shlex.split(connection_command)
        output_command_args.append("cat > %s" % shlex.quote(remote_patch_file))
        log.debug("Starting remote patch transfer: %s" % str(output_command_args))
        try:
            output_process = subprocess.Popen(output_command_args, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as exc:
            raise TaskProcessingError("Failed to store remote patch file: %s" % str(exc))
    else:
        remote_command = "%s --server" % shlex.quote(remote_bdsync)
        local_patch_file = tempfile.NamedTemporaryFile(dir=target_patch_dir, delete=False)
        output_process = None
    # run bdsync and handle the resulting states
    args = []
    args.append(local_bdsync)
    if bdsync_args:
        args.extend(shlex.split(bdsync_args))
    args.append(remote_command)
    args.append(source)
    args.append(target)
    patch_create_start_time = time.time()
    log.debug("Starting local bdsync process: %s" % str(args))
    try:
        if connection_command:
            bdsync = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=output_process.stdin, stderr=subprocess.PIPE)
        else:
            bdsync = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise TaskProcessingError("Failed to start bdsync: %s" % str(exc))
    if connection_command and (output_process.wait() != 0):
        raise TaskProcessingError("Failed to transfer the patch file (exitcode=%d): %s" % \
                (output_process.returncode, _get_pipe_output(output_process.stderr)))
    if bdsync.wait() != 0:
        if (bdsync.returncode == 1) and BDSYNC_REMOTE_TARGET_MISSING_REGEX.search(error_output):
            raise TaskProcessingError("The target (%s) is missing: please copy it manually first" % target)
        else:
            raise TaskProcessingError("bdsync failed (exitcode=%d): %s" % (bdsync.returncode, _get_pipe_output(bdsync.stderr)))
    patch_create_time = datetime.timedelta(seconds=(time.time() - patch_create_start_time))
    log.info("bdsync successfully created and transferred a binary patch")
    if not connection_command:
        log.info("Patch Size: %s" % sizeof_fmt(os.path.getsize(local_patch_file.name)))
    log.info("Patch Create Time: %s" % patch_create_time)
    patch_apply_start_time = time.time()
    # everything went fine - now the patch should be applied
    if connection_command:
        patch_source = None
        bdsync_args = shlex.split(connection_command)
        bdsync_args.append("%s --patch < %s" % (shlex.quote(remote_bdsync), shlex.quote(remote_patch_file)))
    else:
        local_patch_file.seek(0)
        patch_source = local_patch_file
        bdsync_args = [local_bdsync, "--patch"]
    log.info("Applying the patch")
    log.debug("bdsync patch arguments: %s" % str(bdsync_args))
    try:
        bdsync = subprocess.Popen(bdsync_args, stdin=patch_source, stderr=subprocess.PIPE)
    except OSError as exc:
        raise TaskProcessingError("Failed to run bdsync patch process: %s" % str(exc))
    if bdsync.wait() != 0:
        raise TaskProcessingError("Failed to patch target (exitcode=%d): %s" % \
                (bdsync.returncode, _get_pipe_output(bdsync.stderr)))
    patch_apply_time = datetime.timedelta(seconds=(time.time() - patch_apply_start_time))
    log.info("Successfully applied the patch")
    log.info("Patch Apply Time: %s" % patch_apply_time)
    if connection_command:
        # remove remote patch file
        remove_args = shlex.split(connection_command)
        remove_args.append("rm %s" % shlex.quote(remote_patch_file))
        log.debug("Removing the remote temporary patch file: %s" % str(remove_args))
        try:
            remove_process = subprocess.Popen(remove_args, stderr=subprocess.PIPE)
        except OSError as exc:
            raise TaskProcessingError("Failed to execute remote patch removal: %s" % str(exc))
        if remove_process.wait() != 0:
            raise TaskProcessingError("Failed to remove remote patch file (exitcode=%d): %s" % \
                    (remove_process.returncode, _get_pipe_output(remove_process.stderr)))
    else:
        os.unlink(bdsync_out.name)


def process_task(config):
    settings = load_settings(config)
    validate_settings(settings)
    # everything looks fine - we can start
    if "lvm" in settings:
        real_source = prepare_lvm_snapshot(settings["source_path"],
                settings["lvm"]["snapshot_size"], settings["lvm"]["snapshot_name_suffix"])
    else:
        real_source = settings["source_path"]
    try:
        run_bdsync(real_source, settings["target_path"], settings["target_patch_dir"],
                settings["connection_command"], settings["local_bdsync_bin"], settings["remote_bdsync_bin"], settings["bdsync_args"])
    finally:
        if "lvm" in settings:
            cleanup_lvm_snapshot(real_source)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Manage one or more bdsync transfers.")
    parser.add_argument("--log-level", dest="log_level", default="info",
            choices=("debug", "info", "warning", "error"), help="Output verbosity")
    parser.add_argument("--config", metavar="CONFIG_FILE", dest="config_file",
            default="/etc/bdsync-manager.conf", type=argparse.FileType('r'),
            help="Location of the config file")
    parser.add_argument("--task", metavar="TASK_NAME", dest="tasks", action="append")
    args = parser.parse_args()
    log_levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
    }
    log.setLevel(log_levels[args.log_level])
    return args


def _get_safe_string(text):
    return re.sub(r"\W", "_", text)


if __name__ == "__main__":
    log = logging.getLogger("bdsync-manager")
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter("[bdsync-manager] %(asctime)s - %(message)s"))
    log_handler.setLevel(logging.DEBUG)
    log.addHandler(log_handler)
    log.debug("Parsing arguments")
    args = parse_arguments()
    config = configparser.ConfigParser()
    log.debug("Reading config file: %s" % str(args.config_file.name))
    config.read_file(args.config_file)
    if args.tasks:
        tasks = []
        for task in args.tasks:
            if task in config.sections():
                tasks.append(task)
            else:
                log.warning("Skipping unknown task: %s" % _get_safe_string(task))
    else:
        tasks = config.sections()
    if not tasks:
        log.warning("There is nothing to be done (no tasks found in config file).")
    for task in tasks:
        log_handler.setFormatter(logging.Formatter("[Task '%s'] %%(levelname)s: %%(message)s" % str(task)))
        try:
            process_task(config[task])
        except TaskProcessingError as exc:
            log.error(str(exc))
