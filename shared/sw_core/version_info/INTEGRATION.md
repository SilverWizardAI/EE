# Integration Guide: Adding version_info to Your Applications

This guide shows how to integrate the `version_info` library into any Python application.

## Table of Contents

1. [Quick Integration for PIW](#quick-integration-for-piw)
2. [General Integration for Any App](#general-integration-for-any-app)
3. [Build Script Updates](#build-script-updates)
4. [GUI Integration Patterns](#gui-integration-patterns)
5. [Deployment Checklist](#deployment-checklist)

---

## Quick Integration for PIW

### Step 1: Update build_piw.sh

Add version generation before bundling:

```bash
# In build_piw.sh, add before calling bundle.py:

echo "Generating version information..."
uv run python -m version_info.generator version.json

# Continue with existing build...
uv run python bundle.py
```

### Step 2: Use in bundler_ui.py

Add version display to your GUI:

```python
# At the top of bundler_ui.py
from version_info import format_version, format_for_about_box

class BundlerUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title with version
        version = format_version('short')
        self.setWindowTitle(f"Python Install Wizard {version}")

        # Add version to status bar
        status_version = format_version('standard')
        self.statusBar().showMessage(f"Ready | {status_version}")

    def show_about_dialog(self):
        """Show about dialog with version info"""
        about_text = format_for_about_box("Python Install Wizard")
        QMessageBox.about(self, "About PIW", about_text)
```

### Step 3: Include in Bundle

The library will be automatically included when PyInstaller/bundler scans imports.
No special configuration needed!

---

## General Integration for Any App

### Step 1: Copy Library to Project

```bash
# Copy the entire version_info directory
cp -r /path/to/version_info /your/project/

# Or create as a subdirectory
mkdir -p /your/project/libs/
cp -r /path/to/version_info /your/project/libs/
```

### Step 2: Create version.json

```bash
cd /your/project

cat > version.json << 'EOF'
{
  "version": "1.0.0",
  "build_number": 1
}
EOF
```

### Step 3: Update .gitignore

```bash
echo "version_info/_version_data.py" >> .gitignore
echo "build_info.py" >> .gitignore  # If using old system
```

### Step 4: Integrate into Build

Choose your build system:

#### Option A: Python Build Script

```python
#!/usr/bin/env python
"""build.py"""

from version_info.generator import generate_version_module
import subprocess

def main():
    # Generate version data
    print("Generating version information...")
    generate_version_module('./version.json')

    # Your build commands
    print("Building application...")
    subprocess.run(['pyinstaller', 'main.py'])
    # or: subprocess.run(['python', 'setup.py', 'build'])
    # or: subprocess.run(['uv', 'run', 'python', 'bundle.py'])

if __name__ == '__main__':
    main()
```

#### Option B: Bash Build Script

```bash
#!/bin/bash
set -e

echo "Generating version information..."
uv run python -m version_info.generator version.json

echo "Building application..."
pyinstaller main.py
# or: python setup.py build
# or: uv run python bundle.py
```

#### Option C: Makefile

```makefile
.PHONY: build version

version:
	@echo "Generating version information..."
	@uv run python -m version_info.generator version.json

build: version
	@echo "Building application..."
	@pyinstaller main.py
```

### Step 5: Use in Your Application

```python
# main.py or your entry point

from version_info import get_version, format_for_log
import logging

# Log version on startup
logging.info(f"Starting application: {format_for_log()}")

# Use in GUI, CLI, etc.
def main():
    version = get_version()
    print(f"My App v{version}")
    # ...
```

---

## Build Script Updates

### PIW: build_piw.sh Enhancement

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=================================="
echo "Building Python Install Wizard"
echo "=================================="

# 1. Generate version information
echo ""
echo "Step 1: Generating version information..."
uv run python -m version_info.generator version.json

# 2. Build the application
echo ""
echo "Step 2: Building application bundle..."
uv run python bundle.py

# 3. Create installer
echo ""
echo "Step 3: Creating installer..."
./create_installer.sh

echo ""
echo "✓ Build complete!"
uv run python -c "from version_info import format_version; print(f'  Version: {format_version()}')"
```

### PIW: build_piw_v2.py Integration

```python
# In build_piw_v2.py, add at the beginning of build process:

from version_info.generator import generate_version_module

def build_piw():
    """Build PIW with version tracking"""

    # Generate version data
    print("Generating version information...")
    generate_version_module(
        version_json_path='version.json',
        extra_data={
            'theme_default': 'Dark',  # From your config
        }
    )

    # Continue with existing build...
    # (rest of your build_piw_v2 code)
```

---

## GUI Integration Patterns

### PyQt6: Main Window

```python
from PyQt6.QtWidgets import QMainWindow, QLabel, QStatusBar
from PyQt6.QtCore import Qt
from version_info import get_version, format_version

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window title with version
        version = get_version()
        self.setWindowTitle(f"My App {version}")

        # Version label in UI
        version_label = QLabel(format_version('standard'))
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Status bar with version
        self.statusBar().showMessage(f"Ready | {format_version()}")

    def setup_menu(self):
        """Setup menu with About action"""
        from version_info import format_for_about_box

        help_menu = self.menuBar().addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(lambda: QMessageBox.about(
            self,
            "About",
            format_for_about_box("My Application")
        ))
```

### PyQt6: Splash Screen

```python
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt
from version_info import format_version

class SplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap)

        # Show version on splash
        version_text = format_version('standard')
        self.showMessage(
            f"Loading {version_text}...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.white
        )
```

### Tkinter: Main Window

```python
import tkinter as tk
from tkinter import messagebox
from version_info import get_version, format_for_about_box

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window title with version
        version = get_version()
        self.title(f"My App {version}")

        # Menu with About
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def show_about(self):
        about_text = format_for_about_box("My Application")
        messagebox.showinfo("About", about_text)
```

---

## Deployment Checklist

### Pre-Build

- [ ] `version.json` exists in project root
- [ ] Version number updated (if manual versioning)
- [ ] `version_info/_version_data.py` in `.gitignore`
- [ ] Build script calls `generate_version_module()`

### Build Integration

- [ ] Version generation runs BEFORE bundling/packaging
- [ ] Build script auto-increments build number
- [ ] Timestamps use UTC
- [ ] Custom fields added if needed
- [ ] Generated `_version_data.py` included in bundle

### Runtime Testing

- [ ] Version displayed in GUI (window title, about box, etc.)
- [ ] Version logged on startup
- [ ] `get_version()` returns correct version
- [ ] `get_build_number()` returns correct build number
- [ ] Timestamps are in UTC

### Distribution

- [ ] Final bundle includes `version_info/` directory
- [ ] `_version_data.py` generated and bundled
- [ ] Version visible to end users
- [ ] About dialog shows correct information

---

## Advanced: Custom Build Numbers

### Option 1: Auto-Increment (Default)

```python
# Increments build_number by 1 each build
generate_version_module('version.json', auto_increment=True)
```

### Option 2: Timestamp-Based (PIW Style)

```python
from version_info.generator import VersionGenerator
from datetime import datetime, timezone

generator = VersionGenerator('version.json')

# Custom build number logic
now = datetime.now(timezone.utc)
build_number = int(now.timestamp()) - 1700000000  # PIW style

generator.version_data['build_number'] = build_number
generator.generate_version_module(update_build=True, auto_increment=False)
```

### Option 3: Git-Based

```bash
# Use git commit count as build number
BUILD_NUMBER=$(git rev-list --count HEAD)

uv run python -c "
import json
with open('version.json', 'r+') as f:
    data = json.load(f)
    data['build_number'] = $BUILD_NUMBER
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
"

uv run python -m version_info.generator version.json --no-increment
```

---

## Troubleshooting

### Module Not Found

```python
# If you get ModuleNotFoundError: No module named 'version_info'

# Solution 1: Ensure version_info/ is in same directory as your main script
# Solution 2: Add to Python path:
import sys
sys.path.insert(0, '/path/to/directory/containing/version_info')
```

### Version Shows "0.0.0-dev"

This means `_version_data.py` hasn't been generated yet.

```bash
# Generate it:
uv run python -m version_info.generator version.json
```

### Build Number Not Incrementing

```python
# Check your generator call:
generate_version_module(
    'version.json',
    auto_increment=True  # Must be True
)
```

### Timestamps Wrong Timezone

All timestamps are UTC by design. The generator uses:
```python
datetime.now(timezone.utc)
```

If you see local time, check that you're using the generated `_version_data.py`,
not manually set values.

---

## Migration from Existing System

### From build_info.py

If you have an existing `build_info.py`:

```bash
# 1. Backup
cp build_info.py build_info.py.backup

# 2. Create version.json from build_info.py
uv run python -c "
import build_info
import json

data = {
    'version': build_info.VERSION,
    'build_number': build_info.BUILD_NUMBER
}

with open('version.json', 'w') as f:
    json.dump(data, f, indent=2)
"

# 3. Generate new system
uv run python -m version_info.generator version.json

# 4. Update imports in code
# Change: from build_info import VERSION
# To:     from version_info import get_version
```

### From pyproject.toml Only

```bash
# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

# Create version.json
cat > version.json << EOF
{
  "version": "$VERSION",
  "build_number": 1
}
EOF

# Generate version data
uv run python -m version_info.generator version.json
```

---

## Complete Example: New Project Setup

```bash
# 1. Copy library
cp -r /path/to/version_info ./

# 2. Create version.json
cat > version.json << 'EOF'
{
  "version": "1.0.0",
  "build_number": 1
}
EOF

# 3. Update .gitignore
echo "version_info/_version_data.py" >> .gitignore

# 4. Create build script
cat > build.sh << 'EOF'
#!/bin/bash
set -e
uv run python -m version_info.generator version.json
pyinstaller main.py
EOF
chmod +x build.sh

# 5. Update main.py
cat >> main.py << 'EOF'

from version_info import get_version, format_for_log
import logging

logging.basicConfig(level=logging.INFO)
logging.info(f"Starting: {format_for_log()}")

def main():
    print(f"My App v{get_version()}")
    # Your code here

if __name__ == '__main__':
    main()
EOF

# 6. Test
./build.sh
```

Done! Your application now has comprehensive version tracking.
