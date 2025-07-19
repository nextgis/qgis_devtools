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


from qgis.core import QgsSettings

from devtools.core.constants import PLUGIN_SETTINGS_GROUP


class DevToolsSettings:
    """DevToolsSettings manages persistent plugin settings."""

    KEY_LAST_RUN_VERSION = f"{PLUGIN_SETTINGS_GROUP}/other/lastRunVersion"
    KEY_DID_LAST_LAUNCH_FAIL = (
        f"{PLUGIN_SETTINGS_GROUP}/other/didLastLaunchFail"
    )
    KEY_IS_DEBUG_LOGS_ENABLED = (
        f"{PLUGIN_SETTINGS_GROUP}/other/debugLogsEnabled"
    )

    __settings: QgsSettings

    def __init__(self) -> None:
        """Initialize the settings manager."""
        self.__settings = QgsSettings()

    @property
    def last_run_version(self) -> str:
        """Get the last run plugin version.

        :return: Version string in the format "major.minor.patch".
        :rtype: str
        """
        return self.__settings.value(
            self.KEY_LAST_RUN_VERSION,
            defaultValue="0.0.0",
            type=str,
        )

    @last_run_version.setter
    def last_run_version(self, version: str) -> None:
        self.__settings.setValue(self.KEY_LAST_RUN_VERSION, version)

    @property
    def did_last_launch_fail(self) -> bool:
        """Checks whether the last plugin launch failed.

        :return: True if the last launch failed, False otherwise.
        :rtype: bool
        """
        return self.__settings.value(
            self.KEY_DID_LAST_LAUNCH_FAIL,
            defaultValue=False,
            type=bool,
        )

    @did_last_launch_fail.setter
    def did_last_launch_fail(self, value: bool) -> None:
        self.__settings.setValue(self.KEY_DID_LAST_LAUNCH_FAIL, value)

    @property
    def is_debug_logs_enabled(self) -> bool:
        """Check if debug logs are enabled.

        :return: True if debug logs are enabled, False otherwise.
        :rtype: bool
        """
        return self.__settings.value(
            self.KEY_IS_DEBUG_LOGS_ENABLED,
            defaultValue=False,
            type=bool,
        )

    @is_debug_logs_enabled.setter
    def is_debug_logs_enabled(self, value: bool) -> None:
        self.__settings.setValue(self.KEY_IS_DEBUG_LOGS_ENABLED, value)
