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

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, Union, cast

from console.console import PythonConsole
from qgis.core import QgsApplication, QgsProcessingUtils, QgsSettings
from qgis.PyQt.QtCore import QUrl, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar
from qgis.utils import iface

from devtools.core import utils
from devtools.core.logging import logger
from devtools.debug.adapters.debugpy.debugpy_adapter import DebugpyAdapter
from devtools.debug.debug_interface import DebugInterface
from devtools.debug.debug_settings import DebugSettings
from devtools.debug.enums import DebugState
from devtools.debug.ui.debug_button import DebugButton
from devtools.debug.ui.debug_settings_page import DebugSettingsPageFactory
from devtools.devtools_interface import DevToolsInterface
from devtools.ui.utils import plugin_icon

if TYPE_CHECKING:
    from qgis.gui import QgisInterface

    from devtools.debug.adapters.abstract_debug_adapter import (
        AbstractDebugAdapter,
    )

    assert isinstance(iface, QgisInterface)


class DebugManager(DebugInterface):
    """Debug manager for QGIS DevTools.

    Controls the debug adapter, debug button, and settings integration.
    """

    state_changed = pyqtSignal(DebugState)
    """Signal emitted when the debug state changes."""

    _adapters: List["AbstractDebugAdapter"]
    _current_adapter_index: int

    __debug_current_script_button: Optional[QAction]  # pyright: ignore[reportInvalidTypeForm]
    __python_console: Optional[PythonConsole]

    def __init__(self, parent: DevToolsInterface) -> None:
        """Initialize DebugManager instance.

        :param parent: Plugin interface instance.
        :type parent: DevToolsInterface
        """
        super().__init__(parent)
        self._plugin = parent
        self._debug_control_button = None
        self._adapters = []
        self._current_adapter_index = -1
        self.__debug_current_script_button = None
        self.__python_console = None

    @property
    def adapter(self) -> Optional["AbstractDebugAdapter"]:
        """Get the currently selected debug adapter.

        :returns: Active debug adapter or None if not selected.
        :rtype: Optional[AbstractDebugAdapter]
        """
        return (
            self._adapters[self._current_adapter_index]
            if self._current_adapter_index != -1
            else None
        )

    @pyqtSlot()
    def start(self) -> None:
        """Start the debug session.

        If the debug session is already started, does nothing.
        """
        if self.adapter.state != DebugState.STOPPED:
            logger.info(self.tr("Debug already started"))
            return

        try:
            self.adapter.start()
        except Exception as error:
            logger.exception("Can't start debug")
            DevToolsInterface.instance().notifier.display_exception(error)

    @pyqtSlot()
    def stop(self) -> None:
        """Stop the debug session."""
        self.adapter.stop()

    @pyqtSlot()
    def debug_script(self, script_path: Union[str, Path]) -> None:
        """Debug the script.

        :param script_path: Path to the script to debug.
        """
        self.adapter.debug_script(script_path)

    def breakpoint(self) -> None:
        """Toggle breakpoint at the current line."""
        self.adapter.breakpoint()

    def load(self) -> None:
        """Load and initialize the debug manager and UI."""
        self._adapters = [
            DebugpyAdapter(self),
        ]
        self._current_adapter_index = 0
        self.adapter.state_changed.connect(self.state_changed)
        self.adapter.open_docs.connect(self.__open_docs)

        self.__add_button()
        self.__load_settings_page()

        # self._plugin.settings_changed.connect(self.__reload)

        settings = DebugSettings()
        if settings.auto_start:
            self.start()

    def unload(self) -> None:
        """Unload the debug manager and clean up UI."""
        # self._plugin.settings_changed.disconnect(self.__reload)

        self.__unload_settings_page()
        self.__remove_button()
        self.adapter.stop()
        for adapter in self._adapters:
            adapter.deleteLater()
        self._adapters = []
        self._current_adapter_index = -1

    def integrate_into_python_console(
        self, python_console: "PythonConsole"
    ) -> None:
        """Integrate the debug interface into the Python console.

        :param python_console: The Python console instance to integrate with.
        """
        self.__python_console = python_console

        debug_script_text = self.tr("Debug script")
        self.__debug_current_script_button = QAction()
        self.__debug_current_script_button.setCheckable(False)
        self.__debug_current_script_button.setEnabled(True)
        self.__debug_current_script_button.setIcon(
            plugin_icon("action_debug.svg")
        )
        self.__debug_current_script_button.setMenuRole(
            QAction.MenuRole.PreferencesRole
        )
        self.__debug_current_script_button.setIconVisibleInMenu(True)
        self.__debug_current_script_button.setToolTip(debug_script_text)
        self.__debug_current_script_button.setText(debug_script_text)
        self.__debug_current_script_button.triggered.connect(
            self.__debug_current_script
        )

        toolbar = cast("QToolBar", python_console.console.toolBarEditor)
        toolbar_actions = toolbar.actions()
        index = toolbar_actions.index(
            python_console.console.runScriptEditorButton  # pyright: ignore[reportArgumentType]
        )
        toolbar.insertAction(
            toolbar_actions[index + 1], self.__debug_current_script_button
        )

    def deintegrate_from_python_console(self) -> None:
        """Deintegrate the debug interface from the Python console."""
        if self.__debug_current_script_button is not None:
            self.__debug_current_script_button.deleteLater()
            self.__debug_current_script_button = None

        self.__python_console = None

    def __add_button(self) -> None:
        self._debug_control_button = DebugButton()
        self._debug_control_button.set_adapter_name(self.adapter.name())
        self._debug_control_button.toggle_debug_state.connect(
            self.__toggle_debug_state
        )
        self.state_changed.connect(self.__update_control_button_state)
        self._debug_control_button.open_docs.connect(self.__open_docs)
        self.__update_control_button_state(self.adapter.state)
        iface.statusBarIface().addPermanentWidget(self._debug_control_button)

    def __remove_button(self) -> None:
        self.state_changed.disconnect(self.__update_control_button_state)
        iface.statusBarIface().removeWidget(self._debug_control_button)
        self._debug_control_button.deleteLater()
        self._debug_control_button = None

    def __load_settings_page(self) -> None:
        self.__debug_settings_page_factory = DebugSettingsPageFactory(
            self._adapters
        )
        iface.registerOptionsWidgetFactory(self.__debug_settings_page_factory)

    def __unload_settings_page(self) -> None:
        if self.__debug_settings_page_factory is None:
            return

        iface.unregisterOptionsWidgetFactory(
            self.__debug_settings_page_factory
        )
        self.__debug_settings_page_factory.deleteLater()
        self.__debug_settings_page_factory = None

    @pyqtSlot()
    def __toggle_debug_state(self) -> None:
        if self.adapter.state != DebugState.STOPPED:
            self.stop()
            return

        self.start()

    @pyqtSlot(DebugState)
    def __update_control_button_state(self, state: DebugState) -> None:
        self._debug_control_button.set_state(state)

        if state == DebugState.STOPPED:
            ok, reason = self.adapter.can_start()
            if ok:
                self._debug_control_button.unblock_start()
            else:
                self._debug_control_button.block_start(reason)

    @pyqtSlot()
    def __debug_current_script(self) -> None:
        """Handle the debug script button click."""
        if (
            self.__debug_current_script_button is None
            or self.__python_console is None
        ):
            return

        script_path, is_temporary_file = self.__prepare_script()
        if script_path is None:
            return

        # Run the debug command in the QGIS console's shell
        current_tab = (
            self.__python_console.console.tabEditorWidget.currentWidget()
        )
        script_path_literal = QgsProcessingUtils.stringToPythonLiteral(
            str(script_path)
        )
        shell = (
            current_tab.console_widget
            if hasattr(current_tab, "console_widget")
            else current_tab.pythonconsole
        ).shell

        shell.runCommand(
            f"devtools.debugger.debug_script(Path({script_path_literal}))",
            skipHistory=True,
        )

        if is_temporary_file:
            Path(script_path).unlink()

    def __prepare_script(self) -> Tuple[Optional[str], bool]:
        # Get the current tab from the Python editor
        current_tab = (
            self.__python_console.console.tabEditorWidget.currentWidget()
        )

        # Check if the script is empty
        filename = (
            current_tab.code_editor_widget.filePath()
            if hasattr(current_tab, "code_editor_widget")
            else current_tab.tabwidget.currentWidget().path
        )
        if not filename and not current_tab.isModified():
            empty_editor_message = QgsApplication.translate(
                "PythonConsole", "Hey, type something to run!"
            )
            current_tab.showMessage(empty_editor_message)
            return None, False

        # Perform syntax check
        if not current_tab.syntaxCheck():
            return None, False

        # Save the script if modified and auto-save is enabled
        is_auto_save_enabled = QgsSettings().value(
            "pythonConsole/autoSaveScript", False, type=bool
        )
        if filename and current_tab.isModified() and is_auto_save_enabled:
            current_tab.save(filename)

        # If the script is saved and unmodified, run debug
        if filename and not current_tab.isModified():
            return filename, False

        # Warn the user about unsaved scripts
        warning_title = self.tr("Unsaved script")
        warning_text = self.tr(
            "Breakpoints will not work with unsaved files. "
            "Do you want to continue debugging the unsaved script?"
        )
        buttons = QMessageBox.StandardButtons(
            QMessageBox.StandardButtons()
            | QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )
        default_button = QMessageBox.StandardButton.No

        user_response = QMessageBox.question(
            iface.mainWindow(),
            warning_title,
            warning_text,
            buttons,
            default_button,
        )
        if user_response != QMessageBox.StandardButton.Yes:
            return None, False

        # Create a new temp file if the file isn't already saved.
        filename = current_tab.createTempFile()
        return filename, True

    @pyqtSlot()
    def __open_docs(self) -> None:
        url = DevToolsInterface.instance().metadata.get(
            "general", "user_guide"
        )
        url += f"?{utils.utm_tags('debug')}"
        QDesktopServices.openUrl(QUrl(url))
