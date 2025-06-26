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
    QLabel,
    QVBoxLayout,
    QWidget,
)

from devtools.core.constants import PACKAGE_NAME, PLUGIN_NAME
from devtools.core.exceptions import DevToolsUiLoadError
from devtools.core.logging import logger, update_logging_level
from devtools.core.settings import DevToolsSettings
from devtools.devtools_interface import DevToolsInterface
from devtools.ui.utils import plugin_icon


class DevToolsSettingsPage(QgsOptionsPageWidget):
    """Settings page for QGIS DevTools plugin.

    Provides UI and logic for managing plugin settings in QGIS options dialog.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the settings page widget.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.__load_ui()
        self.__load_settings()

    def apply(self) -> None:
        """Apply changes made in the settings page.

        Saves settings and emits settings_changed signal.
        """
        settings = DevToolsSettings()
        self.__save_other(settings)

        plugin = DevToolsInterface.instance()
        plugin.settings_changed.emit()

    def cancel(self) -> None:
        """Cancel changes made in the settings page."""

    def __load_ui(self) -> None:
        widget: Optional[QWidget] = None
        try:
            widget = uic.loadUi(
                str(Path(__file__).parent / "devtools_settings_page_base.ui")
            )
        except Exception as error:
            raise DevToolsUiLoadError from error

        if widget is None:
            raise DevToolsUiLoadError

        self.__widget = widget
        self.__widget.setParent(self)

        self.debug_logs_checkbox: QCheckBox = self.__widget.debug_logs_checkbox

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.__widget)

    def __load_settings(self) -> None:
        settings = DevToolsSettings()
        self.debug_logs_checkbox.setChecked(settings.is_debug_logs_enabled)

    def __save_other(self, settings: DevToolsSettings) -> None:
        old_debug_enabled = settings.is_debug_logs_enabled
        new_debug_enabled = self.debug_logs_checkbox.isChecked()
        settings.is_debug_logs_enabled = new_debug_enabled
        if old_debug_enabled != new_debug_enabled:
            debug_state = "enabled" if new_debug_enabled else "disabled"
            update_logging_level()
            logger.warning(f"Debug messages were {debug_state}")


class DevToolsSettingsErrorPage(QgsOptionsPageWidget):
    """Error page shown if settings page fails to load.

    Displays an error message in the options dialog.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the error page widget.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
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


class DevToolsSettingsPageFactory(QgsOptionsWidgetFactory):
    """Factory for creating the QGIS DevTools settings page.

    Registers the settings page in the QGIS options dialog.
    """

    def __init__(self) -> None:
        """Initialize the settings page factory."""
        super().__init__()
        self.setTitle(PLUGIN_NAME)
        self.setIcon(plugin_icon())
        self.setKey(PACKAGE_NAME)

    def path(self) -> List[str]:
        """Return the settings page path in the options dialog.

        :returns: List of path elements.
        :rtype: List[str]
        """
        return []

    def createWidget(
        self, parent: Optional[QWidget] = None
    ) -> Optional[QgsOptionsPageWidget]:
        """Create and return the settings page widget.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        :returns: Settings page widget or error page if loading fails.
        :rtype: Optional[QgsOptionsPageWidget]
        """
        try:
            return DevToolsSettingsPage(parent)
        except Exception:
            logger.exception("An error occurred while loading settings page")
            return DevToolsSettingsErrorPage(parent)
