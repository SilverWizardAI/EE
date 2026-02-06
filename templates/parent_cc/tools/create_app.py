"""
Create App from Template - sw_pcc Library Wrapper

This file imports from the centralized sw_pcc library.
All app creation functionality is maintained in EE/shared/sw_pcc/create_app.py

Installation:
    The sw_pcc library must be available via Python path.
    See EE/shared/sw_pcc/README.md for installation instructions.
"""

# Import everything from the centralized library
from sw_pcc.create_app import *  # noqa: F401,F403

# For backwards compatibility
__all__ = ['create_app_from_template', 'TEMPLATES']
