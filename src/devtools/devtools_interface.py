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


import configparser
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from qgis import utils
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QObject, QTranslator, pyqtSignal

from devtools.core.constants import PACKAGE_NAME
from devtools.core.logging import logger, unload_logger
from devtools.shared.qobject_metaclass import QObjectMetaClass

if TYPE_CHECKING:
    from devtools.debug.debug_interface import DebugInterface
    from devtools.notifier.notifier_interface import NotifierInterface


class DevToolsInterface(QObject, metaclass=QObjectMetaClass):
    """Interface for the QGIS DevTools plugin.

    This abstract base class provides singleton access to the plugin
    instance, exposes plugin metadata, version, and path, and defines
    abstract properties and methods that must be implemented by concrete
    subclasses.
    """

    settings_changed = pyqtSignal()

    @classmethod
    def instance(cls) -> "DevToolsInterface":
        """Return the singleton instance of the DevToolsInterface plugin.

        :returns: The DevToolsInterface plugin instance.
        :rtype: DevToolsInterface
        :raises AssertionError: If the plugin has not been created yet.
        """
        plugin = utils.plugins.get(PACKAGE_NAME)
        assert plugin is not None, "Using a plugin before it was created"
        return plugin

    @property
    def metadata(self) -> configparser.ConfigParser:
        """Return the parsed metadata for the plugin.

        :returns: Parsed metadata as a ConfigParser object.
        :rtype: configparser.ConfigParser
        """
        metadata = utils.plugins_metadata_parser.get(PACKAGE_NAME)
        assert metadata is not None, "Using a plugin before it was created"
        return metadata

    @property
    def version(self) -> str:
        """Return the plugin version.

        :returns: Plugin version string.
        :rtype: str
        """
        return self.metadata.get("general", "version")

    @property
    def path(self) -> "Path":
        """Return the plugin path.

        :returns: Path to the plugin directory.
        :rtype: Path
        """
        return Path(__file__).parent

    # @property
    # @abstractmethod
    # def toolbar(self) -> "QToolBar":
    #     """Return the plugin toolbar instance.

    #     :returns: Toolbar instance for the plugin.
    #     :rtype: QToolBar
    #     """
    #     ...

    @property
    @abstractmethod
    def notifier(self) -> "NotifierInterface":
        """Return the notifier for displaying messages to the user.

        :returns: Notifier interface instance.
        :rtype: NotifierInterface
        """
        ...

    @property
    @abstractmethod
    def debug(self) -> "DebugInterface":
        """Return the debug manager.

        :returns: An instance of DebugInterface.
        :rtype: DebugInterface
        """
        ...

    def initGui(self) -> None:
        """Initialize the GUI components and load necessary resources."""
        self.__translators = list()

        try:
            self._load()
        except Exception:
            logger.exception("An error occurred while plugin loading")

    def unload(self) -> None:
        """Unload the plugin and perform cleanup operations."""
        try:
            self._unload()
        except Exception:
            logger.exception("An error occurred while plugin unloading")

        self.__unload_translations()
        unload_logger()

    @abstractmethod
    def _load(self) -> None:
        """Load the plugin resources and initialize components.

        This method must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def _unload(self) -> None:
        """Unload the plugin resources and clean up components.

        This method must be implemented by subclasses.
        """
        ...

    def _add_translator(self, translator_path: Path) -> None:
        """Add a translator for the plugin.

        :param translator_path: Path to the translation file.
        :type translator_path: Path
        """
        translator = QTranslator()
        is_loaded = translator.load(str(translator_path))
        if not is_loaded:
            logger.debug(f"Translator {translator_path} wasn't loaded")
            return

        is_installed = QgsApplication.installTranslator(translator)
        if not is_installed:
            logger.error(f"Translator {translator_path} wasn't installed")
            return

        # Should be kept in memory
        self.__translators.append(translator)

    def __unload_translations(self) -> None:
        """Remove all translators added by the plugin."""
        for translator in self.__translators:
            QgsApplication.removeTranslator(translator)
        self.__translators.clear()
