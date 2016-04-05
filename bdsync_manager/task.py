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

import bdsync_manager
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
                       self.settings["remote_bdsync_bin"], self.settings["bdsync_args"],
                       self.settings["create_target_if_missing"])
        finally:
            if "lvm" in self.settings:
                lvm_volume.remove_snapshot()


class BDSyncPatch:

    def __init__(self, source, target, local_bdsync, bdsync_args):
        self._source = source
        self._target = target
        self._local_bdsync = local_bdsync
        self._bdsync_args = bdsync_args


    def get_generate_command(self):
        args = []
        args.append(self._local_bdsync)
        args.extend(shlex.split(self._bdsync_args))
        args.append(self._bdsync_server_command)
        args.append(self._source)
        args.append(self._target)
        command = args.pop(0)
        return plumbum.local[command][tuple(args)]


class LocalPatch(BDSyncPatch):

    def __init__(self, source, target, local_bdsync, bdsync_args, target_patch_dir):
        super().__init__(source, target, local_bdsync, bdsync_args)
        self._bdsync_server_command = "%s --server" % shlex.quote(local_bdsync)
        self._patch_file = tempfile.NamedTemporaryFile(dir=target_patch_dir, delete=False)

    def get_transfer_command(self):
        return self.get_generate_command() > self._patch_file

    def get_size(self):
        return os.path.getsize(self._patch_file.name)

    def target_exists(self):
        return os.path.exists(self._target)

    def create_target(self):
        tfile = open(self._target, "w")
        tfile.close()

    def get_apply_command(self):
        self._patch_file.seek(0)
        patch_call_args = shlex.split(self._bdsync_args) + ["--patch"]
        return plumbum.local[self._local_bdsync][tuple(patch_call_args)] < self._patch_file

    def cleanup(self):
        os.unlink(self._patch_file.name)


class RemotePatch(BDSyncPatch):

    def __init__(self, source, target, local_bdsync, bdsync_args, target_patch_dir, connection_command, remote_bdsync):
        super().__init__(source, target, local_bdsync, bdsync_args)
        self._connection_command = connection_command
        self._remote_bdsync = remote_bdsync
        self._bdsync_server_command = "%s %s --server" % (connection_command, shlex.quote(remote_bdsync))
        self._patch_file = bdsync_manager.utils.get_remote_tempfile(connection_command, target, target_patch_dir)
        log.debug("Using remote temporary patch file: %s", self._patch_file)

    def get_transfer_command(self):
        transfer_command_args = shlex.split(self._connection_command)
        transfer_command_args.append("cat > %s" % shlex.quote(self._patch_file))
        transfer_command_command = transfer_command_args.pop(0)
        transfer_command = plumbum.local[transfer_command_command][tuple(transfer_command_args)]
        log.debug("Using remote patch transfer: %s", " ".join(transfer_command.formulate()))
        return self.get_generate_command() | transfer_command

    def get_size(self):
        patch_size_args = shlex.split(self._connection_command)
        # "stat --format %s" returns the size of the file in bytes
        patch_size_args.append("stat --format %%s %s" % shlex.quote(self._patch_file))
        patch_size_command = patch_size_args.pop(0)
        return plumbum.local[patch_size_command](tuple(patch_size_args))

    def target_exists(self):
        cmd_args = shlex.split(self._connection_command)
        cmd_args.append("test -e %s" % shlex.quote(self._target))
        cmd_command = cmd_args.pop(0)
        retcode = plumbum.local[cmd_command][tuple(cmd_args)].run()[0]
        return retcode == 0

    def create_target(self):
        cmd_args = shlex.split(self._connection_command)
        cmd_args.append("touch %s" % shlex.quote(self._target))
        cmd_command = cmd_args.pop(0)
        plumbum.local[cmd_command](tuple(cmd_args))

    def get_apply_command(self):
        # remote command: "bdsync [bdsync_args] --patch < PATCH_FILE"
        remote_command_tokens = []
        remote_command_tokens.append(self._remote_bdsync)
        remote_command_tokens.extend(shlex.split(self._bdsync_args))
        remote_command_tokens.append("--patch")
        remote_command_combined = " ".join([shlex.quote(token) for token in remote_command_tokens])
        # the input file is added after an unquoted "<"
        remote_command_combined += " < %s" % shlex.quote(self._patch_file)
        # local command: "ssh foo@bar 'REMOTE_COMMAND'"
        patch_call_args = shlex.split(self._connection_command)
        patch_call_args.append(remote_command_combined)
        patch_call_command = patch_call_args.pop(0)
        return plumbum.local[patch_call_command][tuple(patch_call_args)]

    def cleanup(self):
        # remove remote patch file
        remove_args = shlex.split(self._connection_command)
        remove_args.append("rm %s" % shlex.quote(self._patch_file))
        remove_command = remove_args.pop(0)
        remove = plumbum.local[remove_command][remove_args]
        log.debug("Removing remote temporary patch file: %s", " ".join(remove.formulate()))
        remove()


def run_bdsync(source, target, target_patch_dir, connection_command, local_bdsync, remote_bdsync, bdsync_args, create_if_missing):
    log.info("Creating binary patch")
    if connection_command:
        patch = RemotePatch(source, target, local_bdsync, bdsync_args, target_patch_dir,
                            connection_command, remote_bdsync)
    else:
        patch = LocalPatch(source, target, local_bdsync, bdsync_args, target_patch_dir)
    # run bdsync and handle the resulting states
    patch_create_start_time = time.time()
    patch_create_command = patch.get_transfer_command()
    log.debug("Starting local bdsync process: %s", " ".join(patch_create_command.formulate()))
    # TODO: replace ".run()" with "& RETCODE" as soon as Debian stretch is released
    retcode = patch_create_command.run(retcode=(0, 6))[0]
    if retcode == 6:
        # a "read" error could indicate a non-existing remote target
        if not patch.target_exists():
            if create_if_missing:
                log.warning("Creating missing target file: %s", target)
                patch.create_target()
                log.info("Trying again to create the patch")
                patch_create_command()
            else:
                raise bdsync_manager.TaskProcessingError("The target does not exist (while 'create_target_if_missing' is disabled)")
    patch_create_time = datetime.timedelta(seconds=(time.time() - patch_create_start_time))
    log.debug("bdsync successfully created and transferred a binary patch")
    log.info("Patch Create Time: %s", patch_create_time)
    log.info("Patch Size: %s", bdsync_manager.utils.sizeof_fmt(int(patch.get_size())))
    patch_apply_start_time = time.time()
    # everything went fine - now the patch should be applied
    apply_patch = patch.get_apply_command()
    log.debug("Applying the patch: %s", " ".join(apply_patch.formulate()))
    apply_patch()
    patch_apply_time = datetime.timedelta(seconds=(time.time() - patch_apply_start_time))
    log.debug("Successfully applied the patch")
    log.info("Patch Apply Time: %s", patch_apply_time)
    patch.cleanup()
