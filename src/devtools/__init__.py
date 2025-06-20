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


from typing import TYPE_CHECKING

from qgis.core import QgsRuntimeProfiler

from devtools.core.exceptions import DevToolsReloadAfterUpdateWarning
from devtools.core.settings import DevToolsSettings
from devtools.devtools_interface import DevToolsInterface

if TYPE_CHECKING:
    from qgis.gui import QgisInterface


def classFactory(_iface: "QgisInterface") -> DevToolsInterface:
    """Create and return an instance of the DevTools plugin.

    :param _iface: QGIS interface instance passed by QGIS at plugin load.
    :type _iface: QgisInterface
    :returns: An instance of DevToolsInterface (plugin or stub).
    :rtype: DevToolsInterface
    """
    settings = DevToolsSettings()

    try:
        with QgsRuntimeProfiler.profile("Import plugin"):  # type: ignore PylancereportAttributeAccessIssue
            from devtools.devtools_plugin import DevToolsPlugin

        plugin = DevToolsPlugin()

        settings.did_last_launch_fail = False

    except Exception as error:
        import copy

        from qgis.PyQt.QtCore import QTimer

        from devtools.devtools_plugin_stub import DevToolsPluginStub

        error_copy = copy.deepcopy(error)
        exception = error_copy

        if not settings.did_last_launch_fail:
            # Sometimes after an update that changes the plugin structure,
            # the plugin may fail to load. Restarting QGIS helps.
            exception = DevToolsReloadAfterUpdateWarning()
            exception.__cause__ = error_copy

        settings.did_last_launch_fail = True

        plugin = DevToolsPluginStub()

        def display_exception() -> None:
            plugin.notifier.display_exception(exception)

        QTimer.singleShot(0, display_exception)

    return plugin
