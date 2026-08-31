# QGIS DevTools Plugin
# Copyright (C) 2025  NextGIS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or any
# later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import importlib.util
from pathlib import Path
from typing import Any, List, Optional, Tuple


class DebugpyHandler:
    """Provide access to the optional debugpy package."""

    def __init__(self) -> None:
        """Initialize the optional debugpy integration."""
        self.__debugpy: Any = None
        self.__debugpy_internal: Any = None
        self.__log_directory: Optional[Path] = None
        self.__version: Optional[str] = None

        if not importlib.util.find_spec("debugpy"):
            return

        import debugpy  # noqa: PLC0415
        import debugpy.server.api as debugpy_internal  # noqa: PLC0415

        self.__debugpy = debugpy
        self.__debugpy_internal = debugpy_internal
        self.__version = getattr(debugpy, "__version__", "unknown")

        if not hasattr(self.__debugpy_internal.listen, "called"):
            self.__debugpy_internal.listen.called = False

    @property
    def is_installed(self) -> bool:
        """Return whether debugpy is available in the QGIS Python runtime."""
        return self.__debugpy is not None

    @property
    def version(self) -> Optional[str]:
        """Return the installed debugpy version, if available."""
        return self.__version

    @property
    def is_started(self) -> bool:
        """Return whether debugpy has started in the current process."""
        # https://github.com/microsoft/debugpy/blob/1aff9aa541955b967f41895570d4c0b54a7504d9/src/debugpy/server/api.py#L143
        return self.is_installed and self.__debugpy_internal.listen.called

    def configure(self, python_executable: str) -> None:
        """Configure debugpy for the interpreter used by its adapter."""
        self.__debugpy.configure(python=python_executable)

    def listen(self, endpoint: Tuple[str, int]) -> Tuple[str, int]:
        """Start debugpy listening at an endpoint."""
        result_endpoint = self.__debugpy.listen(
            endpoint if endpoint[0] else endpoint[-1]
        )
        self.__debugpy_internal.listen.called = True
        return result_endpoint

    def breakpoint(self) -> None:
        """Trigger a debugpy breakpoint."""
        self.__debugpy.breakpoint()

    def is_client_connected(self) -> bool:
        """Return whether a debug client is connected."""
        return self.__debugpy.is_client_connected()

    def enable_logging(self, directory: Path) -> Path:
        """Enable debugpy file logging and return its active directory."""
        # debugpy logging is process-global, so preserve its directory across
        # plugin reloads on the same process-global module.
        log_directory = getattr(
            self.__debugpy_internal, "devtools_log_directory", None
        )
        if log_directory is not None:
            self.__log_directory = Path(log_directory)
            return self.__log_directory

        self.__debugpy.log_to(str(directory))
        self.__log_directory = directory
        self.__debugpy_internal.devtools_log_directory = directory
        return directory

    def diagnostic_log_files(self) -> List[Path]:
        """Return debugpy diagnostic log files from the active directory."""
        if self.__log_directory is None:
            return []
        return sorted(self.__log_directory.glob("debugpy.*.log"))
