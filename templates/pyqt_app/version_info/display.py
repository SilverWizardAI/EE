"""
Version information display formatters

This module provides pre-formatted strings for displaying version information
in various contexts (GUI about boxes, CLI help text, logs, etc.)
"""

from typing import Optional, Dict, Any
from .reader import (
    get_version,
    get_build_number,
    get_build_date,
    get_build_time,
    get_build_timestamp,
    is_development_build,
    get_build_info,
)


def format_version(style: str = 'standard') -> str:
    """
    Format version string for display

    Args:
        style: Format style - 'standard', 'short', 'long', 'full'

    Returns:
        Formatted version string

    Styles:
        - 'standard': "2.0.0 (Build 70142242)"
        - 'short': "2.0.0"
        - 'long': "Version 2.0.0, Build 70142242, 2026-02-04"
        - 'full': Full multi-line format with all details

    Example:
        >>> from version_info import format_version
        >>> print(format_version('standard'))
        2.0.0 (Build 70142242)
    """
    if style == 'short':
        return format_version_short()
    elif style == 'long':
        return format_version_long()
    elif style == 'full':
        return format_version_full()
    else:  # 'standard'
        return format_version_standard()


def format_version_short() -> str:
    """
    Format short version string (version only)

    Returns:
        Version string (e.g., "2.0.0")
    """
    version = get_version()
    if is_development_build():
        return f"{version}"
    return version


def format_version_standard() -> str:
    """
    Format standard version string (version + build number)

    Returns:
        Standard format string (e.g., "2.0.0 (Build 70142242)")
    """
    version = get_version()
    build = get_build_number()

    if is_development_build():
        return f"{version} (Development)"

    return f"{version} (Build {build})"


def format_version_long() -> str:
    """
    Format long version string (version + build + date)

    Returns:
        Long format string (e.g., "Version 2.0.0, Build 70142242, 2026-02-04")
    """
    version = get_version()
    build = get_build_number()
    date = get_build_date()

    if is_development_build():
        return f"Version {version} (Development Build)"

    return f"Version {version}, Build {build}, {date}"


def format_version_full() -> str:
    """
    Format full version information (multi-line)

    Returns:
        Multi-line formatted string with all version details
    """
    version = get_version()
    build = get_build_number()
    date = get_build_date()
    time = get_build_time()

    if is_development_build():
        return f"""Version: {version}
Build: Development
Status: Running in development mode"""

    return f"""Version: {version}
Build: {build}
Date: {date}
Time: {time}"""


def format_build_info(include_labels: bool = True) -> str:
    """
    Format all build information as key-value pairs

    Args:
        include_labels: If True, includes field labels

    Returns:
        Formatted build information

    Example:
        >>> print(format_build_info())
        Version: 2.0.0
        Build Number: 70142242
        Build Date: 2026-02-04
        Build Time: 15:30:00 UTC
    """
    info = get_build_info()

    if not include_labels:
        return '\n'.join(str(v) for v in info.values())

    lines = []
    label_map = {
        'version': 'Version',
        'build_number': 'Build Number',
        'build_date': 'Build Date',
        'build_time': 'Build Time',
        'build_timestamp': 'Build Timestamp',
    }

    for key, value in info.items():
        label = label_map.get(key, key.replace('_', ' ').title())
        lines.append(f"{label}: {value}")

    return '\n'.join(lines)


def format_for_about_box(app_name: Optional[str] = None) -> str:
    """
    Format version info for GUI about box

    Args:
        app_name: Application name (optional)

    Returns:
        Formatted string suitable for about dialog

    Example:
        >>> from version_info import format_for_about_box
        >>> about_text = format_for_about_box("My App")
        >>> # Use in PyQt6:
        >>> QMessageBox.about(parent, "About", about_text)
    """
    version = get_version()
    build = get_build_number()
    date = get_build_date()

    lines = []

    if app_name:
        lines.append(app_name)
        lines.append("")

    lines.append(f"Version {version}")

    if not is_development_build():
        lines.append(f"Build {build}")
        lines.append(f"Released {date}")
    else:
        lines.append("Development Build")

    return '\n'.join(lines)


def format_for_cli_help(app_name: Optional[str] = None) -> str:
    """
    Format version info for CLI --version output

    Args:
        app_name: Application name (optional)

    Returns:
        Formatted string suitable for CLI

    Example:
        >>> from version_info import format_for_cli_help
        >>> print(format_for_cli_help("myapp"))
        myapp 2.0.0 (Build 70142242, 2026-02-04)
    """
    version = get_version()
    build = get_build_number()
    date = get_build_date()

    if is_development_build():
        suffix = "(development)"
    else:
        suffix = f"(Build {build}, {date})"

    if app_name:
        return f"{app_name} {version} {suffix}"

    return f"{version} {suffix}"


def format_for_log() -> str:
    """
    Format version info for log files

    Returns:
        Formatted string suitable for logging

    Example:
        >>> import logging
        >>> from version_info import format_for_log
        >>> logging.info(f"Application started: {format_for_log()}")
    """
    version = get_version()
    build = get_build_number()
    timestamp = get_build_timestamp()

    if is_development_build():
        return f"v{version} [dev]"

    return f"v{version} build#{build} ({timestamp})"


def format_for_user_agent(app_name: str) -> str:
    """
    Format version info for HTTP User-Agent header

    Args:
        app_name: Application name

    Returns:
        User-Agent string

    Example:
        >>> from version_info import format_for_user_agent
        >>> headers = {
        ...     'User-Agent': format_for_user_agent('MyApp')
        ... }
        >>> # Results in: "MyApp/2.0.0 (Build 70142242)"
    """
    version = get_version()
    build = get_build_number()

    # Remove any spaces from app name for User-Agent
    app_name = app_name.replace(' ', '')

    if is_development_build():
        return f"{app_name}/{version}-dev"

    return f"{app_name}/{version} (Build {build})"


def get_copyable_version_text() -> str:
    """
    Get version text suitable for copy-paste (support requests, bug reports)

    Returns:
        Formatted text with all relevant details

    Example:
        >>> from version_info import get_copyable_version_text
        >>> # Display in GUI with copy button, or print to console
        >>> print(get_copyable_version_text())
    """
    import platform

    version = get_version()
    build = get_build_number()
    timestamp = get_build_timestamp()

    lines = [
        f"Version: {version}",
        f"Build: {build}",
        f"Built: {timestamp}",
        f"Platform: {platform.system()} {platform.release()}",
        f"Python: {platform.python_version()}",
    ]

    if is_development_build():
        lines.insert(1, "Type: Development Build")

    return '\n'.join(lines)


# Convenience aliases for common use cases
about_box = format_for_about_box
cli_version = format_for_cli_help
log_version = format_for_log
user_agent = format_for_user_agent
