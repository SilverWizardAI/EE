"""
App Launcher - sw_pcc Library Wrapper

This file imports from the centralized sw_pcc library (launcher.py).
All app launching functionality is maintained in EE/shared/sw_pcc/launcher.py

Installation:
    The sw_pcc library must be available via Python path.
    See EE/shared/sw_pcc/README.md for installation instructions.
"""

# Import everything from the centralized library
from sw_pcc.launcher import *  # noqa: F401,F403

# For backwards compatibility
__all__ = ['launch_app', 'stop_app', 'get_app_status']
