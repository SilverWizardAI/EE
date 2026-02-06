# 📦 LIBRARY COMPONENTS (Detailed Extraction List)

**Purpose:** Complete inventory of components to extract
**Format:** Each component lists source location, destination, and extraction notes
**Status:** See `status/LIBRARY_EXTRACTION_STATUS.md` for completion checkboxes

---

## 🎯 Extraction Strategy

### Reading Order
1. Read this file to understand WHAT to extract
2. Work through components in order (top to bottom)
3. Update status file after each completion
4. Test after each extraction before moving to next

### Extraction Process for Each Component
```bash
# For each component:
1. Read source file completely
2. Understand dependencies
3. Copy to EE/shared/[library]/
4. Adjust imports if needed
5. Test the extracted module
6. Document in README
7. Update status file
8. Commit with message: "feat: Extract [component] from [source]"
```

---

## 📚 Phase 1A: sw_core Library (Application Framework)

**Location:** `EE/shared/sw_core/`
**Purpose:** Core application framework used by all PyQt6 apps

### Component 1.1: base_application.py

**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/base_application.py`
**Destination:** `EE/shared/sw_core/base_application.py`
**Size:** ~400-500 lines

**What it provides:**
- BaseApplication class (QMainWindow subclass)
- MM mesh integration
- Graceful shutdown handling
- Signal handling for Qt
- Heartbeat timer
- Settings management
- Module monitoring integration
- Window setup and status bar

**Dependencies:**
- PyQt6 (QtWidgets, QtCore, QtGui)
- mesh_integration module
- settings_manager module
- module_monitor module
- parent_cc_protocol module

**Extraction notes:**
- This is the CORE class - extract carefully
- Preserve all signal handling logic
- Keep QTimer parenting (critical for Qt event loop)
- Test with minimal app after extraction

**Testing:**
```python
# Create minimal test:
from sw_core.base_application import BaseApplication, create_application

class TestApp(BaseApplication):
    def __init__(self, **kwargs):
        super().__init__(app_name="TestApp", **kwargs)

# Run and verify:
# - Window appears
# - Mesh connects
# - Heartbeat works
# - Clean shutdown
```

---

### Component 1.2: parent_cc_protocol.py

**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/parent_cc_protocol.py`
**Destination:** `EE/shared/sw_core/parent_cc_protocol.py`
**Size:** ~300-400 lines

**What it provides:**
- ParentCCProtocol class
- Spawn EE workers
- Monitor worker health
- Send prompts to workers
- Handle worker responses
- Query worker status

**Dependencies:**
- mesh_integration module
- spawn_claude module (see 1.4)
- Python logging

**Extraction notes:**
- Depends on spawn_claude - extract that first
- Or extract both together
- Test spawning functionality thoroughly

---

### Component 1.3: mesh_integration.py

**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/mesh_integration.py`
**Destination:** `EE/shared/sw_core/mesh_integration.py`
**Size:** ~200-300 lines

**What it provides:**
- MeshIntegration class
- Connect to MM proxy
- Register app with mesh
- Send heartbeats
- Call mesh services
- Error handling and reconnection

**Dependencies:**
- MM mesh client (from MM project)
- Python requests or httpx

**Extraction notes:**
- Core networking component
- Test with MM mesh running (port 6001)
- Verify auto-reconnection works
- Check heartbeat functionality

**Testing:**
```python
# Verify:
# 1. MM mesh running on port 6001
# 2. App registers successfully
# 3. Heartbeat appears in mesh
# 4. Can call services
# 5. Survives MM restart (reconnect)
```

---

### Component 1.4: spawn_claude.py

**Source:** `/A_Coding/Test_App_PCC/tools/spawn_claude.py`
**Destination:** `EE/shared/sw_core/spawn_claude.py`
**Size:** ~250-350 lines

**What it provides:**
- spawn_claude_instance() function
- AppleScript prompt injection (C3's proven pattern)
- Directory navigation
- Context prompts
- Initial task prompts
- Background/foreground modes

**Dependencies:**
- subprocess (AppleScript execution)
- pathlib
- logging

**Extraction notes:**
- This is CRITICAL for Parent CC protocol
- Uses C3's proven prompt injection pattern (see memory/MEMORY.md)
- Sequence: directory prompt → claude prompt → initial prompt
- Necessary because Claude Code prioritizes terminal input over startup

**Testing:**
```python
# Test spawning:
result = spawn_claude_instance(
    app_folder=Path("/path/to/test"),
    app_name="TestWorker",
    initial_prompt="Say hello",
    background=False
)

# Verify:
# - New terminal window appears
# - Navigates to correct directory
# - Claude Code starts
# - Receives initial prompt
# - Instance ID returned
```

---

### Component 1.5: settings_manager.py

**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/settings_manager.py`
**Destination:** `EE/shared/sw_core/settings_manager.py`
**Size:** ~200-250 lines

**What it provides:**
- SettingsManager class
- Load/save app settings
- JSON-based configuration
- Default values
- Settings validation
- Per-app settings files

**Dependencies:**
- Python json
- pathlib
- logging

**Extraction notes:**
- Simple utility, low risk
- Handles missing files gracefully
- Creates settings directory if needed

**Testing:**
```python
# Test:
mgr = SettingsManager(app_name="TestApp")
mgr.set("key", "value")
mgr.save()
# Verify file created in correct location
# Restart and verify settings loaded
```

---

### Component 1.6: module_monitor.py

**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/module_monitor.py`
**Destination:** `EE/shared/sw_core/module_monitor.py`
**Size:** ~150-200 lines

**What it provides:**
- ModuleMonitor class
- Scan Python modules for size
- Warn about bloated modules (>600 lines)
- Report cyclomatic complexity
- Quality metrics

**Dependencies:**
- Python ast module
- pathlib
- logging

**Extraction notes:**
- Development tool, not runtime critical
- Helps maintain code quality
- Can extract later if needed (lower priority)

---

### Component 1.7: version_info/

**Source:** `/A_Coding/PIW/version_info/`
**Destination:** `EE/shared/sw_core/version_info/`
**Size:** Package directory with multiple files

**What it provides:**
- Version management system
- _version_data.py (actual version info)
- _version_manager.py (version operations)
- Version bumping (major/minor/patch)
- Git tag integration
- Changelog tracking

**Dependencies:**
- Python packaging
- Git (for tagging)
- logging

**Extraction notes:**
- PIW has the best implementation
- Copy entire directory
- May need slight adjustments for EE structure
- Very useful for all projects

**Files to copy:**
```
version_info/
├── __init__.py
├── _version_data.py
├── _version_manager.py
└── README.md
```

**Testing:**
```python
from sw_core.version_info import VERSION, VersionManager

print(VERSION)  # Should show version string
mgr = VersionManager()
mgr.bump_patch()  # Test bumping
```

---

## 📚 Phase 1B: sw_pcc Library (Parent CC Tools)

**Location:** `EE/shared/sw_pcc/`
**Purpose:** Tools for creating and managing PyQt apps

### Component 2.1: create_app.py

**Source:** `/A_Coding/Test_App_PCC/tools/create_app.py`
**Destination:** `EE/shared/sw_pcc/create_app.py`
**Size:** ~400-500 lines

**What it provides:**
- Create new apps from template
- Copy template directory
- Substitute variables (app name, version, etc.)
- Generate project structure
- Initialize git repository
- Create initial commit

**Dependencies:**
- pathlib
- shutil (for directory copying)
- Jinja2 or string.Template (for substitution)
- argparse (CLI interface)
- logging

**Extraction notes:**
- This is the MAIN app creation tool
- Test thoroughly - broken creates = broken workflow
- Verify template variable substitution
- Test with actual template creation

**Testing:**
```bash
# Test:
python -m sw_pcc.create_app \
  --name NewTestApp \
  --template pyqt_app \
  --output /tmp/test_apps

# Verify:
# - Directory created
# - Files generated correctly
# - No template variables left unsubstituted
# - App runs successfully
```

---

### Component 2.2: registry.py

**Source:** `/A_Coding/Test_App_PCC/tools/registry.py`
**Destination:** `EE/shared/sw_pcc/registry.py`
**Size:** ~200-300 lines

**What it provides:**
- AppRegistry class
- Register apps with paths
- Discover installed apps
- List available apps
- Get app metadata
- JSON-based storage

**Dependencies:**
- Python json
- pathlib
- logging

**Extraction notes:**
- Simple registry system
- Low risk extraction
- Test discovery functionality

**Testing:**
```python
from sw_pcc.registry import AppRegistry

registry = AppRegistry()
registry.register("TestApp", "/path/to/app")
apps = registry.list_apps()
# Verify app appears in list
```

---

### Component 2.3: launcher.py

**Source:** `/A_Coding/Test_App_PCC/tools/launch_app.py`
**Destination:** `EE/shared/sw_pcc/launcher.py`
**Size:** ~250-350 lines

**What it provides:**
- AppLauncher class
- Launch apps by name
- Pass command-line arguments
- Background/foreground modes
- Process management
- Launch multiple instances

**Dependencies:**
- subprocess
- registry module (2.2)
- pathlib
- logging

**Extraction notes:**
- Depends on registry - extract after registry
- Test launching functionality thoroughly
- Verify process management (start/stop/restart)

**Testing:**
```bash
# Test:
python -m sw_pcc.launcher --app TestApp --action launch

# Verify:
# - App launches successfully
# - Process tracked correctly
# - Can stop/restart
# - Clean shutdown
```

---

## 📦 Phase 2: Package Configuration

### Component 3.1: pyproject.toml (sw_core)

**Location:** `EE/shared/sw_core/pyproject.toml`
**Content:** Package metadata and dependencies

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sw-core"
version = "0.1.0"
description = "Silver Wizard Core Application Framework"
authors = [{name = "Silver Wizard Software"}]
requires-python = ">=3.13"
dependencies = [
    "PyQt6>=6.6.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.7.0",
    "ruff>=0.0.287",
]
```

**Testing:**
```bash
cd EE/shared/sw_core
pip install -e .
# Verify installation works
python -c "from sw_core import BaseApplication; print('OK')"
```

---

### Component 3.2: pyproject.toml (sw_pcc)

**Location:** `EE/shared/sw_pcc/pyproject.toml`
**Content:** Package metadata and dependencies

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sw-pcc"
version = "0.1.0"
description = "Silver Wizard Parent CC Tools"
authors = [{name = "Silver Wizard Software"}]
requires-python = ">=3.13"
dependencies = [
    "sw-core>=0.1.0",
]

[project.scripts]
create-app = "sw_pcc.create_app:main"
launch-app = "sw_pcc.launcher:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
]
```

---

### Component 3.3: README.md (sw_core)

**Location:** `EE/shared/sw_core/README.md`
**Content:** Usage documentation

```markdown
# sw_core - Silver Wizard Core Framework

Core application framework for Silver Wizard Software PyQt6 applications.

## Installation

```bash
pip install -e path/to/EE/shared/sw_core
```

## Usage

```python
from sw_core import BaseApplication, create_application

class MyApp(BaseApplication):
    def __init__(self, **kwargs):
        super().__init__(app_name="MyApp", **kwargs)
        # Your app code here

if __name__ == "__main__":
    import sys
    sys.exit(create_application(MyApp, "MyApp", "1.0.0"))
```

## Components

- **BaseApplication**: Main application class with mesh integration
- **ParentCCProtocol**: Spawn and control Claude Code workers
- **MeshIntegration**: Connect to MM mesh proxy
- **SettingsManager**: App settings management
- **ModuleMonitor**: Code quality monitoring
- **version_info**: Version management system
```

---

### Component 3.4: README.md (sw_pcc)

**Location:** `EE/shared/sw_pcc/README.md`
**Content:** Tool documentation

```markdown
# sw_pcc - Silver Wizard Parent CC Tools

Tools for creating and managing PyQt6 applications.

## Installation

```bash
pip install -e path/to/EE/shared/sw_pcc
```

## Usage

### Create new app

```bash
create-app --name MyNewApp --template pyqt_app
```

### Launch app

```bash
launch-app --app MyApp --action launch
```

## Components

- **create_app**: Create new apps from templates
- **registry**: App discovery and registration
- **launcher**: Launch and manage apps
```

---

## 📋 Extraction Order (Recommended)

**Cycle 1: Foundation**
1. mesh_integration.py (no dependencies)
2. settings_manager.py (no dependencies)
3. spawn_claude.py (no dependencies)
4. version_info/ (no dependencies)

**Cycle 2: Core Application**
5. base_application.py (depends on 1, 2)
6. parent_cc_protocol.py (depends on 1, 3)
7. module_monitor.py (optional, can be later)

**Cycle 3: PCC Tools**
8. registry.py (no dependencies)
9. create_app.py (no heavy dependencies)
10. launcher.py (depends on 8)

**Cycle 4: Packaging & Testing**
11. Create pyproject.toml files
12. Create README files
13. Test installations
14. Update templates to use libraries

---

## ✅ Completion Checklist

Mark in `status/LIBRARY_EXTRACTION_STATUS.md`:

**Phase 1A (sw_core):**
- [ ] mesh_integration.py extracted and tested
- [ ] settings_manager.py extracted and tested
- [ ] spawn_claude.py extracted and tested
- [ ] version_info/ extracted and tested
- [ ] base_application.py extracted and tested
- [ ] parent_cc_protocol.py extracted and tested
- [ ] module_monitor.py extracted and tested
- [ ] pyproject.toml created
- [ ] README.md created
- [ ] Package installs successfully
- [ ] All imports work

**Phase 1B (sw_pcc):**
- [ ] registry.py extracted and tested
- [ ] create_app.py extracted and tested
- [ ] launcher.py extracted and tested
- [ ] pyproject.toml created
- [ ] README.md created
- [ ] Package installs successfully
- [ ] CLI commands work

**Phase 2 (Integration):**
- [ ] Template updated to use sw_core
- [ ] Created test app from updated template
- [ ] Test app runs successfully
- [ ] All functionality preserved
- [ ] No regressions

---

## 🎯 Success Metrics

**Code Quality:**
- All modules < 600 lines (warning), ideally < 400
- All public APIs documented
- No hardcoded paths or credentials
- Clean imports (no circular dependencies)

**Functionality:**
- 100% of original functionality preserved
- All tests pass
- No errors in logs
- Clean startup and shutdown

**Integration:**
- Existing projects can optionally use libraries
- New projects use libraries by default
- Templates generate working apps
- Documentation complete

---

**Next Steps:** Start with Cycle 1 components (simplest, no dependencies) and work through systematically. Test after each extraction. Commit frequently. Document everything.
