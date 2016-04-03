"""
    bdsync-manager: maintain synchronization tasks for remotely or locally synchronized blockdevices via bdsync

    Copyright (C) 2015-2016 Lars Kruse <devel@sumpfralle.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import os
import shlex
import tempfile
import time

import plumbum

import bdsync_manager.utils
log = bdsync_manager.utils.get_logger()


class Task:

    def __init__(self, config_dict):
        self.settings = dict(config_dict)

    def run(self):
        if self.settings["disabled"]:
            log.info("Skipping disabled task")
            return
        if "lvm" in self.settings:
            lvm_volume = self.settings["lvm"]["caller"].get_volume(self.settings["lvm"]["vg_name"],
                                                                   self.settings["source_path"])
            real_source = lvm_volume.get_snapshot(self.settings["lvm"]["snapshot_name"],
                                                  self.settings["lvm"]["snapshot_size"])
        else:
            real_source = self.settings["source_path"]
        try:
            run_bdsync(real_source, self.settings["target_path"], self.settings["target_patch_dir"],
                       self.settings["connection_command"], self.settings["local_bdsync_bin"],
                       self.settings["remote_bdsync_bin"], self.settings["bdsync_args"])
        finally:
            if "lvm" in self.settings:
                lvm_volume.remove_snapshot()


def run_bdsync(source, target, target_patch_dir, connection_command, local_bdsync, remote_bdsync, bdsync_args):
    log.info("Creating binary patch")
    if connection_command:
        # prepend the connection command
        remote_command = "%s %s --server" % (connection_command, shlex.quote(remote_bdsync))
        remote_patch_file = bdsync_manager.utils.get_remote_tempfile(connection_command, target,
                                                                     target_patch_dir)
        log.debug("Using remote temporary patch file: %s" % str(remote_patch_file))
        output_command_args = shlex.split(connection_command)
        output_command_args.append("cat > %s" % shlex.quote(remote_patch_file))
        output_command_command = output_command_args.pop(0)
        output_command = plumbum.local[output_command_command][tuple(output_command_args)]
        log.debug("Using remote patch transfer: %s", " ".join(output_command.formulate()))
        patch_size_args = shlex.split(connection_command)
        # "stat --format %s" returns the size of the file in bytes
        patch_size_args.append("stat --format %%s %s" % shlex.quote(remote_patch_file))
        patch_size_command = patch_size_args.pop(0)
        patch_size_func = plumbum.local[patch_size_command][tuple(patch_size_args)]
    else:
        remote_command = "%s --server" % shlex.quote(local_bdsync)
        local_patch_file = tempfile.NamedTemporaryFile(dir=target_patch_dir, delete=False)
        patch_size_func = lambda: os.path.getsize(local_patch_file.name)
        output_command = None
    # run bdsync and handle the resulting states
    create_patch_args = []
    create_patch_args.append(local_bdsync)
    create_patch_args.extend(shlex.split(bdsync_args))
    create_patch_args.append(remote_command)
    create_patch_args.append(source)
    create_patch_args.append(target)
    create_patch_command = create_patch_args.pop(0)
    patch_source = plumbum.local[create_patch_command][tuple(create_patch_args)]
    patch_create_start_time = time.time()
    if connection_command:
        chain = patch_source | output_command
    else:
        chain = patch_source > local_patch_file
    log.debug("Starting local bdsync process: %s", " ".join(chain.formulate()))
    chain()
    patch_create_time = datetime.timedelta(seconds=(time.time() - patch_create_start_time))
    log.debug("bdsync successfully created and transferred a binary patch")
    log.info("Patch Create Time: %s" % patch_create_time)
    log.info("Patch Size: %s" % sizeof_fmt(int(patch_size_func())))
    patch_apply_start_time = time.time()
    # everything went fine - now the patch should be applied
    if connection_command:
        patch_source = None
        # remote command: "bdsync [bdsync_args] --patch < PATCH_FILE"
        remote_command_tokens = []
        remote_command_tokens.append(remote_bdsync)
        remote_command_tokens.extend(shlex.split(bdsync_args))
        remote_command_tokens.append("--patch")
        remote_command_combined = " ".join([shlex.quote(token) for token in remote_command_tokens])
        # the input file is added after an unquoted "<"
        remote_command_combined += " < %s" % shlex.quote(remote_patch_file)
        # local command: "ssh foo@bar 'REMOTE_COMMAND'"
        patch_call_args = shlex.split(connection_command)
        patch_call_args.append(remote_command_combined)
        patch_call_command = patch_call_args.pop(0)
        apply_patch = plumbum.local[patch_call_command][tuple(patch_call_args)]
    else:
        local_patch_file.seek(0)
        patch_call_args = shlex.split(bdsync_args) + ["--patch"]
        apply_patch = (plumbum.local[local_bdsync][tuple(patch_call_args)] < local_patch_file)
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
        remove_command = remove_args.pop(0)
        log.debug("Removing the remote temporary patch file: %s" % str(remove_args))
        plumbum.local[remove_command](remove_args)
    else:
        os.unlink(local_patch_file.name)
