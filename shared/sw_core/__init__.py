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

from .terminal_manager import TerminalManager, get_terminal_manager

from .base_application import BaseApplication, create_application

# Import parent_cc_protocol components
from .parent_cc_protocol import (
    ParentCCProtocol,
    RequestType,
    RequestPriority,
    ControlCommand
)

# PyQt6-dependent imports - only if available
try:
    from .settings_manager import SettingsManager
    from .mesh_integration import MeshIntegration
    __all__ = [
        "spawn_claude_instance",
        "check_instance_status",
        "stop_instance",
        "ModuleMonitor",
        "ModuleSizeViolation",
        "TerminalManager",
        "get_terminal_manager",
        "SettingsManager",
        "MeshIntegration",
        "BaseApplication",
        "create_application",
        "ParentCCProtocol",
        "RequestType",
        "RequestPriority",
        "ControlCommand"
    ]
except ImportError:
    # PyQt6 not available, skip PyQt6-dependent modules
    __all__ = [
        "spawn_claude_instance",
        "check_instance_status",
        "stop_instance",
        "ModuleMonitor",
        "ModuleSizeViolation",
        "TerminalManager",
        "get_terminal_manager",
        "BaseApplication",
        "create_application",
        "ParentCCProtocol",
        "RequestType",
        "RequestPriority",
        "ControlCommand"
    ]

__version__ = "1.0.0"
