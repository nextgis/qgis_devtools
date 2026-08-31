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

import json
import runpy
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from qgis.PyQt.QtCore import QObject, QTimer, pyqtSlot
from qgis.PyQt.QtWidgets import QMenu, QMessageBox
from qgis.utils import iface

from devtools.core.enums import Ide
from devtools.core.logging import logger
from devtools.core.settings import DevToolsSettings
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
from devtools.platform.debugpy_handler import DebugpyHandler
from devtools.shared.ui import (
    FlashingPushButton,
    FlashingToolButton,
    WaitingDialog,
)

if TYPE_CHECKING:
    from qgis.gui import QgisInterface, QgsOptionsPageWidget
    from qgis.PyQt.QtWidgets import QWidget

    assert isinstance(iface, QgisInterface)


class DebugpyAdapter(AbstractDebugAdapter):
    """debugpy implementation for debug adapter.

    Provides integration with debugpy for remote debugging in QGIS DevTools.
    """

    __state: DebugState
    __timer: QTimer
    __start_notification_timer: QTimer

    __active_hostname: Optional[str]
    __active_port: Optional[int]

    __message_id: Optional[str]
    __handler: DebugpyHandler
    __log_directory: Optional[Path]

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize DebugpyAdapter instance.

        :param parent: Parent QObject.
        :type parent: QObject, optional
        """
        super().__init__(parent)

        self.__state = DebugState.STOPPED

        self.__timer = QTimer(self)
        self.__timer.setInterval(1000)  # 1s
        self.__timer.timeout.connect(self.__update_connected_state)
        self.__start_notification_timer = QTimer(self)
        self.__start_notification_timer.setSingleShot(True)
        self.__start_notification_timer.timeout.connect(
            self.__show_start_notification
        )

        self.__active_hostname = None
        self.__active_port = None
        self.__message_id = None
        self.__handler = DebugpyHandler()
        self.__log_directory = None

        if not self.is_installed:
            logger.debug("debugpy is not installed")
            return

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

    @property
    def is_installed(self) -> bool:
        """Check if the debug adapter is installed.

        :returns: True if the adapter is installed, False otherwise.
        :rtype: bool
        """
        return self.__handler.is_installed

    @property
    def supports_stop(self) -> bool:
        """Return whether debugpy can stop its process-global server."""
        return False

    @property
    def supports_restart(self) -> bool:
        """Return whether debugpy can restart in the same QGIS process."""
        return False

    def can_start(self) -> Tuple[bool, Optional[str]]:
        """Check if the debug adapter can be started.

        :returns: Tuple (can_start, reason). If can_start is False, reason
                  contains the explanation.
        :rtype: Tuple[bool, Optional[str]]
        """
        error = None

        if not self.is_installed:
            error = DebugLibraryNotInstalledError("debugpy")

        elif self.__handler.is_started:
            error = DebugAlreadyStartedInProcessError()

        if error is not None:
            message = error.user_message.replace("\u200b", "<br><br>")
            if error.detail:
                message += "<br><br>" + error.detail
            return False, message

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
        if not self.is_installed:
            error = DebugLibraryNotInstalledError("debugpy")
            error.add_action(self.tr("User Guide"), self.open_docs.emit)
            raise error

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

        try:
            self.__enable_logging()
            self.__handler.configure(python_path())
            self.__active_hostname, self.__active_port = (
                self.__start_listening(endpoints)
            )
        except Exception:
            self.__log_diagnostics()
            raise

        if settings.show_notification:
            # Delayed notification to avoid bug with unusable messages
            # when adding before UI is loaded
            self.__start_notification_timer.start(0)
        else:
            logger.info(
                self.tr("Debug session started at {hostname}:{port}").format(
                    hostname=self.__active_hostname, port=self.__active_port
                ),
            )

        self.__timer.start()
        self.__set_state(DebugState.RUNNING)

    @pyqtSlot()
    def stop(self) -> None:
        """Leave the process-global debugpy server running.

        debugpy remains active until QGIS exits. It has no supported shutdown
        API, and calling vendored pydevd internals during disconnect is unsafe.
        """
        return

    def unload(self) -> None:
        """Stop adapter-owned timers before its QObject is deleted."""
        self.__timer.stop()
        self.__start_notification_timer.stop()

    def debug_script(self, script_path: Union[str, Path]) -> None:
        """Debug the script.

        :param script_path: Path to the script to debug.
        """
        script_path = Path(script_path)

        if self.state == DebugState.STOPPED:
            ok, reason = self.can_start()
            if not ok:
                message_box = QMessageBox(iface.mainWindow())
                message_box.setIcon(QMessageBox.Icon.Warning)
                message_box.setWindowTitle(self.tr("Cannot start debugging"))
                message_box.setText(reason)
                message_box.setStandardButtons(
                    QMessageBox.StandardButtons()
                    | QMessageBox.StandardButton.Ok
                    | QMessageBox.StandardButton.Help
                )
                help_button = message_box.button(
                    QMessageBox.StandardButton.Help
                )
                help_button.setText(self.tr("User Guide"))
                help_button.clicked.connect(self.open_docs)
                message_box.exec()
                return

            self.start()

        if self.state != DebugState.RUNNING_AND_USER_CONNECTED:
            title = self.tr("Waiting for client...")
            message = self.tr(
                "Waiting for client to connect to debugger at {host}:{port}"
            ).format(host=self.__active_hostname, port=self.__active_port)
            dialog = WaitingDialog(title, message, iface.mainWindow())

            copy_params_button = FlashingPushButton(
                self.tr("Copy launch.json template"), self.tr("Copied!")
            )
            copy_params_button.clicked.connect(self.__copy_params)

            dialog.add_button(copy_params_button)

            def checker() -> None:
                if self.state == DebugState.RUNNING_AND_USER_CONNECTED:
                    dialog.accept()
                elif self.state == DebugState.STOPPED:
                    dialog.reject()

            self.state_changed.connect(checker)
            try:
                dialog.exec()
            finally:
                self.state_changed.disconnect(checker)

            if dialog.result() != WaitingDialog.DialogCode.Accepted:
                return

        runpy.run_path(
            script_path.as_posix(),
            run_name="__main__",
            init_globals={
                "iface": iface,
                "devtools": DevToolsInterface.instance(),
            },
        )

    def breakpoint(self) -> None:
        """Toggle breakpoint at the current line."""
        self.__handler.breakpoint()

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
        if self.__handler.is_started:
            raise DebugAlreadyStartedInProcessError

        result_endpoint = ("", -1)

        for i, endpoint in enumerate(endpoints):
            logger.debug(f"Try listen at {endpoint}")

            try:
                result_endpoint = self.__handler.listen(endpoint)

                break

            except Exception as error:
                error_message = str(error)

                if i + 1 != len(
                    endpoints
                ) and DebugPortInUseError.is_port_in_use_error(error_message):
                    continue

                if DebugPortInUseError.is_port_in_use_error(error_message):
                    raise DebugPortInUseError(endpoint[-1]) from error

                raise

        return result_endpoint

    def __enable_logging(self) -> None:
        if (
            self.__log_directory is not None
            or not DevToolsSettings().is_debug_logs_enabled
        ):
            return

        temporary_directory = None
        try:
            temporary_directory = Path(
                tempfile.mkdtemp(prefix="qgis-devtools-debugpy-")
            )
            self.__log_directory = self.__handler.enable_logging(
                temporary_directory
            )
        except (OSError, RuntimeError):
            if temporary_directory is not None:
                shutil.rmtree(temporary_directory, ignore_errors=True)
            logger.debug("Can't enable debugpy diagnostics")
            return

        if self.__log_directory != temporary_directory:
            shutil.rmtree(temporary_directory, ignore_errors=True)
        logger.debug(f"debugpy diagnostics directory: {self.__log_directory}")

    def __log_diagnostics(self) -> None:
        if self.__log_directory is None:
            return

        try:
            log_files = self.__handler.diagnostic_log_files()
        except OSError:
            logger.exception("Can't list debugpy diagnostic logs")
            return

        if not log_files:
            logger.debug("debugpy did not produce diagnostic logs")
            return

        remaining_log_size = 256 * 1024
        for log_file in log_files:
            if remaining_log_size == 0:
                logger.debug(
                    "debugpy diagnostics output was truncated at 262144 bytes"
                )
                break

            try:
                with log_file.open("rb") as log_stream:
                    log_stream.seek(0, 2)
                    log_size = log_stream.tell()
                    max_log_size = min(64 * 1024, remaining_log_size)
                    log_stream.seek(max(log_size - max_log_size, 0))
                    log_content = (
                        log_stream.read(max_log_size)
                        .decode("utf-8", errors="replace")
                        .strip()
                    )
            except OSError:
                logger.exception(
                    f"Can't read debugpy diagnostic log: {log_file}"
                )
                continue

            remaining_log_size -= min(log_size, max_log_size)
            if log_content:
                if log_size > max_log_size:
                    log_content = (
                        f"[Only the last {max_log_size} bytes are shown.]\n"
                        f"{log_content}"
                    )
                logger.debug(
                    f"debugpy diagnostics from {log_file.name}:\n{log_content}"
                )

    @pyqtSlot()
    def __update_connected_state(self) -> None:
        self.__set_state(
            DebugState.RUNNING_AND_USER_CONNECTED
            if self.__handler.is_client_connected()
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
        if self.state == DebugState.STOPPED:
            return

        copy_params_button = FlashingToolButton(
            self.tr("Copy launch.json template"), self.tr("Copied!")
        )
        menu = QMenu(copy_params_button)
        copy_with_mappings_action = menu.addAction(
            self.tr("Copy launch.json template with path mappings")
        )
        copy_with_mappings_action.triggered.connect(
            lambda: self.__copy_params(True)
        )
        copy_params_button.setMenu(menu)
        copy_params_button.setPopupMode(
            FlashingToolButton.ToolButtonPopupMode.MenuButtonPopup
        )

        copy_params_button.clicked.connect(self.__copy_params)

        notifier = DevToolsInterface.instance().notifier
        self.__message_id = notifier.display_message(
            self.tr("Debug session started at {hostname}:{port}").format(
                hostname=self.__active_hostname, port=self.__active_port
            ),
            widgets=[copy_params_button],
        )

    @pyqtSlot()
    def __copy_params(self, with_mappings: bool = False) -> None:
        plugins_path = DevToolsInterface.instance().path.parent.as_posix()

        mappings = ""
        if with_mappings:
            mappings = f"""
                "pathMappings": [
                    {{
                        "localRoot": "${{workspaceFolder}}",
                        "remoteRoot": "{plugins_path}/<YOUR_PLUGIN_NAME>"
                    }}
                ],
            """

        content = f"""
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
                        {mappings}
                        "justMyCode": true
                    }}
                ]
            }}
        """

        try:
            parsed_json = json.loads(content)
            formatted_content = json.dumps(
                parsed_json, indent=4, ensure_ascii=False, sort_keys=False
            )
        except Exception:
            formatted_content = content

        set_clipboard_data(
            "application/json", formatted_content.encode(), formatted_content
        )
        set_clipboard_data(
            "application/json", formatted_content.encode(), formatted_content
        )
