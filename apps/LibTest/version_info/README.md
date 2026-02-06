# Version Info Library

A reusable, self-contained library for managing version information in Python applications.

## Features

- ✅ **Build-time generation**: Automatically captures version, build number, and timestamps during builds
- ✅ **Runtime access**: Clean API to read version info from running applications
- ✅ **Development fallback**: Works in development without a build
- ✅ **Display utilities**: Pre-formatted strings for GUI, CLI, logs, and more
- ✅ **UTC timestamps**: All timestamps in UTC for consistency
- ✅ **Zero dependencies**: Pure Python, no external dependencies
- ✅ **Cross-platform**: Works on any platform Python supports

## Quick Start

### 1. Copy Library to Your Project

```bash
cp -r version_info /path/to/your/project/
```

### 2. Create version.json

```json
{
  "version": "1.0.0",
  "build_number": 1
}
```

### 3. Generate Version Data (in your build script)

```python
from version_info.generator import generate_version_module

# Auto-updates build number and timestamp
generate_version_module('version.json')
```

Or from command line:
```bash
python -m version_info.generator version.json
```

### 4. Use in Your Application

```python
from version_info import get_version, format_version

# Simple usage
version = get_version()  # "1.0.0"
display = format_version()  # "1.0.0 (Build 12345)"

# GUI About box
from version_info import format_for_about_box
about_text = format_for_about_box("My Application")
```

## API Reference

### Core Functions

```python
from version_info import (
    get_version,          # Get version string
    get_build_number,     # Get build number
    get_build_date,       # Get build date
    get_build_time,       # Get build time (UTC)
    get_build_timestamp,  # Get full timestamp
    get_build_info,       # Get all info as dict
)

version = get_version()           # "1.0.0"
build = get_build_number()        # 12345
date = get_build_date()           # "2026-02-04"
time = get_build_time()           # "15:30:00 UTC"
timestamp = get_build_timestamp() # "2026-02-04 15:30:00"
info = get_build_info()           # Full dictionary
```

### Display Formatters

```python
from version_info import (
    format_version,           # Standard format
    format_for_about_box,     # GUI about dialog
    format_for_cli_help,      # CLI --version
    format_for_log,           # Log files
    format_for_user_agent,    # HTTP User-Agent
    get_copyable_version_text # Bug reports
)

# Different styles
format_version('short')    # "1.0.0"
format_version('standard') # "1.0.0 (Build 12345)"
format_version('long')     # "Version 1.0.0, Build 12345, 2026-02-04"
format_version('full')     # Multi-line format

# Context-specific formats
about_text = format_for_about_box("My App")
cli_text = format_for_cli_help("myapp")
log_text = format_for_log()
ua_text = format_for_user_agent("MyApp")
```

## Build Integration Examples

### Python Build Script

```python
#!/usr/bin/env python
"""build.py - Build script with version generation"""

from version_info.generator import generate_version_module

def build():
    # Generate version module (auto-increments build number)
    generate_version_module(
        version_json_path='./version.json',
        extra_data={'theme_default': 'Dark'}  # Optional custom data
    )

    # Rest of your build process...
    # - Compile UI files
    # - Run PyInstaller
    # - Create .app bundle
    # etc.

if __name__ == '__main__':
    build()
```

### Bash Build Script

```bash
#!/bin/bash
# build.sh - Build script with version generation

# Generate version module
python -m version_info.generator version.json

# Rest of build
python setup.py build
# or PyInstaller, py2app, etc.
```

### PyInstaller Integration

```python
# build_with_pyinstaller.py

from version_info.generator import generate_version_module
import PyInstaller.__main__

# Generate version data first
generate_version_module('./version.json')

# Run PyInstaller
PyInstaller.__main__.run([
    'main.py',
    '--name=MyApp',
    '--onefile',
    # version_info will be bundled automatically
])
```

## GUI Integration Examples

### PyQt6 About Dialog

```python
from PyQt6.QtWidgets import QMessageBox
from version_info import format_for_about_box

def show_about_dialog(parent):
    about_text = format_for_about_box("My Application")
    QMessageBox.about(parent, "About", about_text)
```

### PyQt6 Status Bar

```python
from PyQt6.QtWidgets import QMainWindow
from version_info import format_version

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Show version in status bar
        version_text = format_version('standard')
        self.statusBar().showMessage(f"Ready | {version_text}")
```

### Tkinter About Dialog

```python
from tkinter import messagebox
from version_info import format_for_about_box

def show_about():
    about_text = format_for_about_box("My Application")
    messagebox.showinfo("About", about_text)
```

## CLI Integration Examples

### argparse --version

```python
import argparse
from version_info import format_for_cli_help

parser = argparse.ArgumentParser()
parser.add_argument(
    '--version',
    action='version',
    version=format_for_cli_help('myapp')
)
```

### Click --version

```python
import click
from version_info import get_version

@click.command()
@click.version_option(version=get_version())
def main():
    pass
```

## Logging Integration

```python
import logging
from version_info import format_for_log

# Log version on startup
logging.info(f"Application started: {format_for_log()}")
```

## Advanced Usage

### Custom Fields

Add custom data during build:

```python
from version_info.generator import generate_version_module

generate_version_module(
    version_json_path='./version.json',
    extra_data={
        'theme_default': 'Dark',
        'api_endpoint': 'https://api.example.com',
        'build_machine': 'CI-Server-01'
    }
)
```

Access custom fields at runtime:

```python
from version_info.reader import get_custom_field

theme = get_custom_field('theme_default', 'Light')
endpoint = get_custom_field('api_endpoint')
```

### Manual Build Number Control

```python
from version_info.generator import generate_version_module

# Don't auto-increment (use existing build number)
generate_version_module(
    version_json_path='./version.json',
    auto_increment=False
)

# Don't update anything (just generate from existing data)
generate_version_module(
    version_json_path='./version.json',
    update_build=False
)
```

### Development vs Production Detection

```python
from version_info.reader import is_development_build

if is_development_build():
    print("Running in development mode")
    # Enable debug features
else:
    print("Running production build")
    # Use optimized settings
```

## Version.json Format

```json
{
  "version": "1.0.0",
  "build_number": 1,
  "build_date": "2026-02-04",
  "build_time": "15:30:00 UTC",
  "build_timestamp": "2026-02-04 15:30:00",
  "build_timestamp_iso": "2026-02-04T15:30:00+00:00",
  "build_timestamp_unix": 1738683000
}
```

**Required fields:**
- `version`: Semantic version string

**Auto-generated fields:**
- `build_number`: Auto-incremented or timestamp-based
- `build_date`: UTC date (YYYY-MM-DD)
- `build_time`: UTC time (HH:MM:SS UTC)
- `build_timestamp`: Combined date/time
- `build_timestamp_iso`: ISO 8601 format
- `build_timestamp_unix`: Unix epoch timestamp

**Custom fields:**
- Add any additional fields you need - they'll be accessible via `get_custom_field()`

## How It Works

### Build Time

1. `generator.py` reads `version.json`
2. Updates build number (increments by 1 or uses timestamp)
3. Updates all timestamps (UTC)
4. Generates `_version_data.py` with all constants
5. Saves updated `version.json`

### Runtime

1. `reader.py` imports `_version_data.py`
2. Provides clean API to access version constants
3. Falls back to development defaults if `_version_data.py` doesn't exist
4. `display.py` formats version info for various contexts

## File Structure

```
version_info/
├── __init__.py          # Public API exports
├── generator.py         # Build-time generation
├── reader.py            # Runtime reading
├── display.py           # Display formatters
├── _version_data.py     # Auto-generated (gitignored)
└── README.md            # This file
```

## .gitignore

Add this to your `.gitignore`:

```
version_info/_version_data.py
```

The `_version_data.py` file is auto-generated during builds and should not be committed.

## License

This library is provided as-is for use in any project.
