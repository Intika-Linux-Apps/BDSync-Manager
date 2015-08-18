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
import tempfile
import time

import plumbum

LVM_SIZE_REGEX = re.compile(r"^[0-9]+[bBsSkKmMgGtTpPeE]?$")
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
    output = plumbum.local[cmd_args[0]](cmd_args[1:])
    # remove linebreaks from result
    return output.rstrip("\n\r")


def sizeof_fmt(num, suffix='B'):
    # source: http://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def run_bdsync(source, target, target_patch_dir, connection_command, local_bdsync, remote_bdsync, bdsync_args):
    log.info("Creating binary patch")
    if connection_command:
        # prepend the connection command
        remote_command = "%s %s --server" % (connection_command, shlex.quote(remote_bdsync))
        remote_patch_file = get_remote_tempfile(connection_command, target, target_patch_dir)
        log.debug("Using remote temporary patch file: %s" % str(remote_patch_file))
        output_command_args = shlex.split(connection_command)
        output_command_args.append("cat > %s" % shlex.quote(remote_patch_file))
        log.debug("Using remote patch transfer: %s" % str(output_command_args))
        output_command = plumbum.local[output_command_args[0]][tuple(output_command_args[1:])]
        patch_size_command = shlex.split(connection_command)
        # "stat --format %s" returns the size of the file in bytes
        patch_size_command.append("stat --format %%s %s" % shlex.quote(remote_patch_file))
        patch_size_func = plumbum.local[patch_size_command[0]][tuple(patch_size_command[1:])]
    else:
        remote_command = "%s --server" % shlex.quote(remote_bdsync)
        local_patch_file = tempfile.NamedTemporaryFile(dir=target_patch_dir, delete=False)
        patch_size_func = lambda: os.path.getsize(local_patch_file.name)
        output_command = None
    # run bdsync and handle the resulting states
    args = []
    args.append(local_bdsync)
    if bdsync_args:
        args.extend(shlex.split(bdsync_args))
    args.append(remote_command)
    args.append(source)
    args.append(target)
    patch_source = plumbum.local[args[0]][args[1:]]
    patch_create_start_time = time.time()
    if connection_command:
        chain = patch_source | output_command
    else:
        chain = patch_source > local_patch_file
    log.debug("Starting local bdsync process: %s" % str(args))
    chain()
    patch_create_time = datetime.timedelta(seconds=(time.time() - patch_create_start_time))
    log.debug("bdsync successfully created and transferred a binary patch")
    log.info("Patch Create Time: %s" % patch_create_time)
    log.info("Patch Size: %s" % sizeof_fmt(int(patch_size_func())))
    patch_apply_start_time = time.time()
    # everything went fine - now the patch should be applied
    if connection_command:
        patch_source = None
        bdsync_args = shlex.split(connection_command)
        bdsync_args.append("%s --patch < %s" % (shlex.quote(remote_bdsync), shlex.quote(remote_patch_file)))
        apply_patch = plumbum.local[bdsync_args[0]][tuple(bdsync_args[1:])]
    else:
        local_patch_file.seek(0)
        patch_source = local_patch_file
        apply_patch = plumbum.local[local_bdsync]["--patch"]
    log.debug("Applying the patch")
    log.debug("bdsync patching: %s" % str(apply_patch))
    apply_patch()
    patch_apply_time = datetime.timedelta(seconds=(time.time() - patch_apply_start_time))
    log.debug("Successfully applied the patch")
    log.info("Patch Apply Time: %s" % patch_apply_time)
    if connection_command:
        # remove remote patch file
        remove_args = shlex.split(connection_command)
        remove_args.append("rm %s" % shlex.quote(remote_patch_file))
        log.debug("Removing the remote temporary patch file: %s" % str(remove_args))
        plumbum.local[remove_args[0]](remove_args[1:])
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
