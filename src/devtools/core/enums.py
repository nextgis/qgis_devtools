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

from dataclasses import dataclass
from enum import Enum


@dataclass
class IdeInfo:
    """Stores information about an IDE.

    :param full_name: Full name of the IDE.
    :type full_name: str
    """

    full_name: str


class Ide(Enum):
    """Enumeration of supported IDEs.

    Each member contains an :class:`IdeInfo` instance with IDE details.
    """

    VSCODE = IdeInfo("Visual Studio Code")
    VISUAL_STUDIO = IdeInfo("Visual Studio")
    ECLIPSE = IdeInfo("Eclipse")
