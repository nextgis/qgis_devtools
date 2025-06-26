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

from typing import TYPE_CHECKING, List, Optional

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.utils import iface

from devtools.core.logging import logger
from devtools.debug.adapters.debugpy.debugpy_adapter import DebugpyAdapter
from devtools.debug.debug_interface import DebugInterface
from devtools.debug.debug_settings import DebugSettings
from devtools.debug.enums import DebugState
from devtools.debug.ui.debug_button import DebugButton
from devtools.debug.ui.debug_settings_page import DebugSettingsPageFactory
from devtools.devtools_interface import DevToolsInterface

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

    def __init__(self, parent: DevToolsInterface) -> None:
        """Initialize DebugManager instance.

        :param parent: Plugin interface instance.
        :type parent: DevToolsInterface
        """
        super().__init__(parent)
        self._plugin = parent
        self._button = None
        self._adapters = []
        self._current_adapter_index = -1

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

    def load(self) -> None:
        """Load and initialize the debug manager and UI."""
        self._adapters = [
            DebugpyAdapter(self),
        ]
        self._current_adapter_index = 0
        self.adapter.state_changed.connect(self.state_changed)

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

    def __add_button(self) -> None:
        self._button = DebugButton()
        self._button.set_adapter_name(self.adapter.name())
        self._button.toggle_debug_state.connect(self.__toggle_debug_state)
        self.state_changed.connect(self.__update_state)
        self.__update_state(self.adapter.state)
        iface.statusBarIface().addPermanentWidget(self._button)

    def __remove_button(self) -> None:
        self.state_changed.disconnect(self.__update_state)
        iface.statusBarIface().removeWidget(self._button)
        self._button.deleteLater()
        self._button = None

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
    def __update_state(self, state: DebugState) -> None:
        self._button.set_state(state)

        if state == DebugState.STOPPED:
            ok, reason = self.adapter.can_start()
            if ok:
                self._button.unblock_start()
            else:
                self._button.block_start(reason)
