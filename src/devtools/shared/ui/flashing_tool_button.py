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


from typing import Optional

from qgis.PyQt.QtCore import Qt, QTimer, pyqtSlot
from qgis.PyQt.QtWidgets import QToolButton, QWidget


class FlashingToolButton(QToolButton):
    """QToolButton subclass that flashes its text for one second on click.

    :param text: Initial button text
    :type text: str
    :param flash_text: Flashing button text
    :type flash_text: str
    :param parent: Parent widget
    :type parent: QWidget, optional
    """

    def __init__(
        self, text: str, flash_text: str, parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the FlashingToolButton.

        :param text: Initial button text
        :type text: str
        :param flash_text: Flashing button text
        :type flash_text: str
        :param parent: Parent widget
        :type parent: QWidget, optional
        """
        super().__init__(parent)
        self.setObjectName("FlashingToolButton")
        self.setText(text)
        # Ensure the tool button shows text only
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        self._original_text = text
        self._flash_text = flash_text
        self.clicked.connect(self._on_clicked)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._restore_text)

        self._update_minimum_width()

    def _update_minimum_width(self) -> None:
        """Set minimum width to fit the longest text."""
        font_metrics = self.fontMetrics()
        width = max(
            font_metrics.horizontalAdvance(self._original_text),
            font_metrics.horizontalAdvance(self._flash_text),
        )
        # Add some padding for style
        self.setMinimumWidth(width + 20)

    @pyqtSlot()
    def _on_clicked(self) -> None:
        """Handle button click event and flash text for one second."""
        self.setText(self._flash_text)
        self._timer.start(1000)

    @pyqtSlot()
    def _restore_text(self) -> None:
        """Restore the original button text."""
        self.setText(self._original_text)
