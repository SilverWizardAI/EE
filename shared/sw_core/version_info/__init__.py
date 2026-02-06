"""
Version Info Library - Reusable version management for Python applications

This library provides build-time version generation and runtime version access
for Python applications. It can be dropped into any Python project to manage
version information consistently.

Usage:
    Build-time (in your build script):
        from version_info.generator import generate_version_module
        generate_version_module('path/to/version.json')

    Runtime (in your application):
        from version_info import get_version, get_build_info, format_version

        version = get_version()  # "2.0.0"
        build = get_build_info()  # Full dict with all build data
        display = format_version()  # Formatted string for display
"""

from .reader import (
    get_version,
    get_build_number,
    get_build_date,
    get_build_time,
    get_build_timestamp,
    get_build_info,
    get_version_dict,
)

from .display import (
    format_version,
    format_version_short,
    format_version_long,
    format_version_full,
    format_build_info,
    format_for_about_box,
    format_for_cli_help,
    format_for_log,
    format_for_user_agent,
    get_copyable_version_text,
)

__all__ = [
    # Core getters
    'get_version',
    'get_build_number',
    'get_build_date',
    'get_build_time',
    'get_build_timestamp',
    'get_build_info',
    'get_version_dict',

    # Display formatters
    'format_version',
    'format_version_short',
    'format_version_long',
    'format_version_full',
    'format_build_info',
    'format_for_about_box',
    'format_for_cli_help',
    'format_for_log',
    'format_for_user_agent',
    'get_copyable_version_text',
]

__version__ = get_version()
