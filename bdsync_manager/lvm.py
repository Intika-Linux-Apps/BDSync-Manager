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

import os

import plumbum

from bdsync_manager import NotFoundError, RequirementsError
from bdsync_manager.utils import log


class Caller:

    def __init__(self, exec_path="/sbin/lvm"):
        self._exec_path = exec_path
        self._check_path()

    def get_volume(self, volume_path):
        return Volume(self, volume_path)

    def __getitem__(self, args):
        """ provide a prepare/call interface similar to plumbum's """
        return plumbum.local[self._exec_path][args]

    def __call__(self, *args):
        return self[tuple(args)]()

    def _check_path(self):
        try:
            self("version")
        except plumbum.CommandNotFound:
            raise RequirementsError("Failed to run LVM ({path}): command not found"
                                    .format(path=self._exec_path))


class Volume:

    def __init__(self, caller, volume_path):
        self._caller = caller
        self._group, self._volume = self._parse_volume_path(volume_path)
        self._snapshot_name = None

    def _parse_volume_path(self, volume_path):
        lvm_info_args = ("lvdisplay", "--columns", "--noheading", "--separator", ":",
                         "-o", "vg_name,lv_name", volume_path)
        cmd = self._caller[lvm_info_args]
        log.debug("Trying to parse LVM volume information: %s", cmd)
        # remove left alignment and the linebreak
        output = cmd().strip()
        if output:
            vg_name, lv_name = output.split(":")
            log.debug("Parsed LVM volume information: %s/%s", vg_name, lv_name)
            return vg_name, lv_name
        else:
            raise NotFoundError("Failed to find find given LVM volume: %s" % volume_path)

    def _get_path(self, volume=None):
        if volume is None:
            volume = self._volume
        assert volume
        return "/dev/{vg_name}/{volume}".format(vg_name=self._group, volume=volume)

    def _create_snapshot(self, snapshot_name, snapshot_size):
        assert self._snapshot_name is None
        log.info("Creating LVM snapshot: %s/%s", self._group, snapshot_name)
        cmd = self._caller["lvcreate", "--snapshot", "--name", snapshot_name,
                           "--size", snapshot_size, self._get_path()]
        log.debug("LVM snapshot create command: %s", cmd)
        cmd()
        self._snapshot_name = snapshot_name

    def get_snapshot(self, snapshot_name, snapshot_size):
        if self._snapshot_name is None:
            self._create_snapshot(snapshot_name, snapshot_size)
        return self._get_path(self._snapshot_name)

    def remove_snapshot(self):
        assert self._snapshot_name is not None
        log.info("Removing LVM snapshot: %s/%s", self._group, self._snapshot_name)
        cmd = self._caller["lvremove", "--force", "%s/%s" % (self._group, self._snapshot_name)]
        log.debug("LVM snapshot remove command: %s", " ".join(cmd.formulate()))
        cmd()
        self._snapshot_name = None
