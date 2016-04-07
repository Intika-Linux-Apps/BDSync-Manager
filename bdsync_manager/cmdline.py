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

import argparse
import logging
import re

import bdsync_manager
import bdsync_manager.config
from bdsync_manager.utils import log


EXITCODE_SUCCESS = 0
EXITCODE_MISSING_DEPENDENCY = 1
EXITCODE_CONFIGURATION_ERROR = 2
EXITCODE_TASK_PROCESSING_ERROR = 3
EXITCODE_CANCELLED = 4


def parse_arguments():
    parser = argparse.ArgumentParser(description="Manage one or more bdsync transfers.")
    parser.add_argument("--log-level", dest="log_level", default="warning",
                        choices=("debug", "info", "warning", "error"), help="Output verbosity")
    parser.add_argument("--config", metavar="CONFIG_FILE", dest="config_file",
                        default="/etc/bdsync-manager.conf", type=argparse.FileType('r'),
                        help="Location of the config file")
    parser.add_argument("--task", metavar="TASK_NAME", dest="tasks", action="append")
    args = parser.parse_args()
    log_levels = {"debug": logging.DEBUG,
                  "info": logging.INFO,
                  "warning": logging.WARNING,
                  "error": logging.ERROR}
    log.setLevel(log_levels[args.log_level])
    return args


def _get_safe_string(text):
    return re.sub(r"\W", "_", text)


def main():
    try:
        bdsync_manager.utils.verify_requirements()
    except bdsync_manager.RequirementsError as error:
        log.error(str(error))
        return EXITCODE_MISSING_DEPENDENCY
    log.debug("Parsing arguments")
    args = parse_arguments()
    try:
        settings = bdsync_manager.config.Configuration(args.config_file.name)
    except bdsync_manager.TaskSettingsError as error:
        log.error(error)
        return EXITCODE_CONFIGURATION_ERROR
    if args.tasks:
        tasks = []
        for task in args.tasks:
            if task in settings.tasks:
                tasks.append(task)
            else:
                log.warning("Skipping unknown task: %s", _get_safe_string(task))
    else:
        tasks = settings.tasks.keys()
    if not tasks:
        log.warning("There is nothing to be done (no tasks found in config file).")
    processing_error = False
    # late import: avoid import problems before dependency checks (see above)
    from bdsync_manager.task import Task
    for task_name in tasks:
        task = Task(settings.tasks[task_name])
        bdsync_manager.utils.set_log_format("[Task {0}] %(levelname)s: %(message)s"
                                            .format(task_name))
        try:
            task.run()
        except bdsync_manager.TaskProcessingError as error:
            log.error(str(error))
            processing_error = True
    if processing_error:
        return EXITCODE_TASK_PROCESSING_ERROR
    else:
        return EXITCODE_SUCCESS


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        log.info("Cancelled task")
        exit(EXITCODE_CANCELLED)
