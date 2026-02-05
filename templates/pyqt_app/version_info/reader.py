"""
Runtime version information reader

This module provides functions to read version information at runtime
from the auto-generated _version_data.py module, with fallbacks for
development environments where the module may not exist.
"""

from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path


# Try to import generated version data
try:
    from . import _version_data
    _HAS_VERSION_DATA = True
except ImportError:
    _HAS_VERSION_DATA = False
    _version_data = None


# Development fallback values
_DEV_FALLBACK = {
    'version': '0.0.0-dev',
    'build_number': 0,
    'build_date': 'unknown',
    'build_time': 'unknown',
    'build_timestamp': 'unknown',
}


def _get_version_attr(attr_name: str, fallback: Any = None) -> Any:
    """
    Get attribute from version data module with fallback

    Args:
        attr_name: Attribute name (lowercase, as in version.json)
        fallback: Value to return if attribute not found

    Returns:
        Attribute value or fallback
    """
    if not _HAS_VERSION_DATA:
        return _DEV_FALLBACK.get(attr_name, fallback)

    const_name = attr_name.upper()
    return getattr(_version_data, const_name, fallback)


def get_version() -> str:
    """
    Get application version string

    Returns:
        Version string (e.g., "2.0.0" or "0.0.0-dev" in development)

    Example:
        >>> from version_info import get_version
        >>> version = get_version()
        >>> print(f"App version: {version}")
    """
    return _get_version_attr('version', '0.0.0-dev')


def get_build_number() -> int:
    """
    Get build number

    Returns:
        Build number as integer (0 in development)

    Example:
        >>> build = get_build_number()
        >>> print(f"Build #{build}")
    """
    build = _get_version_attr('build_number', 0)
    try:
        return int(build)
    except (ValueError, TypeError):
        return 0


def get_build_date() -> str:
    """
    Get build date

    Returns:
        Build date string (e.g., "2026-02-04" or "unknown" in development)
    """
    return _get_version_attr('build_date', 'unknown')


def get_build_time() -> str:
    """
    Get build time

    Returns:
        Build time string (e.g., "15:30:00 UTC" or "unknown" in development)
    """
    return _get_version_attr('build_time', 'unknown')


def get_build_timestamp() -> str:
    """
    Get combined build timestamp

    Returns:
        Build timestamp string (e.g., "2026-02-04 15:30:00")
    """
    return _get_version_attr('build_timestamp', 'unknown')


def get_build_timestamp_unix() -> Optional[int]:
    """
    Get build timestamp as Unix epoch

    Returns:
        Unix timestamp as integer, or None if not available
    """
    ts = _get_version_attr('build_timestamp_unix', None)
    if ts is not None:
        try:
            return int(ts)
        except (ValueError, TypeError):
            return None
    return None


def get_build_timestamp_iso() -> Optional[str]:
    """
    Get build timestamp in ISO 8601 format

    Returns:
        ISO timestamp string, or None if not available
    """
    return _get_version_attr('build_timestamp_iso', None)


def is_development_build() -> bool:
    """
    Check if running in development mode (no version data generated)

    Returns:
        True if running without generated version data
    """
    return not _HAS_VERSION_DATA


def get_build_info() -> Dict[str, Any]:
    """
    Get all build information as a dictionary

    Returns:
        Dictionary containing all available build information

    Example:
        >>> info = get_build_info()
        >>> print(f"Version {info['version']}, Build {info['build_number']}")
    """
    if _HAS_VERSION_DATA and hasattr(_version_data, 'VERSION_INFO'):
        return _version_data.VERSION_INFO.copy()

    # Return development fallback
    return _DEV_FALLBACK.copy()


def get_version_dict() -> Dict[str, Any]:
    """
    Get version information as a dictionary (alias for get_build_info)

    Returns:
        Dictionary containing all available build information
    """
    return get_build_info()


def get_custom_field(field_name: str, fallback: Any = None) -> Any:
    """
    Get custom field from version data

    Useful for accessing extra_data fields added during build.

    Args:
        field_name: Name of the field (lowercase)
        fallback: Value to return if field not found

    Returns:
        Field value or fallback

    Example:
        >>> theme = get_custom_field('theme_default', 'Light')
        >>> print(f"Default theme: {theme}")
    """
    return _get_version_attr(field_name, fallback)


def print_version_info():
    """
    Print all version information to console (for debugging)

    Example:
        >>> from version_info.reader import print_version_info
        >>> print_version_info()
    """
    info = get_build_info()

    print("=" * 60)
    print("VERSION INFORMATION")
    print("=" * 60)

    if is_development_build():
        print("⚠ Running in DEVELOPMENT mode (no build data)")
        print()

    for key, value in sorted(info.items()):
        print(f"{key:25} : {value}")

    print("=" * 60)


# Convenience aliases
version = get_version
build_number = get_build_number
build_date = get_build_date
build_time = get_build_time
