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


import collections
import configparser
import os
import re

import bdsync_manager.lvm
from bdsync_manager import TaskSettingsError
import bdsync_manager.utils


LVM_SIZE_REGEX = re.compile(r"^[0-9]+[bBsSkKmMgGtTpPeE]?$")


class Configuration:

    def __init__(self, filename):
        log = bdsync_manager.utils.get_logger()
        log.debug("Reading config file: %s", filename)
        self.config = configparser.ConfigParser()
        try:
            self.config.read([filename])
        except configparser.Error as error:
            raise TaskSettingsError("Failed to parse configuration ({0}): {1}"
                                    .format(filename, error))
        self._tasks = {key: TaskConfiguration(self.config[key]) for key in self.config.sections()}

    @property
    def tasks(self):
        return dict(self._tasks)


class TaskConfiguration(collections.UserDict):

    def __init__(self, config_section):
        super().__init__()
        self._load(config_section)
        self.validate()

    def _load(self, config):
        # load and validate settings
        try:
            self["local_bdsync_bin"] = config["local_bdsync_bin"]
            self["remote_bdsync_bin"] = config.get("remote_bdsync_bin", None)
            self["bdsync_args"] = config.get("bdsync_args", "")
            self["source_path"] = config["source_path"]
            self["target_path"] = config["target_path"]
            self["disabled"] = config.getboolean("disabled", False)
            self["apply_patch_in_place"] = config.getboolean("apply_patch_in_place", False)
            self["connection_command"] = config.get("connection_command", None)
            self["target_patch_dir"] = config.get("target_patch_dir", None)
            self["create_target_if_missing"] = config.getboolean("create_target_if_missing", False)
            lvm_snapshot_enabled = config.getboolean("lvm_snapshot_enabled", False)
            if lvm_snapshot_enabled:
                self["lvm"] = {
                        "snapshot_size": config["lvm_snapshot_size"],
                        "snapshot_name": config.get("lvm_snapshot_name", "bdsync-snapshot"),
                        "program_path": config.get("lvm_program_path", "/sbin/lvm"),
                }
        except configparser.NoOptionError as exc:
            raise TaskSettingsError("Missing a mandatory task option: %s" % str(exc))
        # expand path names (e.g. user directories, ...)
        path_filter = os.path.expanduser
        for key in ("local_bdsync_bin", "remote_bdsync_bin", "source_path", "target_path", "target_patch_dir"):
            # apply filtering only if value is set / non-empty
            if self[key]:
                self[key] = path_filter(self[key])

    def validate(self):
        if not os.path.isfile(self["local_bdsync_bin"]):
            raise TaskSettingsError("The local 'bdsync' binary was not found ({0})."
                                    .format(self["local_bdsync_bin"]))
        if not os.path.exists(self["source_path"]):
            raise TaskSettingsError("The source device (source_path={0}) does not exist"
                                    .format(self["source_path"]))
        if self["connection_command"] and not self["remote_bdsync_bin"]:
            raise TaskSettingsError("The setting 'remote_bdsync_bin' is required if 'connection_command' is defined.")
        if "lvm" in self:
            if not os.path.exists(self["lvm"]["program_path"]):
                raise TaskSettingsError("Failed to find 'lvm' executable (lvm_program_path='{0}')"
                                        .format(self["lvm"]["program_path"]))
            self["lvm"]["caller"] = bdsync_manager.lvm.Caller(self["lvm"]["program_path"])
            if not LVM_SIZE_REGEX.match(self["lvm"]["snapshot_size"]):
                raise TaskSettingsError("Invalid LVM snapshot size ({0})"
                                        .format(self["lvm"]["snapshot_size"]))
            vg_name = self["lvm"]["caller"]("lvs", "--noheadings", "--options", "vg_name",
                                            self["source_path"]).strip()
            if not vg_name:
                raise TaskSettingsError("Failed to discover the name of the Volume Group of '{0}' via 'lvs'"
                                        .format(self["source_path"]))
            self["lvm"]["vg_name"] = vg_name
        if not self["connection_command"]:
            # local transfer
            if not os.path.exists(os.path.dirname(self["target_path"])):
                raise TaskSettingsError("The directory of the local target (target_path={0}) does not exist"
                                        .format(self["target_path"]))
            if not os.path.isdir(self["target_patch_dir"]):
                raise TaskSettingsError("The patch directory of the local target (target_patch_dir={0}) does not exist"
                                        .format(self["target_patch_dir"]))
