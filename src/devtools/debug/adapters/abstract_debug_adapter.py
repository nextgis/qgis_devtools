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


from abc import abstractmethod
from typing import TYPE_CHECKING, List, Optional, Tuple

from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot

from devtools.debug.enums import DebugState
from devtools.shared.qobject_metaclass import QObjectMetaClass

if TYPE_CHECKING:
    from qgis.gui import QgsOptionsPageWidget
    from qgis.PyQt.QtWidgets import QWidget

    from devtools.core.enums import Ide


class AbstractDebugAdapter(QObject, metaclass=QObjectMetaClass):
    """Abstract base class for debug adapters."""

    state_changed = pyqtSignal(DebugState)
    """Signal emitted when the debug adapter state changes."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Return the adapter name.

        :returns: Adapter name.
        :rtype: str
        """
        ...

    @classmethod
    @abstractmethod
    def supported_ide(cls) -> List["Ide"]:
        """Return the list of supported IDEs.

        :returns: List of supported IDEs.
        :rtype: List[Ide]
        """
        ...

    @property
    @abstractmethod
    def state(self) -> "DebugState":
        """Return the current debug adapter state.

        :returns: Current debug state.
        :rtype: DebugState
        """
        ...

    @abstractmethod
    def can_start(self) -> Tuple[bool, Optional[str]]:
        """Check if the debug adapter can be started.

        :returns: Tuple (can_start, reason). If can_start is False, reason
                  contains the explanation.
        :rtype: Tuple[bool, Optional[str]]
        """
        ...

    @abstractmethod
    @pyqtSlot()
    def start(self) -> None:
        """Start the debug adapter.

        This method should be implemented by subclasses to start the debugging
        process.
        """
        ...

    @abstractmethod
    @pyqtSlot()
    def stop(self) -> None:
        """Stop the debug adapter.

        This method should be implemented by subclasses to stop the debugging
        process.
        """
        ...

    @classmethod
    @abstractmethod
    def create_settings_widget(
        cls, parent: Optional["QWidget"] = None
    ) -> "QgsOptionsPageWidget":
        """Create and return the settings widget for the debug adapter.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        :returns: Settings widget for the adapter.
        :rtype: QgsOptionsPageWidget
        """
