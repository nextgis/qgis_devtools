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


import sys
from pathlib import Path
from typing import Union

from qgis.core import QgsApplication, QgsSettings
from qgis.PyQt.QtCore import QByteArray, QLocale, QMimeData
from qgis.PyQt.QtGui import QClipboard

from devtools.core.constants import PACKAGE_NAME


def locale() -> str:
    """Return the current locale code as a two-letter lowercase string.

    :returns: Two-letter lowercase locale code (e.g., "en", "fr").
    :rtype: str
    """
    override_locale = QgsSettings().value(
        "locale/overrideFlag", defaultValue=False, type=bool
    )
    if not override_locale:
        locale_full_name = QLocale.system().name()
    else:
        locale_full_name = QgsSettings().value("locale/userLocale", "")
    return locale_full_name[0:2].lower()


def python_path() -> str:
    """Return the path to the current Python executable.

    :returns: Path to the Python executable.
    :rtype: str
    """
    python_executable = sys.executable
    qgis_path = Path(python_executable).parent

    if sys.platform == "win32":
        for candidate in (qgis_path / "python3.exe", qgis_path / "python.exe"):
            if candidate.exists():
                return str(candidate)
        return python_executable

    if sys.platform == "darwin":
        wrapper = qgis_path / "python"
        if wrapper.exists():
            return str(wrapper)

        for candidate in (qgis_path / "python3.12", qgis_path / "python3"):
            if candidate.exists():
                return str(candidate)

        return python_executable

    # linux/other
    return python_executable


def set_clipboard_data(
    mime_type: str, data: Union[QByteArray, bytes, bytearray], text: str = ""
) -> None:
    """Set clipboard data with the specified MIME type and text.

    This function is a duplicate of QgsClipboard.setData, which is not
    available in Python bindings.

    :param mime_type: MIME type for the clipboard data.
    :type mime_type: str
    :param data: Data to set in the clipboard.
    :type data: Union[QByteArray, bytes, bytearray]
    :param text: Text to set in the clipboard.
    :type text: str
    :returns: None
    """
    mime_data = QMimeData()
    mime_data.setData(mime_type, data)
    if len(text) > 0:
        mime_data.setText(text)

    clipboard = QgsApplication.clipboard()
    assert clipboard is not None
    if sys.platform == "linux":
        selection_mode = QClipboard.Mode.Selection
        clipboard.setMimeData(mime_data, selection_mode)
    clipboard.setMimeData(mime_data, QClipboard.Mode.Clipboard)


def utm_tags(utm_medium: str, *, utm_campaign: str = "constant") -> str:
    """Generate a UTM tag string with customizable medium and campaign.

    :param utm_medium: UTM medium value.
    :type utm_medium: str
    :param utm_campaign: UTM campaign value.
    :type utm_campaign: str
    :returns: UTM tag string.
    :rtype: str
    """
    return (
        f"utm_source=qgis_plugin&utm_medium={utm_medium}"
        f"&utm_campaign={utm_campaign}&utm_term={PACKAGE_NAME}"
        f"&utm_content={locale()}"
    )
