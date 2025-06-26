# QGIS DevTools Plugin
# Copyright (C) 2025  NextGIS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or any
# later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.


from typing import Optional

from qgis.core import QgsSettings

from devtools.debug.debug_settings import DebugSettings


class DebugpySettings(DebugSettings):
    """debugpy adapter settings.

    This class provides access to persistent settings for the debugpy
    adapter using QGIS settings storage.

    """

    DEBUGPY_GROUP = f"{DebugSettings.DEBUG_GROUP}/adapters/debugpy"
    KEY_HOSTNAME = f"{DEBUGPY_GROUP}/hostname"
    KEY_PORT_FROM = f"{DEBUGPY_GROUP}/portFrom"
    KEY_PORT_TO = f"{DEBUGPY_GROUP}/portTo"
    KEY_AUTO_SELECT_PORT = f"{DEBUGPY_GROUP}/autoSelectPort"

    def __init__(self) -> None:
        """Initialize DebugpySettings instance."""
        self._settings = QgsSettings()

    @property
    def hostname(self) -> Optional[str]:
        """Get the hostname for debugpy adapter.

        :returns: Hostname string or None if not set.
        :rtype: Optional[str]
        """
        value = self._settings.value(self.KEY_HOSTNAME, type=str)
        return value if value else None

    @hostname.setter
    def hostname(self, value: Optional[str]) -> None:
        """Set the hostname for debugpy adapter.

        :param value: Hostname string or None.
        :type value: Optional[str]
        """
        if value is None:
            self._settings.remove(self.KEY_HOSTNAME)
            return
        self._settings.setValue(self.KEY_HOSTNAME, value)

    @property
    def port_from(self) -> int:
        """Get the starting port for debugpy adapter.

        :returns: Starting port number or None if not set.
        :rtype: Optional[int]
        """
        return self._settings.value(
            self.KEY_PORT_FROM, defaultValue=5678, type=int
        )

    @port_from.setter
    def port_from(self, value: Optional[int]) -> None:
        """Set the starting port for debugpy adapter.

        :param value: Port number or None.
        :type value: Optional[int]
        """
        if value is None:
            self._settings.remove(self.KEY_PORT_FROM)
            return
        self._settings.setValue(self.KEY_PORT_FROM, value)

    @property
    def port_to(self) -> int:
        """Get the ending port for debugpy adapter.

        :returns: Ending port number or None if not set.
        :rtype: Optional[int]
        """
        return self._settings.value(
            self.KEY_PORT_TO, defaultValue=5678, type=int
        )

    @port_to.setter
    def port_to(self, value: Optional[int]) -> None:
        """Set the ending port for debugpy adapter.

        :param value: Port number or None.
        :type value: Optional[int]
        """
        if value is None:
            self._settings.remove(self.KEY_PORT_TO)
            return
        self._settings.setValue(self.KEY_PORT_TO, value)

    @property
    def auto_select_port(self) -> bool:
        """Get the auto select port setting.

        :returns: True if auto select port is enabled, False otherwise.
        :rtype: bool
        """
        return self._settings.value(
            self.KEY_AUTO_SELECT_PORT, defaultValue=False, type=bool
        )

    @auto_select_port.setter
    def auto_select_port(self, value: bool) -> None:
        """Set the auto select port setting.

        :param value: True to enable auto select port, False to disable.
        :type value: bool
        """
        self._settings.setValue(self.KEY_AUTO_SELECT_PORT, value)
