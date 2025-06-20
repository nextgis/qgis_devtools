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

from qgis.PyQt.QtCore import QObject

from devtools.shared.qobject_metaclass import QObjectMetaClass


class AbstractDebugAdapter(QObject, metaclass=QObjectMetaClass):
    """Abstract base class for debug adapters."""

    @abstractmethod
    def start(self) -> None:
        """Start the debug.

        :raises NotImplementedError: If not implemented in subclass.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the debugadapter.

        :raises NotImplementedError: If not implemented in subclass.
        """
        ...
