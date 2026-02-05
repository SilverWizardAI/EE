"""
PyQt6 Application Template

Enterprise-grade application framework for Silver Wizard Software.
"""

from .base_application import BaseApplication, create_application
from .settings_manager import SettingsManager
from .version_manager import VersionManager
from .mesh_integration import MeshIntegration
from .module_monitor import ModuleMonitor, ModuleSizeViolation
from .parent_cc_protocol import (
    ParentCCProtocol,
    AssistanceRequest,
    AssistanceResponse,
    RequestType,
    RequestPriority
)

__version__ = "1.0.0"

__all__ = [
    "BaseApplication",
    "create_application",
    "SettingsManager",
    "VersionManager",
    "MeshIntegration",
    "ModuleMonitor",
    "ModuleSizeViolation",
    "ParentCCProtocol",
    "AssistanceRequest",
    "AssistanceResponse",
    "RequestType",
    "RequestPriority",
]
