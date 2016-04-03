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

import logging
import os
import shlex

from bdsync_manager import RequirementsError


__logger = None
__log_handler = None


def get_logger():
    global __logger
    global __log_handler
    if __logger is None:
        __logger = logging.getLogger("bdsync-manager")
        __log_handler = logging.StreamHandler()
        __log_handler.setFormatter(logging.Formatter("[bdsync-manager] %(asctime)s - %(message)s"))
        __log_handler.setLevel(logging.DEBUG)
        __logger.addHandler(__log_handler)
    return __logger


def set_log_format(fmt):
    __log_handler.setFormatter(logging.Formatter(fmt))


def get_remote_tempfile(connection_command, target, directory):
    # late import: we want to able to run "verify_requirements" in any case
    import plumbum
    cmd_args = shlex.split(connection_command)
    cmd_args.append("mktemp --tmpdir=%s %s-XXXX.bdsync" % (shlex.quote(directory), shlex.quote(os.path.basename(target))))
    cmd_command = cmd_args.pop(0)
    output = plumbum.local[cmd_command](cmd_args)
    # remove linebreaks from result
    return output.rstrip("\n\r")


def sizeof_fmt(num, suffix='B'):
    # source: http://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def verify_requirements():
    try:
        import plumbum
    except ImportError:
        raise RequirementsError("Failed to import the required python module 'plumbum'")
