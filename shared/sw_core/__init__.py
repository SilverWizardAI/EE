"""
sw_core - Silver Wizard Core Libraries

Shared infrastructure components for Silver Wizard applications.

This package provides reusable components for:
- Claude instance spawning and management
- Application settings persistence
- Module size monitoring and enforcement

Usage:
    from sw_core import spawn_claude_instance, ModuleMonitor, SettingsManager
"""

from .spawn_claude import (
    spawn_claude_instance,
    check_instance_status,
    stop_instance
)

from .module_monitor import ModuleMonitor, ModuleSizeViolation

# SettingsManager requires PyQt6 - only import if available
try:
    from .settings_manager import SettingsManager
    __all__ = [
        "spawn_claude_instance",
        "check_instance_status",
        "stop_instance",
        "ModuleMonitor",
        "ModuleSizeViolation",
        "SettingsManager"
    ]
except ImportError:
    # PyQt6 not available, skip SettingsManager
    __all__ = [
        "spawn_claude_instance",
        "check_instance_status",
        "stop_instance",
        "ModuleMonitor",
        "ModuleSizeViolation"
    ]

__version__ = "1.0.0"
