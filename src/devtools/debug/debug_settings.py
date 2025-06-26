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

from devtools.core.constants import PLUGIN_SETTINGS_GROUP


class DebugSettings:
    """Manage persistent debug settings for the QGIS DevTools plugin.

    This class provides accessors and mutators for debugger-related
    settings stored in QGIS settings.
    """

    DEBUG_GROUP = f"{PLUGIN_SETTINGS_GROUP}/debug"
    KEY_AUTO_START = f"{DEBUG_GROUP}/autoStart"
    KEY_SHOW_NOTIFICATION = f"{DEBUG_GROUP}/showNotification"
    KEY_ADAPTER = f"{DEBUG_GROUP}/adapter"

    def __init__(self) -> None:
        """Initialize DebugSettings instance."""
        self._settings = QgsSettings()

    @property
    def auto_start(self) -> bool:
        """Get the auto start debugger setting.

        :returns: True if debugger should start automatically, False otherwise.
        :rtype: bool
        """
        return self._settings.value(
            self.KEY_AUTO_START, defaultValue=False, type=bool
        )

    @auto_start.setter
    def auto_start(self, value: bool) -> None:
        """Set the auto start debugger setting.

        :param value: True to enable auto start, False to disable.
        :type value: bool
        """
        self._settings.setValue(self.KEY_AUTO_START, value)

    @property
    def show_notification(self) -> bool:
        """Get the show notification on debugger start setting.

        :returns: True if notification should be shown, False otherwise.
        :rtype: bool
        """
        return self._settings.value(
            self.KEY_SHOW_NOTIFICATION, defaultValue=True, type=bool
        )

    @show_notification.setter
    def show_notification(self, value: bool) -> None:
        """Set the show notification on debugger start setting.

        :param value: True to show notification, False to disable.
        :type value: bool
        """
        self._settings.setValue(self.KEY_SHOW_NOTIFICATION, value)

    @property
    def current_adapter(self) -> Optional[str]:
        """Get the current debugger adapter setting.

        :returns: Adapter string if set, otherwise None.
        :rtype: Optional[str]
        """
        return self._settings.value(
            self.KEY_ADAPTER, defaultValue=None, type=str
        )

    @current_adapter.setter
    def current_adapter(self, value: Optional[str]) -> None:
        """Set the current debugger adapter setting.

        :param value: Adapter string or None to unset.
        :type value: Optional[str]
        """
        if value is None:
            self._settings.remove(self.KEY_ADAPTER)
            return
        self._settings.setValue(self.KEY_ADAPTER, value)
