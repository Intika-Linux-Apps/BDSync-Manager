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

import bdsync_manager
from bdsync_manager.utils import log


class Caller:

    def __init__(self, exec_path="/sbin/lvm"):
        self._exec_path = exec_path
        self._check_path()

    def get_volume(self, group, volume):
        return Volume(self, group, volume)

    def __getitem__(self, args):
        """ provide a prepare/call interface similar to plumbum's """
        return plumbum.local[self._exec_path][args]

    def __call__(self, *args):
        return self[tuple(args)]()

    def _check_path(self):
        try:
            self("version")
        except plumbum.CommandNotFound:
            raise bdsync_manager.RequirementsError("Failed to run LVM ({path}): command not found"
                                                   .format(path=self._exec_path))


class Volume:

    def __init__(self, caller, group, volume):
        self._caller = caller
        self._group = group
        self._volume = volume
        self._snapshot_name = None

    def _get_path(self, volume=None):
        if volume is None:
            volume = self._volume
        if os.path.isabs(volume):
            return volume
        else:
            return "/dev/{vg_name}/{volume}".format(vg_name=self._group, volume=self._volume)

    def _create_snapshot(self, snapshot_name, snapshot_size):
        assert self._snapshot_name is None
        log.info("Creating LVM snapshot: %s/%s", self._group, snapshot_name)
        cmd = self._caller["lvcreate", "--snapshot", "--name", snapshot_name,
                           "--size", snapshot_size, self._get_path()]
        log.debug("LVM snapshot create command: %s", " ".join(cmd.formulate()))
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
