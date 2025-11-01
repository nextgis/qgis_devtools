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

from typing import TYPE_CHECKING, Optional

from qgis.core import QgsApplication
from qgis.utils import iface

from devtools.core.constants import PACKAGE_NAME
from devtools.core.exceptions import DevToolsError

if TYPE_CHECKING:
    from qgis.gui import QgisInterface

    assert isinstance(iface, QgisInterface)


class DebugError(DevToolsError):
    """General debug error in QGIS DevTools.

    :param log_message: Log message for debugging.
    :type log_message: str or None
    :param user_message: Message for user display.
    :type user_message: str or None
    :param detail: Detailed error description.
    :type detail: str or None
    """

    def __init__(
        self,
        log_message: Optional[str] = None,
        *,
        user_message: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        """Initialize DebugError.

        :param log_message: Log message for debugging.
        :type log_message: str or None
        :param user_message: Message for user display.
        :type user_message: str or None
        :param detail: Detailed error description.
        :type detail: str or None
        """
        default_message = QgsApplication.translate(
            "Exceptions", "An error occurred while running the plugin"
        )

        if log_message is None:
            log_message = default_message
        if user_message is None:
            user_message = default_message

        super().__init__(
            log_message=log_message,
            user_message=user_message,
            detail=detail,
        )


class DebugLibraryNotInstalledError(DebugError):
    """Debug library is not installed.

    Use this exception if debugpy or another debug backend is missing.
    """

    def __init__(self, lib_name: str) -> None:
        """Initialize DebugLibraryNotInstalledError."""
        base_message = QgsApplication.translate(
            "Exceptions", '"{lib_name}" library is not installed.'
        ).format(lib_name=lib_name)
        fix_message = QgsApplication.translate(
            "Exceptions",
            "Installation instructions can be found in the user guide.",
        )
        separator = " \u200b"
        super().__init__(
            log_message=base_message,
            user_message=f"{base_message}{separator}{fix_message}",
        )


class DebugPortInUseError(DebugError):
    """Debug port is already in use.

    Use this exception when the selected debug port is busy.
    """

    def __init__(self, port: int) -> None:
        """
        Initialize error for busy debug port.

        :param port: Port number that is in use.
        :type port: int
        """
        base_message = QgsApplication.translate(
            "Exceptions", "Port {port} is already in use."
        ).format(port=port)
        fix_message = QgsApplication.translate(
            "Exceptions", "Please choose another port in settings."
        )
        separator = " \u200b"
        super().__init__(
            log_message=base_message,
            user_message=f"{base_message}{separator}{fix_message}",
        )
        self.add_action(
            QgsApplication.translate("Exceptions", "Open settings"),
            lambda: iface.showOptionsDialog(
                iface.mainWindow(), f"{PACKAGE_NAME}/debug"
            ),
        )

    @staticmethod
    def is_port_in_use_error(error_message: str) -> bool:
        """
        Determine if error message means port is busy.

        :param error_message: Error message string.
        :type error_message: str
        :returns: True if port is in use, False otherwise.
        :rtype: bool
        """
        return (
            "Address already in use" in error_message
            or "[WinError 10048]" in error_message
        )


class DebugAlreadyRunningError(DebugError):
    """Debug session is already running."""

    def __init__(self) -> None:
        """Initialize DebugAlreadyRunningError."""
        message = QgsApplication.translate(
            "Exceptions", "Debug session is already running."
        )
        super().__init__(log_message=message, user_message=message)


class DebugAlreadyStartedInProcessError(DebugError):
    """Raised when the debug session has already been started in this process.

    Multiple starts can cause the debuggee to hang.
    """

    def __init__(self) -> None:
        """Initialize DebugAlreadyStartedInProcessError."""
        # fmt: off
        base_message = QgsApplication.translate(
            "Exceptions",
            "Debug session has already been started in this process."
        )
        fix_message = QgsApplication.translate(
            "Exceptions",
            "<b>Please restart QGIS</b>."
        )
        detail = (
            QgsApplication.translate(
                "Exceptions",
                "Multiple debug starts can cause the debuggee to hang."
            ) + " " + QgsApplication.translate(
                "Exceptions",
                "This is a limitation of the used debug library."
            )
        )
        # fmt: on
        separator = " \u200b"
        super().__init__(
            log_message=base_message,
            user_message=f"{base_message}{separator}{fix_message}",
            detail=detail,
        )
