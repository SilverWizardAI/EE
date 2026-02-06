"""
Settings Manager

Persistent settings storage with Qt integration and JSON export.
Handles theme preferences, window geometry, user preferences.

Module Size Target: <400 lines (Current: ~200 lines)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import QSettings, QByteArray


logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Manages application settings with persistence.

    Features:
    - QSettings-based storage (platform-native)
    - JSON export/import for portability
    - Type-safe get/set with defaults
    - Theme management (dark/light modes)
    - Window geometry persistence
    - Custom preferences support

    Usage:
        settings = SettingsManager("MyOrg", "MyApp")
        settings.set("theme", "dark")
        theme = settings.get("theme", default="light")
        settings.save_window_geometry(window)
        settings.restore_window_geometry(window)
    """

    def __init__(self, organization: str, application: str):
        """
        Initialize settings manager.

        Args:
            organization: Organization name
            application: Application name
        """
        self.organization = organization
        self.application = application
        self._settings = QSettings(organization, application)

        # Ensure defaults are set
        self._set_defaults()

        logger.info(f"Settings initialized: {organization}/{application}")
        logger.info(f"Settings file: {self._settings.fileName()}")

    def _set_defaults(self):
        """Set default values if not present."""
        defaults = {
            "theme": "dark",
            "first_run": True,
            "window/maximized": False,
        }

        for key, value in defaults.items():
            if not self._settings.contains(key):
                self._settings.setValue(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value.

        Args:
            key: Setting key (can use / for nesting, e.g. "window/width")
            default: Default value if key doesn't exist

        Returns:
            Setting value or default
        """
        value = self._settings.value(key, default)
        logger.debug(f"Get setting: {key} = {value}")
        return value

    def set(self, key: str, value: Any):
        """
        Set setting value.

        Args:
            key: Setting key
            value: Value to store
        """
        self._settings.setValue(key, value)
        logger.debug(f"Set setting: {key} = {value}")

    def remove(self, key: str):
        """
        Remove a setting.

        Args:
            key: Setting key to remove
        """
        self._settings.remove(key)
        logger.debug(f"Removed setting: {key}")

    def contains(self, key: str) -> bool:
        """
        Check if setting exists.

        Args:
            key: Setting key

        Returns:
            True if setting exists
        """
        return self._settings.contains(key)

    def sync(self):
        """Flush settings to disk immediately."""
        self._settings.sync()
        logger.debug("Settings synced to disk")

    def clear(self):
        """Clear all settings."""
        self._settings.clear()
        self._set_defaults()
        logger.info("Settings cleared, defaults restored")

    # Window geometry management

    def save_window_geometry(self, window):
        """
        Save window geometry and state.

        Args:
            window: QMainWindow instance
        """
        self.set("window/geometry", window.saveGeometry())
        self.set("window/state", window.saveState())
        self.set("window/maximized", window.isMaximized())
        logger.debug("Window geometry saved")

    def restore_window_geometry(self, window) -> bool:
        """
        Restore window geometry and state.

        Args:
            window: QMainWindow instance

        Returns:
            True if geometry was restored
        """
        geometry = self.get("window/geometry")
        state = self.get("window/state")
        maximized = self.get("window/maximized", False)

        success = False
        if geometry and isinstance(geometry, QByteArray):
            window.restoreGeometry(geometry)
            success = True

        if state and isinstance(state, QByteArray):
            window.restoreState(state)

        if maximized:
            window.showMaximized()

        if success:
            logger.debug("Window geometry restored")
        return success

    # Theme management

    def get_theme(self) -> str:
        """
        Get current theme.

        Returns:
            "dark" or "light"
        """
        return self.get("theme", "dark")

    def set_theme(self, theme: str):
        """
        Set theme.

        Args:
            theme: "dark" or "light"
        """
        if theme not in ["dark", "light"]:
            logger.warning(f"Invalid theme: {theme}, defaulting to dark")
            theme = "dark"
        self.set("theme", theme)

    # JSON export/import

    def export_to_json(self, file_path: Path) -> bool:
        """
        Export all settings to JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            True if successful
        """
        try:
            data = {}
            for key in self._settings.allKeys():
                value = self._settings.value(key)
                # Skip non-serializable types like QByteArray
                if isinstance(value, (str, int, float, bool, list, dict)):
                    data[key] = value

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Settings exported to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False

    def import_from_json(self, file_path: Path) -> bool:
        """
        Import settings from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            for key, value in data.items():
                self.set(key, value)

            self.sync()
            logger.info(f"Settings imported from: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False

    # Preference helpers

    def get_recent_files(self, max_count: int = 10) -> list:
        """
        Get list of recent files.

        Args:
            max_count: Maximum number of files to return

        Returns:
            List of recent file paths
        """
        recent = self.get("recent_files", [])
        return recent[:max_count] if isinstance(recent, list) else []

    def add_recent_file(self, file_path: str, max_count: int = 10):
        """
        Add file to recent files list.

        Args:
            file_path: Path to add
            max_count: Maximum number of files to keep
        """
        recent = self.get_recent_files(max_count)

        # Remove if already present
        if file_path in recent:
            recent.remove(file_path)

        # Add to front
        recent.insert(0, file_path)

        # Trim to max_count
        recent = recent[:max_count]

        self.set("recent_files", recent)

    def clear_recent_files(self):
        """Clear recent files list."""
        self.set("recent_files", [])

    # Debug helpers

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings as dictionary.

        Returns:
            Dictionary of all settings
        """
        data = {}
        for key in self._settings.allKeys():
            value = self._settings.value(key)
            if not isinstance(value, QByteArray):
                data[key] = value
        return data

    def print_all_settings(self):
        """Print all settings to console (for debugging)."""
        print("\n" + "=" * 60)
        print(f"Settings: {self.organization}/{self.application}")
        print(f"File: {self._settings.fileName()}")
        print("=" * 60)

        for key in sorted(self._settings.allKeys()):
            value = self._settings.value(key)
            if isinstance(value, QByteArray):
                print(f"  {key}: <QByteArray {len(value)} bytes>")
            else:
                print(f"  {key}: {value}")

        print("=" * 60 + "\n")
