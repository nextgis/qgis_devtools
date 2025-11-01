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

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QAbstractButton,
    QDialog,
    QVBoxLayout,
    QWidget,
)

from devtools.core.exceptions import DevToolsUiLoadError


class WaitingDialog(QDialog):
    """Display a modal non-resizable waiting dialog."""

    def __init__(
        self, title: str, text: str, parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the waiting dialog.

        :param title: Window title to display.
        :type title: str
        :param text: Status text to show inside the dialog.
        :type text: str
        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.__load_ui(text)

    def add_button(self, button: QAbstractButton) -> None:
        """Add a custom button to the dialog."""
        self.__widget.custom_buttons_layout.addWidget(button)

    def __load_ui(self, text: str) -> None:
        widget: Optional[QWidget] = None

        try:
            widget = uic.loadUi(
                str(Path(__file__).parent / "waiting_dialog_base.ui")
            )

        except Exception as error:
            raise DevToolsUiLoadError from error

        if widget is None:
            raise DevToolsUiLoadError

        self.__widget = widget
        self.__widget.setParent(self)

        self.__widget.status_label.setText(text)
        self.__widget.button_box.rejected.connect(self.reject)

        # Connect inner dialog signals to outer dialog slots
        self.__widget.accepted.connect(self.accept)
        self.__widget.rejected.connect(self.reject)

        # Place loaded UI into the dialog layout for proper size hint
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__widget)

        # Lock dialog size to prevent resizing
        self.adjustSize()
        self.setFixedSize(self.sizeHint())
