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
from typing import Optional

from qgis.gui import QgsOptionsPageWidget
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from devtools.core.exceptions import DevToolsUiLoadError
from devtools.debug.adapters.debugpy.debugpy_settings import DebugpySettings


class DebugpySettingsPage(QgsOptionsPageWidget):
    """Widget for configuring debugpy adapter settings.

    Provides UI for editing debugpy adapter settings and synchronizing
    them with persistent QGIS settings storage.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize DebugpySettingsPage.

        :param parent: Parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.__load_ui()
        self.__load_settings()

    def apply(self) -> None:
        """Save current UI values to persistent settings."""
        settings = DebugpySettings()
        settings.hostname = self.hostname_lineedit.text() or None
        settings.port_from = self.from_spinbox.value()
        settings.port_to = self.to_spinbox.value()
        settings.auto_select_port = self.auto_select_checkbox.isChecked()

    def cancel(self) -> None:
        """Restore UI values from persistent settings."""
        self.__load_settings()

    def __load_settings(self) -> None:
        """Load settings from persistent storage and update UI."""
        settings = DebugpySettings()
        hostname = settings.hostname
        self.hostname_lineedit.setText(hostname if hostname else "")
        self.from_spinbox.setValue(settings.port_from)
        self.to_spinbox.setValue(settings.port_to)
        self.auto_select_checkbox.setChecked(settings.auto_select_port)

    def __load_ui(self) -> None:
        """Load UI from .ui file and initialize widgets."""
        widget: Optional[QWidget] = None
        try:
            widget = uic.loadUi(
                str(Path(__file__).parent / "debugpy_settings_page_base.ui")
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

        self.hostname_lineedit: QLineEdit = self.__widget.hostname_lineedit
        self.hostname_lineedit.setPlaceholderText("127.0.0.1")

        self.auto_select_checkbox: QCheckBox = (
            self.__widget.auto_select_checkbox
        )
        self.from_spinbox: QSpinBox = self.__widget.from_spinbox
        self.to_spinbox: QSpinBox = self.__widget.to_spinbox
        self.dash_label: QLabel = self.__widget.dash_label

        self.from_spinbox.setMinimum(1024)
        self.from_spinbox.setMaximum(65535)
        self.to_spinbox.setMinimum(1024)
        self.to_spinbox.setMaximum(65535)

        self.from_spinbox.valueChanged.connect(self.__on_from_spinbox_changed)
        self.to_spinbox.valueChanged.connect(self.__on_to_spinbox_changed)
        self.auto_select_checkbox.toggled.connect(
            self.__on_auto_select_checkbox_toggled
        )

    @pyqtSlot(int)
    def __on_from_spinbox_changed(self, value: int) -> None:
        """Update to_spinbox minimum when from_spinbox changes.

        :param value: New value of from_spinbox
        :type value: int
        """
        self.to_spinbox.setMinimum(value)
        if self.to_spinbox.value() < value:
            self.to_spinbox.setValue(value)

    @pyqtSlot(int)
    def __on_to_spinbox_changed(self, value: int) -> None:
        """Update from_spinbox maximum when to_spinbox changes.

        :param value: New value of to_spinbox
        :type value: int
        """
        self.from_spinbox.setMaximum(value)
        if self.from_spinbox.value() > value:
            self.from_spinbox.setValue(value)

    @pyqtSlot(bool)
    def __on_auto_select_checkbox_toggled(self, checked: bool) -> None:  # noqa: FBT001
        """Enable or disable spinboxes based on auto_select_checkbox state.

        :param checked: Checkbox state
        :type checked: bool
        """
        self.from_spinbox.setEnabled(not checked)
        self.to_spinbox.setEnabled(not checked)
        self.dash_label.setEnabled(not checked)
