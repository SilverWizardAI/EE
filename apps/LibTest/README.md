# LibTest

**Enterprise-grade PyQt6 application framework for Silver Wizard Software**

## Overview

This template provides a production-ready base for all Silver Wizard PyQt6 applications with built-in:

- **Automatic Version Tracking** (via PIW's version_info library)
- **Settings Management** (dark/light themes, persistent preferences)
- **MM Mesh Integration** (inter-app communication via MCP Mesh)
- **Module Size Monitoring** (automatic bloat detection <400 lines/module)
- **Parent CC Protocol** (bidirectional communication with Claude Code)
- **Standard UI** (menus, status bar, dialogs)

## Quick Start

### 1. Create version.json

```bash
cp version.json.template version.json
# Edit version.json to set your app's version
```

### 2. Build Your App

```python
from EE.templates.pyqt_app import BaseApplication, create_application
from PyQt6.QtWidgets import QVBoxLayout, QLabel

class MyApp(BaseApplication):
    def __init__(self):
        # Version auto-detected from version.json via version_info
        super().__init__(app_name="LibTest")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(QLabel("Hello from LibTest!"))

if __name__ == "__main__":
    import sys
    sys.exit(create_application(MyApp, "LibTest"))
```

### 3. Generate Version Data (before running)

```bash
# First time and before each build:
python -m pyqt_app.version_info.generator version.json
```

This auto-increments build number and updates timestamps.

## Features

### Automatic Version Management

Version info is automatically detected from `version.json`:

```json
{
  "version": "1.0.0",
  "build_number": 42
}
```

No need to hardcode versions in your code! The template:
- Auto-detects version from `version_info` library
- Shows version in About dialog with build number and date
- Logs version on startup
- Supports development mode (works without generated build data)

See `version_info/README.md` for full documentation.

### Module Size Monitoring

Built-in monitoring warns when modules exceed size limits:
- **Target:** <400 lines (ideal)
- **Warning:** 600 lines (monitor growth)
- **Critical:** 800 lines (must refactor)

See full documentation in this directory.
