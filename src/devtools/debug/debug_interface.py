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
from pathlib import Path
from typing import TYPE_CHECKING, Union

from qgis.PyQt.QtCore import QObject, pyqtSlot

from devtools.shared.qobject_metaclass import QObjectMetaClass

if TYPE_CHECKING:
    from console.console import PythonConsole


class DebugInterface(QObject, metaclass=QObjectMetaClass):
    """Abstract interface for debug managers in QGIS DevTools.

    Defines the contract for starting and stopping debug sessions.
    """

    @abstractmethod
    @pyqtSlot()
    def start(self) -> None:
        """Start the debug session."""
        ...

    @abstractmethod
    @pyqtSlot()
    def stop(self) -> None:
        """Stop the debug session."""
        ...

    @abstractmethod
    @pyqtSlot()
    def debug_script(self, script_path: Union[str, Path]) -> None:
        """Debug the script.

        :param script_path: Path to the script to debug.
        """
        ...

    @abstractmethod
    def breakpoint(self) -> None:
        """Toggle breakpoint at the current line."""
        ...

    @abstractmethod
    def integrate_into_python_console(
        self, python_console: "PythonConsole"
    ) -> None:
        """Integrate the debug interface into the Python console.

        :param python_console: The Python console instance to integrate with.
        """
        ...

    @abstractmethod
    def deintegrate_from_python_console(self) -> None:
        """Deintegrate the debug interface from the Python console."""
        ...
