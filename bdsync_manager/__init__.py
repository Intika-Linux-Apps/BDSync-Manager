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


VERSION = "0.2"


class BDSyncManagerError(Exception): pass
class TaskProcessingError(BDSyncManagerError): pass
class TaskSettingsError(BDSyncManagerError): pass
class RequirementsError(BDSyncManagerError): pass
