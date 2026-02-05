"""
Version Manager

Tracks application version, build information, and update checks.

Module Size Target: <400 lines (Current: ~150 lines)
"""

import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class VersionManager:
    """
    Manages application version and build information.

    Features:
    - Semantic versioning (MAJOR.MINOR.PATCH)
    - Build metadata (date, commit hash, etc.)
    - Version comparison
    - Update checking support

    Usage:
        version = VersionManager("MyApp", "1.2.3")
        info = version.get_version_info()
        build = version.get_build_info()
    """

    def __init__(self, app_name: str, version: str, build_metadata: Dict[str, Any] = None):
        """
        Initialize version manager.

        Args:
            app_name: Application name
            version: Semantic version string (e.g., "1.2.3")
            build_metadata: Optional build metadata dict
        """
        self.app_name = app_name
        self.version = version
        self.build_metadata = build_metadata or {}

        # Parse semantic version
        self.major, self.minor, self.patch = self._parse_version(version)

        # Auto-populate build metadata
        if "build_date" not in self.build_metadata:
            self.build_metadata["build_date"] = datetime.now().isoformat()

        logger.info(f"Version manager initialized: {app_name} v{version}")

    def _parse_version(self, version: str) -> tuple:
        """
        Parse semantic version string.

        Args:
            version: Version string (e.g., "1.2.3")

        Returns:
            Tuple of (major, minor, patch)
        """
        try:
            parts = version.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid version format '{version}': {e}")
            return (0, 0, 0)

    def get_version_info(self) -> Dict[str, Any]:
        """
        Get version information.

        Returns:
            Dictionary with version details
        """
        return {
            "app_name": self.app_name,
            "version": self.version,
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
        }

    def get_build_info(self) -> Dict[str, Any]:
        """
        Get build information.

        Returns:
            Dictionary with build metadata
        """
        return {
            "version": self.version,
            "build_date": self.build_metadata.get("build_date"),
            "commit_hash": self.build_metadata.get("commit_hash", "unknown"),
            "branch": self.build_metadata.get("branch", "unknown"),
        }

    def get_full_version_string(self) -> str:
        """
        Get full version string with metadata.

        Returns:
            Full version string (e.g., "1.2.3+build.20260205")
        """
        base = self.version
        metadata_parts = []

        if "commit_hash" in self.build_metadata:
            commit = self.build_metadata["commit_hash"][:8]
            metadata_parts.append(f"commit.{commit}")

        if metadata_parts:
            return f"{base}+{'.'.join(metadata_parts)}"

        return base

    def is_newer_than(self, other_version: str) -> bool:
        """
        Check if this version is newer than another.

        Args:
            other_version: Version string to compare

        Returns:
            True if this version is newer
        """
        other_major, other_minor, other_patch = self._parse_version(other_version)

        if self.major > other_major:
            return True
        if self.major < other_major:
            return False

        if self.minor > other_minor:
            return True
        if self.minor < other_minor:
            return False

        return self.patch > other_patch

    def is_compatible_with(self, required_version: str) -> bool:
        """
        Check if this version is compatible with required version.
        Compatible means same major version and >= minor.patch.

        Args:
            required_version: Required version string

        Returns:
            True if compatible
        """
        req_major, req_minor, req_patch = self._parse_version(required_version)

        # Different major version = incompatible
        if self.major != req_major:
            return False

        # Same major, check minor.patch
        if self.minor > req_minor:
            return True
        if self.minor == req_minor and self.patch >= req_patch:
            return True

        return False

    def get_version_display(self) -> str:
        """
        Get user-friendly version display string.

        Returns:
            Display string (e.g., "MyApp v1.2.3")
        """
        return f"{self.app_name} v{self.version}"
