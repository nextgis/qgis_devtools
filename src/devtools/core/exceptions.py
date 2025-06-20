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
import uuid
from typing import Any, Callable, Optional

from qgis.core import QgsApplication


class DevToolsExceptionInfoMixin:
    """Mixin providing common fields and logic for DevTools errors and warnings."""

    _error_id: str
    _log_message: str
    _user_message: str
    _detail: Optional[str]
    _try_again: Optional[Callable[[], Any]]

    def __init__(
        self,
        log_message: Optional[str] = None,
        *,
        user_message: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        self._error_id = str(uuid.uuid4())

        default_message = QgsApplication.translate(
            "Exceptions", "An error occurred while running the plugin"
        )

        self._log_message = (
            log_message if log_message else default_message
        ).strip()

        self._user_message = (
            user_message if user_message else default_message
        ).strip()
        self.add_note("Message: " + self._user_message)

        self._detail = detail
        if self._detail is not None:
            self._detail = self._detail.strip()
            self.add_note("Details: " + self._detail)

        self._try_again = None

    @property
    def error_id(self) -> str:
        return self._error_id

    @property
    def log_message(self) -> str:
        return self._log_message

    @property
    def user_message(self) -> str:
        return self._user_message

    @property
    def detail(self) -> Optional[str]:
        return self._detail

    @property
    def try_again(self) -> Optional[Callable[[], Any]]:
        return self._try_again

    @try_again.setter
    def try_again(self, try_again: Optional[Callable[[], Any]]) -> None:
        self._try_again = try_again

    if sys.version_info < (3, 11):

        def add_note(self, note: str) -> None:
            if not isinstance(note, str):
                message = "Note must be a string"
                raise TypeError(message)
            message: str = self.args[0]
            self.args = (f"{message}\n{note}",)


class DevToolsError(DevToolsExceptionInfoMixin, Exception):
    """Base exception for errors in the QGIS DevTools plugin.

    Inherit from this class to define custom error types for the plugin.
    """

    def __init__(
        self,
        log_message: Optional[str] = None,
        *,
        user_message: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        DevToolsExceptionInfoMixin.__init__(
            self,
            log_message,
            user_message=user_message,
            detail=detail,
        )
        Exception.__init__(self, self._log_message)


class DevToolsWarning(DevToolsExceptionInfoMixin, UserWarning):
    """Base warning for non-critical issues in the QGIS DevTools plugin.

    Inherit from this class to define custom warning types for the plugin.
    """

    def __init__(
        self,
        log_message: Optional[str] = None,
        *,
        user_message: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        DevToolsExceptionInfoMixin.__init__(
            self,
            log_message,
            user_message=user_message,
            detail=detail,
        )
        Exception.__init__(self, self._log_message)


class DevToolsReloadAfterUpdateWarning(DevToolsWarning):
    """Warning raised when the plugin structure has changed after an update.

    This warning indicates that the plugin was successfully updated, but due to changes
    in its structure, it may fail to load properly until QGIS is restarted.
    """

    def __init__(self) -> None:
        # fmt: off
        super().__init__(
            log_message="Plugin structure changed",
            user_message=QgsApplication.translate(
                "Exceptions",
                "The plugin has been successfully updated. "
                "To continue working, please restart QGIS."
            ),
        )
        # fmt: on
