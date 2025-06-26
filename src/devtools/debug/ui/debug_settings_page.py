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
from typing import List, Optional

from qgis.gui import (
    QgsOptionsPageWidget,
    QgsOptionsWidgetFactory,
)
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from devtools.core.constants import PACKAGE_NAME
from devtools.core.exceptions import DevToolsUiLoadError
from devtools.core.logging import logger
from devtools.debug.adapters.abstract_debug_adapter import AbstractDebugAdapter
from devtools.debug.debug_settings import DebugSettings
from devtools.devtools_interface import DevToolsInterface
from devtools.ui.utils import material_icon


class DebugSettingsPage(QgsOptionsPageWidget):
    """Widget for managing debug settings in QGIS DevTools.

    Provides UI for configuring general and per-adapter debug settings.
    """

    _adapters: List[AbstractDebugAdapter]
    _adapters_pages: List[QgsOptionsPageWidget]

    def __init__(
        self,
        adapters: List[AbstractDebugAdapter],
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize the debug settings page.

        :param adapters: List of debug adapters.
        :type adapters: List[AbstractDebugAdapter]
        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.setObjectName("DebugSettingsPage")

        self._adapters = adapters
        self._adapters_pages = []

        self.__load_ui()
        self.__load_settings()

    def apply(self) -> None:
        """Apply changes made in the settings page.

        Saves general and adapter-specific settings and emits a signal.
        """
        settings = DebugSettings()
        self.__save_general(settings)

        for adapter_page in self._adapters_pages:
            adapter_page.apply()

        plugin = DevToolsInterface.instance()
        plugin.settings_changed.emit()

    def cancel(self) -> None:
        """Cancel changes made in the settings page.

        Calls cancel on all adapter pages.
        """
        for adapter_page in self._adapters_pages:
            adapter_page.cancel()

    def __load_ui(self) -> None:
        widget: Optional[QWidget] = None
        try:
            widget = uic.loadUi(
                str(Path(__file__).parent / "debug_settings_page_base.ui")
            )
        except Exception as error:
            raise DevToolsUiLoadError from error

        if widget is None:
            raise DevToolsUiLoadError

        self.__widget = widget
        self.__widget.setParent(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.__widget)

        self.start_on_sturtup_checkbox: QCheckBox = (
            self.__widget.start_on_sturtup_checkbox
        )
        self.notification_checkbox: QCheckBox = (
            self.__widget.notification_checkbox
        )
        self.adapter_combobox: QComboBox = self.__widget.adapter_combobox
        self.adapters_settings_widget: QStackedWidget = (
            self.__widget.adapters_settings
        )
        self.adapter_combobox.currentIndexChanged.connect(
            self.adapters_settings_widget.setCurrentIndex
        )

        for adapter in self._adapters:
            self.adapter_combobox.addItem(adapter.name(), adapter.name())

            try:
                widget = adapter.create_settings_widget(self)
            except Exception:
                logger.exception(
                    f"An error occurred while loading {adapter.name()} settings page"
                )
                widget = DebugSettingsErrorPage(self)

            self._adapters_pages.append(widget)
            self.adapters_settings_widget.addWidget(widget)

    def __load_settings(self) -> None:
        settings = DebugSettings()
        adapter_index = self.adapter_combobox.findData(
            settings.current_adapter
        )
        self.adapter_combobox.setCurrentIndex(max(0, adapter_index))
        self.start_on_sturtup_checkbox.setChecked(settings.auto_start)
        self.notification_checkbox.setChecked(settings.show_notification)

    def __save_general(self, settings: DebugSettings) -> None:
        settings.current_adapter = self.adapter_combobox.currentData()
        settings.auto_start = self.start_on_sturtup_checkbox.isChecked()
        settings.show_notification = self.notification_checkbox.isChecked()


class DebugSettingsErrorPage(QgsOptionsPageWidget):
    """Error page shown if the debug settings page fails to load.

    Displays an error message in the options dialog.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the error page widget.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.setObjectName("DebugSettingsPage")

        self.widget = QLabel(
            self.tr("An error occurred while loading settings page"), self
        )
        self.widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.widget)

    def apply(self) -> None:
        """Apply changes (no-op for error page)."""

    def cancel(self) -> None:
        """Cancel changes (no-op for error page)."""


class DebugSettingsPageFactory(QgsOptionsWidgetFactory):
    """Factory for creating the debug settings page in QGIS options.

    Registers the debug settings page in the QGIS options dialog.
    """

    _adapters: List[AbstractDebugAdapter]

    def __init__(self, adapters: List[AbstractDebugAdapter]) -> None:
        """Initialize the settings page factory.

        :param adapters: List of debug adapters.
        :type adapters: List[AbstractDebugAdapter]
        """
        super().__init__()
        self.setTitle(self.tr("Debug"))
        self.setIcon(material_icon("pest_control"))
        self.setKey("debug")

        self._adapters = adapters

    def path(self) -> List[str]:
        """Return the settings page path in the options dialog.

        :returns: List of path elements.
        :rtype: List[str]
        """
        return [PACKAGE_NAME]

    def createWidget(
        self, parent: Optional[QWidget] = None
    ) -> Optional[QgsOptionsPageWidget]:
        """Create and return the debug settings page widget.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        :returns: Settings page widget or error page if loading fails.
        :rtype: Optional[QgsOptionsPageWidget]
        """
        try:
            return DebugSettingsPage(self._adapters, parent)
        except Exception:
            logger.exception("An error occurred while loading settings page")
            return DebugSettingsErrorPage(parent)
