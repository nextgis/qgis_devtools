# QGIS DevTools Plugin
# Copyright (C) 2025  NextGIS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import importlib.util
from textwrap import dedent
from typing import TYPE_CHECKING, List, Optional, Tuple

from qgis.PyQt.QtCore import QObject, QTimer, pyqtSlot

from devtools.core.enums import Ide
from devtools.core.logging import logger
from devtools.core.utils import python_path, set_clipboard_data
from devtools.debug.adapters.abstract_debug_adapter import AbstractDebugAdapter
from devtools.debug.adapters.debugpy.debugpy_settings import DebugpySettings
from devtools.debug.adapters.debugpy.ui.debugpy_settings_page import (
    DebugpySettingsPage,
)
from devtools.debug.enums import DebugState
from devtools.debug.exceptions import (
    DebugAlreadyStartedInProcessError,
    DebugLibraryNotInstalledError,
    DebugPortInUseError,
)
from devtools.devtools_interface import DevToolsInterface
from devtools.shared.ui import FlashingPushButton

if TYPE_CHECKING:
    from qgis.gui import QgsOptionsPageWidget
    from qgis.PyQt.QtWidgets import QWidget

debugpy = None
debugpy_internal = None
pydevd = None
if importlib.util.find_spec("debugpy"):
    import debugpy
    import debugpy.server.api as debugpy_internal
    from debugpy._vendored.pydevd import pydevd


class DebugpyAdapter(AbstractDebugAdapter):
    """debugpy implementation for debug adapter.

    Provides integration with debugpy for remote debugging in QGIS DevTools.
    """

    __state: DebugState
    __timer: QTimer

    __active_hostname: Optional[str]
    __active_port: Optional[int]

    __message_id: Optional[str]

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize DebugpyAdapter instance.

        :param parent: Parent QObject.
        :type parent: QObject, optional
        """
        super().__init__(parent)

        self.__state = DebugState.STOPPED

        if debugpy is None:
            logger.debug("debugpy is not installed")
            return

        self.__timer = QTimer(self)
        self.__timer.setInterval(1000)  # 1s
        self.__timer.timeout.connect(self.__update_connected_state)

        self.__active_hostname = None
        self.__active_port = None
        self.__message_id = None

    @classmethod
    def name(cls) -> str:
        """Return the adapter name.

        :returns: Adapter name.
        :rtype: str
        """
        return "debugpy"

    @classmethod
    def supported_ide(cls) -> List[Ide]:
        """Return the list of supported IDEs.

        :returns: List of supported IDEs.
        :rtype: List[Ide]
        """
        return [Ide.VSCODE, Ide.VISUAL_STUDIO]

    @property
    def state(self) -> DebugState:
        """Return the current debug adapter state.

        :returns: Current debug state.
        :rtype: DebugState
        """
        return self.__state

    def can_start(self) -> Tuple[bool, Optional[str]]:
        """Check if the debug adapter can be started.

        :returns: Tuple (can_start, reason). If can_start is False, reason
                  contains the explanation.
        :rtype: Tuple[bool, Optional[str]]
        """
        if debugpy is None:
            return (
                False,
                self.tr('"{lib_name}" library is not installed.').format(
                    lib_name="debugpy"
                ),
            )

        return True, None

    @property
    def hostname(self) -> Optional[str]:
        """Return the active hostname for the debug session.

        :returns: Hostname or None.
        :rtype: Optional[str]
        """
        return self.__active_hostname

    @property
    def port(self) -> Optional[int]:
        """Return the active port for the debug session.

        :returns: Port or None.
        :rtype: Optional[int]
        """
        return self.__active_port

    @pyqtSlot()
    def start(self) -> None:
        """Start the debug session.

        :raises DebugLibraryNotInstalledError: If debugpy is not installed.
        """
        if debugpy is None:
            raise DebugLibraryNotInstalledError("debugpy")

        settings = DebugpySettings()

        hostname = settings.hostname or ""

        port_from = 0
        port_to = 0
        if not settings.auto_select_port:
            port_from = settings.port_from
            port_to = settings.port_to

        endpoints = [
            (hostname, port) for port in range(port_from, port_to + 1)
        ]

        debugpy.configure(python=python_path())
        self.__active_hostname, self.__active_port = self.__start_listening(
            endpoints
        )

        if settings.show_notification:
            # Delayed notification to avoid bug with unusable messages
            # when adding before UI is loaded
            QTimer.singleShot(0, self.__show_start_notification)
        else:
            logger.info(
                self.tr(
                    f"Debug session started at {self.__active_hostname}:{self.__active_port}"
                ),
            )

        self.__timer.start()
        self.state_changed.emit(DebugState.RUNNING)

    @pyqtSlot()
    def stop(self) -> None:
        """Stop the debug session.

        :raises DebugLibraryNotInstalledError: If debugpy is not installed.
        """
        if debugpy is None:
            raise DebugLibraryNotInstalledError("debugpy")

        self.__timer.stop()
        pydevd.stoptrace()

        self.__active_hostname = None
        self.__active_port = None

        if self.__message_id is not None:
            notifier = DevToolsInterface.instance().notifier
            notifier.dismiss_message(self.__message_id)

        self.__set_state(DebugState.STOPPED)

    @classmethod
    def create_settings_widget(
        cls, parent: Optional["QWidget"] = None
    ) -> "QgsOptionsPageWidget":
        """Create and return the settings widget for the debug adapter.

        :param parent: Optional parent widget.
        :type parent: Optional[QWidget]
        :returns: Settings widget for the adapter.
        :rtype: QgsOptionsPageWidget
        """
        return DebugpySettingsPage(parent)

    def __start_listening(
        self, endpoints: List[Tuple[str, int]]
    ) -> Tuple[str, int]:
        if not hasattr(debugpy_internal.listen, "called"):
            # Support for older versions
            debugpy_internal.listen.called = False  # type: ignore reportFunctionMemberAccess

        if debugpy_internal.listen.called:  # type: ignore reportFunctionMemberAccess
            # https://github.com/microsoft/debugpy/blob/1aff9aa541955b967f41895570d4c0b54a7504d9/src/debugpy/server/api.py#L143
            raise DebugAlreadyStartedInProcessError

        result_endpoint = ("", -1)

        for i, endpoint in enumerate(endpoints):
            logger.debug(f"Try listen at {endpoint}")

            try:
                result_endpoint = debugpy.listen(
                    endpoint if endpoint[0] else endpoint[-1]
                )
                debugpy_internal.listen.called = True  # type: ignore reportFunctionMemberAccess

                break

            except Exception as error:
                error_message = str(error)

                if i + 1 != len(endpoints):
                    continue

                if "Address already in use" in error_message:
                    raise DebugPortInUseError(endpoint[-1]) from error

                raise

        return result_endpoint

    @pyqtSlot()
    def __update_connected_state(self) -> None:
        self.__set_state(
            DebugState.RUNNING_AND_USER_CONNECTED
            if debugpy.is_client_connected()
            else DebugState.RUNNING
        )

    def __set_state(self, state: DebugState) -> None:
        if state == self.__state:
            return

        if state == DebugState.RUNNING_AND_USER_CONNECTED:
            logger.info(self.tr("Client connected"))
        elif (
            self.__state == DebugState.RUNNING_AND_USER_CONNECTED
            and state == DebugState.RUNNING
        ):
            logger.info(self.tr("Client disconnected"))

        self.__state = state
        self.state_changed.emit(self.__state)

    @pyqtSlot()
    def __show_start_notification(self) -> None:
        copy_params_button = FlashingPushButton(
            self.tr("Copy launch.json template"), self.tr("Copied!")
        )
        copy_params_button.clicked.connect(self.__copy_params)

        notifier = DevToolsInterface.instance().notifier
        self.__message_id = notifier.display_message(
            self.tr(
                f"Debug session started at {self.__active_hostname}:{self.__active_port}"
            ),
            widgets=[copy_params_button],
        )

    @pyqtSlot()
    def __copy_params(self) -> None:
        plugins_path = DevToolsInterface.instance().path.parent.as_posix()

        content = dedent(f"""
            {{
                "version": "0.2.0",
                "configurations": [
                    {{
                        "name": "Attach to QGIS",
                        "type": "debugpy",
                        "request": "attach",
                        "connect": {{
                            "host": "{self.__active_hostname}",
                            "port": {self.__active_port}
                        }},
                        "pathMappings": [
                            {{
                                "localRoot": "${{workspaceFolder}}",
                                "remoteRoot": "{plugins_path}/<YOUR_PLUGIN_NAME>"
                            }}
                        ],
                        "justMyCode": true
                    }}
                ]
            }}
        """)
        set_clipboard_data("application/json", content.encode(), content)
