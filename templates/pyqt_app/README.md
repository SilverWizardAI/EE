# PyQt6 Application Template

**Enterprise-grade PyQt6 application framework for Silver Wizard Software**

## Overview

This template provides a production-ready base for all Silver Wizard PyQt6 applications with built-in:

- Settings Management (dark/light themes, persistent preferences)
- Version Tracking (semantic versioning, build metadata)
- MM Mesh Integration (inter-app communication)
- Module Size Monitoring (automatic bloat detection)
- PQTI Support (test harness integration)
- Standard UI (menus, status bar, dialogs)

## Quick Start

```python
from EE.templates.pyqt_app.base_application import BaseApplication, create_application
from PyQt6.QtWidgets import QVBoxLayout, QLabel

class MyApp(BaseApplication):
    def __init__(self):
        super().__init__(app_name="My App", app_version="1.0.0")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(QLabel("Hello from My App!"))

if __name__ == "__main__":
    import sys
    sys.exit(create_application(MyApp, "My App", "1.0.0"))
```

See full documentation in this directory.
