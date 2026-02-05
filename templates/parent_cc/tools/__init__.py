"""
Parent CC Management Tools

Tools for creating, launching, and managing applications.
"""

from .registry import AppRegistry
from .create_app import create_app_from_template
from .launch_app import launch_app
from .spawn_claude import spawn_claude_instance

__all__ = [
    "AppRegistry",
    "create_app_from_template",
    "launch_app",
    "spawn_claude_instance",
]
