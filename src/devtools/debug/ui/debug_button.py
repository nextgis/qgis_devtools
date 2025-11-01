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
from typing import TYPE_CHECKING, Optional

from qgis.core import QgsApplication
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QLabel,
    QMenu,
    QPushButton,
    QToolButton,
    QWidget,
    QWidgetAction,
)
from qgis.utils import iface

from devtools.debug.enums import DebugState
from devtools.ui.utils import draw_icon, material_icon

if TYPE_CHECKING:
    from qgis.gui import QgisInterface

    assert isinstance(iface, QgisInterface)


class DebugButton(QToolButton):
    """Debug button with state-dependent icon and tooltip.

    This widget provides a button for controlling and displaying the state
    of the debugger in the QGIS DevTools plugin.
    """

    toggle_debug_state = pyqtSignal()
    """Signal emitted to toggle the debug state."""

    open_docs = pyqtSignal()
    """Signal emitted to open the documentation."""

    STOPPED_COLOR = ""  # Current theme text color
    STARTED_COLOR = "#e2d047"
    CONNECTED_COLOR = "#88b15f"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize DebugButton widget.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.__load_ui()

    @pyqtSlot(DebugState)
    def set_state(self, state: DebugState = DebugState.STOPPED) -> None:
        """Set the current debug state and update the button UI.

        :param state: Debug state to set.
        :type state: DebugState
        :raises NotImplementedError: If state is unknown.
        """
        status_label_text = self.tr("<b>Status:</b> ")

        start_stop_button: QPushButton = self.__status_widget.start_stop_button

        if state == DebugState.STOPPED:
            self.setIcon(
                material_icon("pest_control", color=self.STOPPED_COLOR)
            )
            self.setToolTip("Debugging is stopped")
            status_label_text += self.tr("stopped")
            start_stop_button.setText(self.tr("Start"))

        elif state == DebugState.RUNNING:
            self.setIcon(
                material_icon("pest_control", color=self.STARTED_COLOR)
            )
            self.setToolTip("Client is not connected to debugger")
            status_label_text += self.tr("running")
            start_stop_button.setText(self.tr("Stop"))

        elif state == DebugState.RUNNING_AND_USER_CONNECTED:
            self.setIcon(
                material_icon("pest_control", color=self.CONNECTED_COLOR)
            )
            self.setToolTip("Client is connected to debugger")
            status_label_text += self.tr("client connected")
            start_stop_button.setText(self.tr("Stop"))

        else:
            raise NotImplementedError

        status_label: QLabel = self.__status_widget.status_label
        status_label.setText(status_label_text)

    def set_adapter_name(self, adapter_name: str) -> None:
        """Set the name of the current debug adapter in the UI.

        :param adapter_name: Name of the adapter.
        :type adapter_name: str
        """
        self.__status_widget.adapter_label.setText(
            self.tr("<b>Adapter:</b> ") + adapter_name
        )

    def block_start(self, reason: Optional[str] = None) -> None:
        """Block the start button and show a warning.

        :param reason: Reason for blocking, shown as tooltip.
        :type reason: Optional[str]
        """
        self.__status_widget.start_stop_button.setEnabled(False)
        self.__status_widget.warning_label.setToolTip(
            reason if reason else self.tr("Unable to start debugging")
        )
        self.__status_widget.warning_label.show()

    def unblock_start(self) -> None:
        """Unblock the start button and hide the warning."""
        self.__status_widget.start_stop_button.setEnabled(True)
        self.__status_widget.warning_label.hide()

    def __load_ui(self) -> None:
        self.setCheckable(True)

        self.__status_widget = uic.loadUi(
            str(Path(__file__).parent / "status_widget_base.ui")
        )
        self.__status_widget.start_stop_button.clicked.connect(
            self.toggle_debug_state
        )

        # Help button
        self.__status_widget.help_button.setIcon(material_icon("help"))
        self.__status_widget.help_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.__status_widget.help_button.clicked.connect(self.open_docs)

        # Settings button
        self.__status_widget.settings_button.setIcon(
            QIcon(":images/themes/default/console/iconSettingsConsole.svg")
        )
        self.__status_widget.settings_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.__status_widget.settings_button.clicked.connect(
            lambda: iface.showOptionsDialog(
                iface.mainWindow(), "DebugSettingsPage"
            )
        )
        draw_icon(
            self.__status_widget.warning_label,
            QgsApplication.getThemeIcon("mIconWarning.svg"),
        )
        self.__status_widget.warning_label.hide()

        menu = QMenu(self)
        action = QWidgetAction(menu)
        action.setDefaultWidget(self.__status_widget)
        menu.addAction(action)

        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setMenu(menu)

        # Hide arrow
        self.setStyleSheet("QToolButton::menu-indicator { image: none; }")

        self.set_state()
