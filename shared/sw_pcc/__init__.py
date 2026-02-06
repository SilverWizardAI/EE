"""
sw_pcc - Silver Wizard Parent CC Control

PCC (Parent CC) tools for managing child applications.

This package provides:
- App registry management
- App creation from templates
- App launching and lifecycle management

Usage:
    from sw_pcc import AppRegistry, create_app_from_template, launch_app
"""

from .registry import AppRegistry
from .create_app import create_app_from_template, TEMPLATES
from .launcher import launch_app, stop_app

__all__ = [
    "AppRegistry",
    "create_app_from_template",
    "TEMPLATES",
    "launch_app",
    "stop_app"
]

__version__ = "1.0.0"
