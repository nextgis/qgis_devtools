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
from qgis.core import Qgis, QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QT_VERSION_STR, QObject, QSysInfo, QUrl, pyqtSlot
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction, QPushButton, QToolBar
from qgis.utils import iface

from devtools.core import utils
from devtools.core.compat import parse_version
from devtools.core.constants import MENU_NAME, PACKAGE_NAME, PLUGIN_NAME
from devtools.core.logging import logger
from devtools.core.settings import DevToolsSettings
from devtools.debug.debug_manager import DebugManager
from devtools.devtools_interface import DevToolsInterface
from devtools.notifier.message_bar_notifier import MessageBarNotifier
from devtools.ui.about_dialog import AboutDialog
from devtools.ui.devtools_settings_page import DevToolsSettingsPageFactory
from devtools.ui.utils import plugin_icon

if TYPE_CHECKING:
    from devtools.debug.debug_interface import DebugInterface
    from devtools.notifier.notifier_interface import NotifierInterface

assert isinstance(iface, QgisInterface)


class DevToolsPlugin(DevToolsInterface):
    """Main plugin class for QGIS DevTools plugin.

    Implements the core logic, toolbar, notifier, and debug manager.
    """

    __toolbar: Optional[QToolBar]
    __notifier: Optional[MessageBarNotifier]
    __debug_manager: Optional[DebugManager]
    __about_plugin_action: Optional[QAction]  # type: ignore reportInvalidTypeForm
    __about_plugin_help_action: Optional[QAction]  # type: ignore reportInvalidTypeForm
    __devtools_settings_page_factory: Optional[DevToolsSettingsPageFactory]
    __open_settings_action: Optional[QAction]  # type: ignore reportInvalidTypeForm

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize the plugin instance.

        :param parent: Optional parent QObject.
        :type parent: Optional[QObject]
        """
        super().__init__(parent)
        metadata_file = self.path / "metadata.txt"

        logger.debug("<b>✓ Plugin created</b>")
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
        self.__debug_manager = None
        self.__about_plugin_action = None
        self.__about_plugin_help_action = None
        self.__devtools_settings_page_factory = None
        self.__open_settings_action = None

    # @property
    # def toolbar(self) -> QToolBar:
    #     """Return the plugin toolbar instance.

    #     :returns: Toolbar instance for the plugin.
    #     :rtype: QToolBar
    #     """
    #     assert self.__toolbar is not None, "Toolbar is not initialized"
    #     return self.__toolbar

    @property
    def notifier(self) -> "NotifierInterface":
        """Return the notifier for displaying messages to the user.

        :returns: Notifier interface instance.
        :rtype: NotifierInterface
        :raises AssertionError: If notifier is not initialized.
        """
        assert self.__notifier is not None, "Notifier is not initialized"
        return self.__notifier

    @property
    def debug(self) -> "DebugInterface":
        """Return the debug manager.

        :returns: Debug manager instance.
        :rtype: DebugInterface
        :raises AssertionError: If debug manager is not initialized.
        """
        assert self.__debug_manager is not None, (
            "Debug manager is not initialized"
        )
        return self.__debug_manager

    def _load(self) -> None:
        """Load the plugin resources and initialize components."""
        self._add_translator(
            self.path / "i18n" / f"{PACKAGE_NAME}_{utils.locale()}.qm",
        )
        self.__notifier = MessageBarNotifier(self)

        # self.__toolbar = iface.addToolBar("DevTools ToolBar")
        # self.__toolbar.setObjectName("DevToolsToolBar")

        self.__load_settings_page()
        self.__load_debug_manager()
        self.__load_about_dialog_actions()
        self.__add_icons_to_menu()

        self.__check_last_version()

    def _unload(self) -> None:
        """Unload the plugin resources and clean up components."""
        self.__unload_about_dialog_actions()
        self.__unload_debug_manager()
        self.__unload_settings_page()

        # if self.__toolbar is not None:
        #     self.__toolbar.deleteLater()
        #     self.__toolbar = None

        if self.__notifier is not None:
            self.__notifier.deleteLater()
            self.__notifier = None

    def __load_about_dialog_actions(self) -> None:
        self.__about_plugin_action = QAction(
            icon=QgsApplication.getThemeIcon("mActionHelpContents.svg"),  # type: ignore reportArgumentType
            text=self.tr("About plugin…"),
        )
        self.__about_plugin_action.triggered.connect(self.__show_about_dialog)
        iface.addPluginToMenu(MENU_NAME, self.__about_plugin_action)

        self.__about_plugin_help_action = QAction(
            icon=plugin_icon(),  # type: ignore reportArgumentType
            text=PLUGIN_NAME,
        )
        self.__about_plugin_help_action.triggered.connect(
            self.__show_about_dialog
        )

        plugin_help_menu = iface.pluginHelpMenu()
        assert plugin_help_menu is not None
        plugin_help_menu.addAction(self.__about_plugin_help_action)  # type: ignore reportCallIssue

    def __unload_about_dialog_actions(self) -> None:
        if self.__about_plugin_action is not None:
            self.__about_plugin_action.deleteLater()
            self.__about_plugin_action = None
        if self.__about_plugin_help_action is not None:
            self.__about_plugin_help_action.deleteLater()
            self.__about_plugin_help_action = None

    def __add_icons_to_menu(self) -> None:
        for action in iface.pluginMenu().actions():
            if action.text() != MENU_NAME:
                continue
            action.setIcon(plugin_icon())

    def __load_debug_manager(self) -> None:
        self.__debug_manager = DebugManager(self)
        self.__debug_manager.load()

    def __unload_debug_manager(self) -> None:
        if self.__debug_manager is not None:
            self.__debug_manager.unload()
            self.__debug_manager = None

    def __load_settings_page(self) -> None:
        self.__devtools_settings_page_factory = DevToolsSettingsPageFactory()
        iface.registerOptionsWidgetFactory(
            self.__devtools_settings_page_factory
        )

        self.__open_settings_action = QAction(
            icon=QIcon(
                ":images/themes/default/console/iconSettingsConsole.svg"
            ),  # type: ignore reportArgumentType
            text=self.tr("Settings…"),
        )
        self.__open_settings_action.triggered.connect(
            lambda: iface.showOptionsDialog(
                iface.mainWindow(), "DebugSettingsPage"
            )
        )
        iface.addPluginToMenu(MENU_NAME, self.__open_settings_action)

    def __unload_settings_page(self) -> None:
        if self.__devtools_settings_page_factory is not None:
            iface.unregisterOptionsWidgetFactory(
                self.__devtools_settings_page_factory
            )
            self.__devtools_settings_page_factory.deleteLater()
            self.__devtools_settings_page_factory = None

        if self.__open_settings_action is not None:
            iface.removePluginMenu(MENU_NAME, self.__open_settings_action)
            self.__open_settings_action.deleteLater()
            self.__open_settings_action = None

    def __check_last_version(self) -> None:
        """Check if the plugin version has changed and notify the user.

        Show message with buttons for user guide, about dialog, and changelog.
        """
        settings = DevToolsSettings()
        last_version = parse_version(settings.last_run_version)
        current_version = parse_version(self.version)
        if last_version == current_version:
            return

        settings.last_run_version = self.version

        def open_docs() -> None:
            url = self.metadata.get("general", "user_guide")
            url += f"?{utils.utm_tags('start')}"
            QDesktopServices.openUrl(QUrl(url))

        def open_changelog() -> None:
            repository = self.metadata.get("general", "repository")
            url = f"{repository}/releases/tag/v{self.version}"
            QDesktopServices.openUrl(QUrl(url))

        changelog_button = QPushButton(self.tr("Open Changelog"))
        changelog_button.clicked.connect(open_changelog)

        guide_button = QPushButton(self.tr("Open User Guide"))
        guide_button.clicked.connect(open_docs)

        about_button = QPushButton(self.tr("About Plugin…"))
        about_button.clicked.connect(self.__show_about_dialog)

        if last_version == parse_version("0.0.0"):
            message = self.tr("Plugin was successfully installed")
            buttons = [guide_button, about_button]
        else:
            message = self.tr("Plugin was successfully updated")
            buttons = [changelog_button, guide_button, about_button]

        self.notifier.display_message(
            message,
            level=Qgis.MessageLevel.Success,
            widgets=buttons,
        )

    @pyqtSlot()
    def __show_about_dialog(self) -> None:
        """Show the about dialog for the plugin."""
        about_dialog = AboutDialog(PACKAGE_NAME)
        about_dialog.exec()
