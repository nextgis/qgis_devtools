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


import sys
from typing import TYPE_CHECKING, Optional

from osgeo import gdal
from qgis.core import Qgis
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import (
    QT_VERSION_STR,
    QObject,
    QSysInfo,
)
from qgis.utils import iface

from devtools.core import utils
from devtools.core.constants import PACKAGE_NAME
from devtools.core.logging import logger
from devtools.devtools_interface import DevToolsInterface
from devtools.notifier.message_bar_notifier import MessageBarNotifier

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QToolBar

    from devtools.debug.debug_interface import DebugInterface
    from devtools.notifier.notifier_interface import NotifierInterface

assert isinstance(iface, QgisInterface)


class DevToolsPluginStub(DevToolsInterface):
    """Stub implementation of plugin interface used to notify the user when the plugin failed to start."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize the plugin stub."""
        super().__init__(parent)
        metadata_file = self.path / "metadata.txt"

        logger.debug("<b>✓ Plugin stub created</b>")
        logger.debug(f"<b>ⓘ OS:</b> {QSysInfo().prettyProductName()}")
        logger.debug(f"<b>ⓘ Qt version:</b> {QT_VERSION_STR}")
        logger.debug(f"<b>ⓘ QGIS version:</b> {Qgis.version()}")
        logger.debug(f"<b>ⓘ Python version:</b> {sys.version}")
        logger.debug(f"<b>ⓘ GDAL version:</b> {gdal.__version__}")
        logger.debug(f"<b>ⓘ Plugin version:</b> {self.version}")
        logger.debug(
            f"<b>ⓘ Plugin path:</b> {self.path}"
            + (
                f" -> {metadata_file.resolve().parent}"
                if metadata_file.is_symlink()
                else ""
            )
        )
        self.__notifier = None

    @property
    def toolbar(self) -> "QToolBar":
        """Return the plugin toolbar instance.

        :returns: Toolbar instance for the plugin.
        :rtype: QToolBar
        """
        raise NotImplementedError

    @property
    def notifier(self) -> "NotifierInterface":
        """Return the notifier for displaying messages to the user.

        :returns: Notifier interface instance.
        :rtype: NotifierInterface
        """
        assert self.__notifier is not None, "Notifier is not initialized"
        return self.__notifier

    @property
    def debug(self) -> "DebugInterface":
        """Return the debug manager.

        :returns: An instance of DebugInterface.
        :rtype: DebugInterface
        """
        raise NotImplementedError

    def _load(self) -> None:
        """Load the plugin resources and initialize components."""
        self._add_translator(
            self.path / "i18n" / f"{PACKAGE_NAME}_{utils.locale()}.qm",
        )
        self.__notifier = MessageBarNotifier(self)

    def _unload(self) -> None:
        """Unload the plugin resources and clean up components."""
        self.__notifier.deleteLater()
        self.__notifier = None
