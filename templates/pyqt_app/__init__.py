"""
PyQt6 Application Template

Enterprise-grade application framework for Silver Wizard Software.
"""

# Import from sw_core library (installed separately)
from sw_core.base_application import BaseApplication, create_application
from sw_core.settings_manager import SettingsManager
from sw_core.mesh_integration import MeshIntegration
from sw_core.module_monitor import ModuleMonitor, ModuleSizeViolation
from sw_core.parent_cc_protocol import (
    ParentCCProtocol,
    AssistanceRequest,
    AssistanceResponse,
    RequestType,
    RequestPriority
)

# Local template components
from .version_manager import VersionManager

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
