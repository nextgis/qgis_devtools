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
from qgis.core import Qgis, QgsApplication, QgsTaskManager
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QT_VERSION_STR, QObject, QSysInfo, pyqtSlot
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.utils import iface

from devtools.core import utils
from devtools.core.constants import MENU_NAME, PACKAGE_NAME, PLUGIN_NAME
from devtools.core.logging import logger
from devtools.devtools_interface import DevToolsInterface
from devtools.notifier.message_bar_notifier import MessageBarNotifier
from devtools.ui.about_dialog import AboutDialog

if TYPE_CHECKING:
    from devtools.notifier.notifier_interface import NotifierInterface

assert isinstance(iface, QgisInterface)


class DevToolsPlugin(DevToolsInterface):
    """Stub implementation of plugin interface used to notify the user when the plugin failed to start."""

    __toolbar: Optional[QToolBar]
    __notifier: Optional[MessageBarNotifier]
    __about_plugin_action: Optional[QAction]  # type: ignore reportInvalidTypeForm
    __about_plugin_help_action: Optional[QAction]  # type: ignore reportInvalidTypeForm

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
        self.__toolbar = None
        self.__notifier = None

    @property
    def toolbar(self) -> "QToolBar":
        """Return the plugin toolbar instance.

        :returns: Toolbar instance for the plugin.
        :rtype: QToolBar
        """
        assert self.__toolbar is not None, "Toolbar is not initialized"
        return self.__toolbar

    @property
    def notifier(self) -> "NotifierInterface":
        """Return the notifier for displaying messages to the user.

        :returns: Notifier interface instance.
        :rtype: NotifierInterface
        """
        assert self.__notifier is not None, "Notifier is not initialized"
        return self.__notifier

    @property
    def task_manager(self) -> "QgsTaskManager":
        """Return the QgsTaskManager instance for background tasks.

        :returns: Task manager instance.
        :rtype: QgsTaskManager
        """
        return QgsApplication.taskManager()  # type: ignore reportReturnType

    def _load(self) -> None:
        """Load the plugin resources and initialize components."""
        self._add_translator(
            self.path / "i18n" / f"{PACKAGE_NAME}_{utils.locale()}.qm",
        )
        self.__notifier = MessageBarNotifier(self)

        self.__toolbar = iface.addToolBar("DevTools ToolBar")
        self.__toolbar.setObjectName("DevToolsToolBar")

        self.__load_about_dialog_actions()
        self.__add_icons_to_menu()

    def _unload(self) -> None:
        """Unload the plugin resources and clean up components."""
        self.__unload_about_dialog_actions()
        self.__toolbar.deleteLater()
        self.__toolbar = None
        self.__notifier = None

    def __load_about_dialog_actions(self) -> None:
        self.__about_plugin_action = QAction(
            icon=QgsApplication.getThemeIcon("mActionHelpContents.svg"),  # type: ignore reportArgumentType
            text=self.tr("About plugin…"),
        )
        self.__about_plugin_action.triggered.connect(self.__show_about_dialog)
        iface.addPluginToMenu(MENU_NAME, self.__about_plugin_action)

        self.__about_plugin_help_action = QAction(
            icon=self.icon(),  # type: ignore reportArgumentType
            text=PLUGIN_NAME,
        )
        self.__about_plugin_help_action.triggered.connect(
            self.__show_about_dialog
        )

        plugin_help_menu = iface.pluginHelpMenu()
        assert plugin_help_menu is not None
        plugin_help_menu.addAction(self.__about_plugin_help_action)  # type: ignore reportCallIssue

    def __unload_about_dialog_actions(self) -> None:
        self.__about_plugin_action.deleteLater()
        self.__about_plugin_action = None
        self.__about_plugin_help_action.deleteLater()
        self.__about_plugin_help_action = None

    def __add_icons_to_menu(self) -> None:
        for action in iface.pluginMenu().actions():
            if action.text() != MENU_NAME:
                continue
            action.setIcon(self.icon())

    @pyqtSlot()
    def __show_about_dialog(self) -> None:
        about_dialog = AboutDialog(PACKAGE_NAME)
        about_dialog.exec()
