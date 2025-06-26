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

from qgis.PyQt.QtCore import QObject, pyqtSlot

from devtools.shared.qobject_metaclass import QObjectMetaClass


class DebugInterface(QObject, metaclass=QObjectMetaClass):
    """Abstract interface for debug managers in QGIS DevTools.

    Defines the contract for starting and stopping debug sessions.
    """

    @abstractmethod
    @pyqtSlot()
    def start(self) -> None:
        """Start the debug session.

        :raises NotImplementedError: Must be implemented in subclass.
        """
        ...

    @abstractmethod
    @pyqtSlot()
    def stop(self) -> None:
        """Stop the debug session.

        :raises NotImplementedError: Must be implemented in subclass.
        """
        ...
