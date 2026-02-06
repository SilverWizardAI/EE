# sw_core - Silver Wizard Core Libraries

Shared infrastructure components for Silver Wizard applications.

## Features

### 🚀 Claude Instance Spawning
Spawn and manage Claude Code instances for applications:

```python
from sw_core import spawn_claude_instance

result = spawn_claude_instance(
    app_folder=Path("/path/to/app"),
    app_name="MyApp",
    initial_prompt="Run the application",
    background=True
)
print(f"Spawned instance: {result['instance_id']}")
```

### 📊 Module Size Monitoring
Track Python module sizes and enforce code quality standards:

```python
from sw_core import ModuleMonitor

monitor = ModuleMonitor(
    project_root=Path.cwd(),
    warning_threshold=600,
    critical_threshold=800
)

violations = monitor.check_all_modules()
if violations:
    print(monitor.generate_report())
```

### ⚙️ Settings Management (PyQt6)
Persistent settings with Qt integration:

```python
from sw_core import SettingsManager

settings = SettingsManager("SilverWizard", "MyApp")
settings.set("theme", "dark")
theme = settings.get("theme", default="light")

# Window geometry
settings.save_window_geometry(window)
settings.restore_window_geometry(window)
```

## Installation

### From Local Path (Development)

```bash
# Install core library
uv pip install -e /path/to/EE/shared/sw_core

# Install with PyQt6 support
uv pip install -e "/path/to/EE/shared/sw_core[pyqt]"
```

### In pyproject.toml

```toml
[project.dependencies]
sw-core = {path = "../EE/shared/sw_core", develop = true}

# Or with PyQt support
sw-core = {path = "../EE/shared/sw_core", develop = true, extras = ["pyqt"]}
```

## Components

### spawn_claude.py
- `spawn_claude_instance()` - Spawn Claude instance
- `check_instance_status()` - Check if instance is running
- `stop_instance()` - Stop instance gracefully

**Module Size:** ~184 lines
**Dependencies:** None (stdlib only)

### module_monitor.py
- `ModuleMonitor` - Track module sizes
- `ModuleSizeViolation` - Violation data class

**Module Size:** ~246 lines
**Dependencies:** None (stdlib only)

### settings_manager.py
- `SettingsManager` - Persistent settings with Qt integration

**Module Size:** ~321 lines
**Dependencies:** PyQt6

## Module Size Guidelines

All modules in sw_core follow strict size guidelines:

- **Target:** <400 lines (Ideal)
- **Acceptable:** 400-600 lines (OK, monitor growth)
- **Warning:** 600-800 lines (At the limit)
- **Critical:** >800 lines (MUST refactor)

Current status: All modules ✅ within target (<400 lines)

## Usage in Templates

### PyQt App Template

```python
# In your PyQt app
from sw_core import SettingsManager, ModuleMonitor

settings = SettingsManager("SilverWizard", "MyApp")
monitor = ModuleMonitor(Path.cwd())
```

### Parent CC Template

```python
# In Parent CC tools
from sw_core import spawn_claude_instance

result = spawn_claude_instance(
    app_folder=app_path,
    app_name=app_name,
    initial_prompt="Start monitoring"
)
```

## Development

### Running Tests

```bash
cd shared/sw_core
pytest
```

### Code Quality

```bash
# Format and lint
ruff check .
ruff format .
```

## Version History

### 1.0.0 (2026-02-06)
- Initial extraction from templates
- spawn_claude.py - Claude instance management
- module_monitor.py - Module size tracking
- settings_manager.py - Qt settings persistence

## License

MIT License - Silver Wizard Software
