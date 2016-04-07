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

import logging
import os
import shlex

try:
    import plumbum
except ImportError:
    # ignore errors: we want to able to run "verify_requirements" in any case
    pass

from bdsync_manager import RequirementsError


def __get_logger():
    """ retrieve the configured logger for bdsync-manager """
    try:
        return log
    except NameError:
        new_logger = logging.getLogger("bdsync-manager")
        new_logger.addHandler(logging.StreamHandler())
        set_log_format()
        return new_logger


def set_log_format(fmt=None):
    """ change the logging format (prefix) """
    if fmt is None:
        fmt = "[bdsync-manager] %(asctime)s - %(message)s"
    __get_logger().handlers[-1].setFormatter(logging.Formatter(fmt))


def get_remote_tempfile(connection_command, target, directory):
    """ create a temporary file on a remote host """
    cmd_args = shlex.split(connection_command)
    cmd_args.append("mktemp --tmpdir={0} {1}-XXXX.bdsync"
                    .format(shlex.quote(directory), shlex.quote(os.path.basename(target))))
    cmd_command = cmd_args.pop(0)
    output = plumbum.local[cmd_command](cmd_args)
    # remove linebreaks from result
    return output.rstrip("\n\r")


def sizeof_fmt(num, suffix='B'):
    """ format a size value (bytes) into a human readable value """
    # source: http://stackoverflow.com/a/1094933
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def verify_requirements():
    """ check if all requirements are available
        @raises RequirementsError
    """
    try:
        import plumbum as foo
    except ImportError:
        raise RequirementsError("Failed to import the required python module 'plumbum'")


log = __get_logger()
