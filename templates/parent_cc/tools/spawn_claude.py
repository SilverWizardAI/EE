"""
Spawn Claude Instance - sw_core Library Wrapper

This file imports from the centralized sw_core library.
All Claude spawning functionality is maintained in EE/shared/sw_core/spawn_claude.py

Installation:
    The sw_core library must be available via Python path.
    See EE/shared/sw_core/README.md for installation instructions.
"""

# Import everything from the centralized library
from sw_core.spawn_claude import *  # noqa: F401,F403

# For backwards compatibility
__all__ = ['spawn_claude_instance']
