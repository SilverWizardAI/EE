"""
Parent CC Management Tools - Library Wrappers

All tools import from centralized sw_pcc and sw_core libraries:
- sw_pcc: App registry, creation, and launcher (PCC-specific tools)
- sw_core: Claude spawning and other core utilities

Installation:
    Ensure sw_core and sw_pcc are available on Python path:

    ```bash
    # Manual .pth file approach
    echo "/path/to/EE/shared" > /opt/homebrew/lib/python3.13/site-packages/_sw_manual.pth
    ```

    Or use pip install -e:
    ```bash
    cd /path/to/EE/shared/sw_core && pip install -e .
    cd /path/to/EE/shared/sw_pcc && pip install -e .
    ```

Architecture:
    These local files are lightweight wrappers that import from the libraries.
    All functionality is maintained in EE/shared/sw_pcc and EE/shared/sw_core.
    This ensures single source of truth and eliminates code duplication.
"""

# Re-export from libraries (via local wrappers)
from .registry import AppRegistry
from .create_app import create_app_from_template, TEMPLATES
from .launch_app import launch_app, stop_app, get_app_status
from .spawn_claude import spawn_claude_instance

__all__ = [
    'AppRegistry',
    'create_app_from_template',
    'TEMPLATES',
    'launch_app',
    'stop_app',
    'get_app_status',
    'spawn_claude_instance',
]
