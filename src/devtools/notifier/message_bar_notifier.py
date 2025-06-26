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


import uuid
from typing import TYPE_CHECKING, List, Optional

from qgis.core import Qgis
from qgis.PyQt.QtCore import QObject, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton, QWidget
from qgis.utils import iface

from devtools import DevToolsInterface
from devtools.core.constants import PLUGIN_NAME
from devtools.core.exceptions import DevToolsError, DevToolsWarning
from devtools.core.logging import logger
from devtools.core.utils import utm_tags
from devtools.notifier.notifier_interface import NotifierInterface

if TYPE_CHECKING:
    from qgis.gui import QgisInterface

    assert isinstance(iface, QgisInterface)


class MessageBarNotifier(NotifierInterface):
    """Notifier implementation for displaying messages and exceptions in QGIS.

    Provides methods to show messages and exceptions using QGIS message bar.
    """

    def __init__(self, parent: Optional[QObject]) -> None:
        """Initialize MessageBarNotifier with an optional parent QObject.

        :param parent: The parent QObject for this notifier.
        """
        super().__init__(parent)

    def __del__(self) -> None:
        """Dismiss all messages on object deletion."""
        self.dismiss_all()

    def display_message(
        self,
        message: str,
        *,
        level: Qgis.MessageLevel = Qgis.MessageLevel.Info,
        widgets: Optional[List[QWidget]] = None,
        **kwargs,  # noqa: ANN003, ARG002
    ) -> str:
        """Display a message to the user via the QGIS message bar.

        :param message: The message to display.
        :param level: The message level as Qgis.MessageLevel.
        :param widgets: Custom widgets for message.
        :return: An identifier for the displayed message.
        """
        custom_widgets = widgets if widgets else []

        message_bar = iface.messageBar()
        widget = message_bar.createMessage(PLUGIN_NAME, message)

        for custom_widget in custom_widgets:
            custom_widget.setParent(widget)
            widget.layout().addWidget(custom_widget)

        item = message_bar.pushWidget(widget, level)
        item.setObjectName("DevToolsMessageBarItem")
        message_id = str(uuid.uuid4())
        item.setProperty("DevToolsMessageId", message_id)

        logger.log(level, message)

        return message_id

    def display_exception(self, error: Exception) -> str:
        """Display an exception as an error message to the user.

        :param error: The exception to display.
        :return: An identifier for the displayed message.
        """
        if not isinstance(error, (DevToolsError, DevToolsWarning)):
            old_error = error
            error = (
                DevToolsError()
                if not isinstance(error, Warning)
                else DevToolsWarning()
            )
            error.__cause__ = old_error
            del old_error

        message = error.user_message.rstrip(".") + "."

        message_bar = iface.messageBar()
        widget = message_bar.createMessage(PLUGIN_NAME, message)

        if not isinstance(error, Warning):
            self._add_error_buttons(error, widget)

        level = (
            Qgis.MessageLevel.Critical
            if not isinstance(error, DevToolsWarning)
            else Qgis.MessageLevel.Warning
        )

        item = message_bar.pushWidget(widget, level)
        item.setObjectName("DevToolsMessageBarItem")
        item.setProperty("DevToolsMessageId", error.error_id)

        if level == Qgis.MessageLevel.Critical:
            logger.exception(error.log_message, exc_info=error)
        else:
            logger.warning(error.user_message)

        return error.error_id

    def dismiss_message(self, message_id: str) -> None:
        """Dismiss a specific message by its identifier.

        :param message_id: The identifier of the message to dismiss.
        """
        for notification in iface.messageBar().items():
            if (
                notification.objectName() != "DevToolsMessageBarItem"
                or notification.property("DevToolsMessageId") != message_id
            ):
                continue
            iface.messageBar().popWidget(notification)

    def dismiss_all(self) -> None:
        """Dismiss all currently displayed messages."""
        for notification in iface.messageBar().items():
            if notification.objectName() != "DevToolsMessageBarItem":
                continue
            iface.messageBar().popWidget(notification)

    def _add_error_buttons(
        self, error: DevToolsError, widget: QWidget
    ) -> None:
        def show_details() -> None:
            user_message = error.user_message.rstrip(".")
            QMessageBox.information(
                iface.mainWindow(), user_message, error.detail or ""
            )

        def let_us_know() -> None:
            plugin = DevToolsInterface.instance()
            tracker_url = plugin.metadata.get("general", "tracker")

            if "github" in tracker_url:
                QDesktopServices.openUrl(QUrl(tracker_url))
            else:
                utm = utm_tags("error")
                QDesktopServices.openUrl(QUrl(f"{tracker_url}/?{utm}"))

        def open_logs() -> None:
            iface.openMessageLog()

        if error.try_again is not None:

            def try_again() -> None:
                error.try_again()
                iface.messageBar().popWidget(widget)

            button = QPushButton(self.tr("Try again"))
            button.pressed.connect(try_again)
            widget.layout().addWidget(button)

        for action_name, action_callback in error.actions:
            button = QPushButton(action_name)
            button.pressed.connect(action_callback)
            widget.layout().addWidget(button)

        if error.detail is not None:
            button = QPushButton(self.tr("Details"))
            button.pressed.connect(show_details)
            widget.layout().addWidget(button)
        else:
            button = QPushButton(self.tr("Open logs"))
            button.pressed.connect(open_logs)
            widget.layout().addWidget(button)

        if type(error) is DevToolsError:
            button = QPushButton(self.tr("Let us know"))
            button.pressed.connect(let_us_know)
            widget.layout().addWidget(button)
