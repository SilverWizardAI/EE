"""
Version Manager

Tracks application version, build information, and update checks.
Integrates with PIW's version_info library for automatic build tracking.

Module Size Target: <400 lines (Current: ~180 lines)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Try to import version_info library for automatic build tracking
try:
    from .version_info import (
        get_version,
        get_build_number,
        get_build_info,
        format_for_about_box,
        is_development_build
    )
    _HAS_VERSION_INFO = True
except ImportError:
    _HAS_VERSION_INFO = False


logger = logging.getLogger(__name__)


class VersionManager:
    """
    Manages application version and build information.

    Features:
    - Automatic version detection from version_info library
    - Semantic versioning (MAJOR.MINOR.PATCH)
    - Build metadata (date, build number, etc.)
    - Version comparison
    - Update checking support

    Usage:
        # With version_info library (recommended):
        version = VersionManager("MyApp")  # Auto-detects version

        # Manual version (fallback):
        version = VersionManager("MyApp", manual_version="1.2.3")
    """

    def __init__(
        self,
        app_name: str,
        manual_version: Optional[str] = None,
        build_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize version manager.

        Args:
            app_name: Application name
            manual_version: Manual version override (optional, uses version_info if available)
            build_metadata: Optional build metadata dict (deprecated, use version_info)
        """
        self.app_name = app_name
        self.build_metadata = build_metadata or {}

        # Use version_info library if available, otherwise use manual version
        if _HAS_VERSION_INFO:
            self.version = get_version()
            self.using_version_info = True
            logger.info(f"Version manager initialized with version_info: {app_name} v{self.version}")
        else:
            self.version = manual_version or "0.0.0-dev"
            self.using_version_info = False
            logger.warning(
                f"Version manager initialized without version_info: {app_name} v{self.version}. "
                f"Run 'python -m version_info.generator' to generate build data."
            )

        # Parse semantic version
        self.major, self.minor, self.patch = self._parse_version(self.version)

        # Auto-populate build metadata (only if not using version_info)
        if not self.using_version_info and "build_date" not in self.build_metadata:
            self.build_metadata["build_date"] = datetime.now().isoformat()

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
            Dictionary with build metadata (from version_info if available)
        """
        if self.using_version_info and _HAS_VERSION_INFO:
            # Use real build data from version_info
            info = get_build_info()
            return {
                "version": info.get("version", self.version),
                "build_number": info.get("build_number", 0),
                "build_date": info.get("build_date", "unknown"),
                "build_time": info.get("build_time", "unknown"),
                "build_timestamp": info.get("build_timestamp", "unknown"),
                "is_development": is_development_build(),
            }
        else:
            # Fallback to manual metadata
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

    def get_about_text(self, include_copyright: bool = True, organization: str = "") -> str:
        """
        Get formatted text for About dialog.

        Args:
            include_copyright: Include copyright notice
            organization: Organization name for copyright

        Returns:
            HTML-formatted about text
        """
        if self.using_version_info and _HAS_VERSION_INFO:
            # Use version_info formatter for professional output
            about_text = format_for_about_box(self.app_name)

            # Add copyright if requested
            if include_copyright and organization:
                about_text += f"\n\n© {datetime.now().year} {organization}"

            return about_text
        else:
            # Fallback format
            build_info = self.get_build_info()
            text = f"{self.app_name}\n\nVersion {self.version}"

            if build_info.get("build_date"):
                text += f"\nBuild: {build_info['build_date']}"

            if include_copyright and organization:
                text += f"\n\n© {datetime.now().year} {organization}"

            return text
