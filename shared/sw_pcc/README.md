# sw_pcc - Silver Wizard Parent CC Control

**PCC (Parent CC) management tools for creating, launching, and monitoring child applications.**

Part of the Silver Wizard Software infrastructure suite.

---

## Features

### App Registry Management
Track and manage all applications under Parent CC control:
- App metadata (name, template, creation date)
- Runtime status (running, stopped, healthy)
- Health check history
- Process tracking

### App Creation from Templates
Create new applications from Silver Wizard templates:
- PyQt6 application template with MM mesh integration
- Counter and logger app variants
- Automatic version management
- Registry auto-registration

### App Lifecycle Management
Launch and control managed applications:
- Python process management
- Headless mode support
- Log file management
- Graceful shutdown

---

## Installation

```bash
# Install in development mode
pip install -e shared/sw_pcc

# Or with UV (faster)
uv pip install -e shared/sw_pcc
```

**Note:** sw_pcc depends on sw_core, so install sw_core first:
```bash
pip install -e shared/sw_core
pip install -e shared/sw_pcc
```

---

## Usage

### Registry Management

```python
from sw_pcc import AppRegistry

# Load registry
registry = AppRegistry("app_registry.json")

# Add new app
registry.add_app(
    name="MyApp",
    template="pyqt_app",
    folder="apps/MyApp",
    mesh_service="myapp"
)

# Update app status
registry.set_status("MyApp", "running")

# Get running apps
running = registry.get_running_apps()
```

### Create App from Template

```python
from sw_pcc import create_app_from_template
from pathlib import Path

app_folder = create_app_from_template(
    app_name="TestApp1",
    template_type="pyqt_app",
    pcc_folder=Path("/path/to/PCC"),
    features=["counter"],
    registry_path=Path("/path/to/app_registry.json")
)
```

### Launch and Stop Apps

```python
from sw_pcc import launch_app, stop_app
from pathlib import Path

# Launch app
result = launch_app(
    app_name="TestApp1",
    pcc_folder=Path("/path/to/PCC"),
    registry_path=Path("/path/to/app_registry.json"),
    headless=False
)

print(f"Launched: PID {result['pid']}, Log: {result['log_file']}")

# Stop app
stop_app(
    app_name="TestApp1",
    registry_path=Path("/path/to/app_registry.json"),
    reason="Manual stop"
)
```

---

## Command-Line Tools

After installation, these commands are available:

### sw-registry
```bash
# List all apps
sw-registry --list

# Show statistics
sw-registry --stats

# Check app health
sw-registry --check-health MyApp
```

### sw-create-app
```bash
# Create new app
sw-create-app \
  --name TestApp1 \
  --template pyqt_app \
  --pcc-folder /path/to/PCC \
  --features counter parent_cc_client
```

### sw-launcher
```bash
# Launch app
sw-launcher \
  --app TestApp1 \
  --pcc-folder /path/to/PCC \
  --action launch

# Launch in headless mode
sw-launcher \
  --app TestApp1 \
  --pcc-folder /path/to/PCC \
  --action launch \
  --headless

# Stop app
sw-launcher \
  --app TestApp1 \
  --pcc-folder /path/to/PCC \
  --action stop
```

---

## Dependencies

- **sw_core**: Core infrastructure (mesh, spawning, base application)
- **Python 3.11+**: Modern Python features
- **pathlib**: File path handling
- **subprocess**: Process management

---

## Architecture

```
sw_pcc/
├── __init__.py          # Package exports
├── registry.py          # AppRegistry class (325 lines)
├── create_app.py        # Template-based app creation (545 lines)
├── launcher.py          # App launch/stop management (308 lines)
├── pyproject.toml       # Package configuration
└── README.md            # This file
```

### Module Sizes
All modules follow Silver Wizard standards:
- ✅ registry.py: 325 lines (<400 target)
- ⚠️ create_app.py: 545 lines (acceptable 400-600 range, monitor growth)
- ✅ launcher.py: 308 lines (<400 target)

---

## Version

Current version: **1.0.0**

Part of the Silver Wizard Enterprise Edition (EE) infrastructure suite.

---

## See Also

- **sw_core**: Core infrastructure library
- **EE/templates/pyqt_app**: PyQt6 application template
- **MM**: MCP Mesh (central proxy for inter-app communication)

---

**Silver Wizard Software** - Enterprise Architect Infrastructure
