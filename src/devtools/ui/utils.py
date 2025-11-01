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
from typing import Optional, Union

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt
from qgis.PyQt.QtGui import QIcon, QPainter, QPixmap
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import QLabel

from devtools.core.constants import PACKAGE_NAME
from devtools.core.logging import logger
from devtools.devtools_interface import DevToolsInterface


def draw_icon(label: QLabel, icon: QIcon, *, size: int = 24) -> None:
    """Draw an icon on a QLabel with the specified size.

    :param label: QLabel to draw the icon on.
    :type label: QLabel
    :param icon: QIcon to draw.
    :type icon: QIcon
    :param size: Icon size in pixels.
    :type size: int
    :returns: None
    """
    pixmap = icon.pixmap(icon.actualSize(QSize(size, size)))
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)


def qgis_icon(icon_name: str) -> QIcon:
    """Return a QGIS theme icon by name.

    :param icon_name: Name of the icon.
    :type icon_name: str
    :returns: QIcon instance for the QGIS theme icon.
    :rtype: QIcon
    """
    icon = QgsApplication.getThemeIcon(icon_name)
    if icon.isNull():
        icon = QIcon(f":images/themes/default/{icon_name}")
    return icon


def plugin_icon(icon_path: Union[Path, str, None] = None) -> QIcon:
    """Return the plugin icon as QIcon.

    :param icon_path: Path or name of the icon file.
    :type icon_path: Union[Path, str, None]
    :returns: QIcon instance for the plugin icon.
    :rtype: QIcon
    """
    plugin = DevToolsInterface.instance()
    icons_path = plugin.path / "resources" / "icons"
    if icon_path is None:
        icon_path = f"{PACKAGE_NAME}_logo.svg"
    full_path = icons_path / icon_path
    if not full_path.exists():
        logger.warning(f"Icon {icon_path} does not exist")
    return QIcon(str(full_path))


def material_icon(
    name: str, *, color: str = "", size: Optional[int] = None
) -> QIcon:
    """Return a material icon as QIcon, optionally recolored and resized.

    :param name: Name of the material icon (without .svg extension).
    :type name: str
    :param color: Color to apply to the icon (hex string).
    :type color: str
    :param size: Size of the icon in pixels.
    :type size: Optional[int]
    :returns: QIcon instance for the material icon.
    :rtype: QIcon
    :raises FileNotFoundError: If the SVG file is not found.
    :raises ValueError: If the SVG cannot be loaded.
    """
    plugin = DevToolsInterface.instance()
    material_icons_path = plugin.path / "resources" / "icons" / "material"

    svg_path = None
    for path in material_icons_path.glob(f"{name}*"):
        if path.is_file():
            svg_path = path
            break

    if svg_path is None:
        message = f"SVG file not found: {svg_path}"
        raise FileNotFoundError(message)

    svg_content = svg_path.read_text()

    if color == "":
        color = QgsApplication.palette().text().color().name()

    modified_svg = svg_content.replace('fill="#ffffff"', f'fill="{color}"')

    byte_array = QByteArray(modified_svg.encode("utf-8"))
    renderer = QSvgRenderer()
    if not renderer.load(byte_array):
        message = "Failed to load SVG."
        raise ValueError(message)

    pixmap = QPixmap(
        renderer.defaultSize() if size is None else QSize(size, size)
    )
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def icon_to_base64(icon: QIcon, size: Optional[int] = None) -> str:
    """Convert a QIcon to a base64-encoded string.

    :param icon: QIcon to convert.
    :type icon: QIcon
    :returns: Base64-encoded string of the icon.
    :rtype: str
    """
    icon_size = QSize(32, 32) if size is None else QSize(size, size)
    pixmap = icon.pixmap(icon_size)

    buffer = QByteArray()
    qbuffer = QBuffer(buffer)
    qbuffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(qbuffer, "PNG")
    qbuffer.close()

    return "data:image/png;base64, " + buffer.toBase64().data().decode("utf-8")
