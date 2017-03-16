"""
    bdsync-manager: maintain synchronization tasks for remotely or locally
    synchronized blockdevices via bdsync

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
import shlex
import time

from plumbum import ProcessExecutionError

from bdsync_manager import TaskProcessingError, NotFoundError
from bdsync_manager.utils import get_command_from_tokens, get_tempfile, sizeof_fmt, log


class Task:

    def __init__(self, config_dict):
        self.settings = dict(config_dict)

    def run(self):
        if self.settings["disabled"]:
            log.info("Skipping disabled task")
            return
        if "lvm" in self.settings:
            lvm_volume = self.settings["lvm"]["caller"].get_volume(self.settings["source_path"])
            real_source = lvm_volume.get_snapshot(self.settings["lvm"]["snapshot_name"],
                                                  self.settings["lvm"]["snapshot_size"])
        else:
            real_source = self.settings["source_path"]
        try:
            bdsync_run(real_source, self.settings["target_path"],
                       self.settings["connection_command"], self.settings["local_bdsync_bin"],
                       self.settings["remote_bdsync_bin"], self.settings["bdsync_args"],
                       self.settings["target_patch_dir"], self.settings["create_target_if_missing"],
                       self.settings["apply_patch_in_place"])
        except ProcessExecutionError as exc:
            raise TaskProcessingError("Failed to run command: {0}".format(exc))
        finally:
            if "lvm" in self.settings:
                lvm_volume.remove_snapshot()


class SyncSource:

    def __init__(self, source_filename, bdsync_bin, bdsync_args):
        self.filename = source_filename
        self._bdsync_bin = bdsync_bin
        self._bdsync_arg_tokens = shlex.split(bdsync_args)

    def get_generate_patch_command(self, sync_target):
        bdsync_server_cmd = sync_target.get_bdsync_command("--server")
        # TODO: fix the command -> string conversion is not
        cmd_args = [self._bdsync_bin] + self._bdsync_arg_tokens + \
                   [str(bdsync_server_cmd), self.filename, sync_target.filename]
        return get_command_from_tokens(cmd_args)


class SyncTarget:

    def __init__(self, target_filename, bdsync_bin, bdsync_args, connection_command=None):
        self.filename = target_filename
        self._bdsync_bin = bdsync_bin
        self._bdsync_arg_tokens = shlex.split(bdsync_args)
        self._connection_tokens = shlex.split(connection_command or "")

    def get_bdsync_command(self, arg):
        cmd_args = self._connection_tokens + [self._bdsync_bin] + self._bdsync_arg_tokens + [arg]
        return get_command_from_tokens(cmd_args)

    def exists(self):
        cmd_args = self._connection_tokens + ["[", "-e", self.filename, "]"]
        cmd = get_command_from_tokens(cmd_args)
        log.debug("Testing if target exists: %s", cmd)
        retcode = cmd.run(retcode=(0, 1))[0]
        log.debug("Target %s", "exists" if (retcode == 0) else "does not exist")
        return retcode == 0

    def create_empty(self):
        cmd_args = self._connection_tokens + ["touch", self.filename]
        cmd = get_command_from_tokens(cmd_args)
        log.debug("Creating target: %s", cmd)
        cmd()

    def get_apply_patch_command(self, patch=None):
        # by default: read from stdin
        patch_command = get_command_from_tokens([self._bdsync_bin] + self._bdsync_arg_tokens +
                                                ["--patch"])
        if patch is not None:
            patch_command = patch_command < patch.filename
        if self._connection_tokens:
            remote_cmd_args = self._connection_tokens + [patch_command]
            return get_command_from_tokens(remote_cmd_args)
        else:
            return patch_command


class SyncPatch:

    def __init__(self, target_patch_dir, connection_command=None):
        self._connection_tokens = shlex.split(connection_command or "")
        self.filename = get_tempfile(target_patch_dir, self._connection_tokens)
        log.debug("Using temporary patch file: %s", self.filename)

    def get_store_command(self):
        if self._connection_tokens:
            remote_cmd_string = "cat > {0}".format(shlex.quote(self.filename))
            store_cmd_args = self._connection_tokens + [remote_cmd_string]
            store_cmd = get_command_from_tokens(store_cmd_args)
        else:
            store_cmd_args = ["cat"]
            store_cmd = get_command_from_tokens(store_cmd_args) > self.filename
        log.debug("Storing patch file: %s", store_cmd)
        return store_cmd

    def get_size(self):
        # "stat --format %s" returns the size of the file in bytes
        cmd_args = self._connection_tokens + ["stat", "--format", "%s", self.filename]
        cmd = get_command_from_tokens(cmd_args)
        log.debug("Retrieving the size of the patch: %s", cmd)
        return int(cmd())

    def cleanup(self):
        # remove patch file
        cmd_args = self._connection_tokens + ["rm", self.filename]
        cmd = get_command_from_tokens(cmd_args)
        log.debug("Removing temporary patch file: %s", cmd)
        cmd()


def bdsync_run(source_filename, target_filename, connection_command, local_bdsync,
               remote_bdsync, bdsync_args, target_patch_dir, create_if_missing, apply_in_place):
    """ Run bdsync in one or two phases. With one phase changes are applied in-place.
        With two phases there are separate stages of patch generation / transfer followed
        by the application of the patch.
    """
    source = SyncSource(source_filename, local_bdsync, bdsync_args)
    target = SyncTarget(target_filename,
                        remote_bdsync if connection_command else local_bdsync,
                        bdsync_args, connection_command)
    # preparations
    if not target.exists():
        if create_if_missing:
            log.warning("Creating missing target file: %s", target.filename)
            target.create_empty()
        else:
            raise NotFoundError("The target does not exist (while 'create_target_if_missing' "
                                "is disabled)")
    generate_patch_cmd = source.get_generate_patch_command(target)
    if apply_in_place:
        start_time = time.time()
        operation = generate_patch_cmd | target.get_apply_patch_command()
        log.debug("Applying changes in-place: %s", operation)
        operation()
        change_apply_time = datetime.timedelta(seconds=(time.time() - start_time))
        log.info("Change Apply Time: %s", change_apply_time)
    else:
        patch = SyncPatch(target_patch_dir, connection_command)
        # generate and store the patch
        start_time = time.time()
        generate_patch_command = generate_patch_cmd | patch.get_store_command()
        log.debug("Generating Patch: %s", generate_patch_command)
        generate_patch_command()
        patch_generate_time = datetime.timedelta(seconds=(time.time() - start_time))
        log.info("Patch Generate Time: %s", patch_generate_time)
        log.info("Patch Size: %s", sizeof_fmt(patch.get_size()))
        # apply the new patch
        start_time = time.time()
        apply_patch_command = target.get_apply_patch_command(patch)
        apply_patch_command()
        patch_apply_time = datetime.timedelta(seconds=(time.time() - start_time))
        log.info("Patch Apply Time: %s", patch_apply_time)
        patch.cleanup()
