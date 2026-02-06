# Library Extraction Plan

Extract reusable components from Test_App_PCC, PIW, CMC into shared libraries (sw_core + sw_pcc).
Eliminate code duplication across Silver Wizard Software ecosystem.

---

## Step 1: Extract mesh_integration.py
**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/mesh_integration.py`
**Destination:** `EE/shared/sw_core/mesh_integration.py`
**Test:** Import + connect to MM mesh (port 6001)
**Dependencies:** None

## Step 2: Extract settings_manager.py
**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/settings_manager.py`
**Destination:** `EE/shared/sw_core/settings_manager.py`
**Test:** Save/load settings to JSON file
**Dependencies:** None

## Step 3: Extract spawn_claude.py
**Source:** `/A_Coding/Test_App_PCC/tools/spawn_claude.py`
**Destination:** `EE/shared/sw_core/spawn_claude.py`
**Test:** Spawn test instance with AppleScript
**Dependencies:** None

## Step 4: Extract version_info/
**Source:** `/A_Coding/PIW/version_info/` (entire directory)
**Destination:** `EE/shared/sw_core/version_info/`
**Test:** Import VERSION, test version bumping
**Dependencies:** None

## Step 5: Extract base_application.py
**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/base_application.py`
**Destination:** `EE/shared/sw_core/base_application.py`
**Test:** Create minimal app with mesh integration
**Dependencies:** Steps 1-4

## Step 6: Extract parent_cc_protocol.py
**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/parent_cc_protocol.py`
**Destination:** `EE/shared/sw_core/parent_cc_protocol.py`
**Test:** Spawn worker via protocol
**Dependencies:** Steps 1, 3

## Step 7: Extract module_monitor.py
**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/module_monitor.py`
**Destination:** `EE/shared/sw_core/module_monitor.py`
**Test:** Scan modules, report sizes
**Dependencies:** None

## Step 8: Extract registry.py
**Source:** `/A_Coding/Test_App_PCC/tools/registry.py`
**Destination:** `EE/shared/sw_pcc/registry.py`
**Test:** Register app + list apps
**Dependencies:** None

## Step 9: Extract create_app.py
**Source:** `/A_Coding/Test_App_PCC/tools/create_app.py`
**Destination:** `EE/shared/sw_pcc/create_app.py`
**Test:** Create test app from template
**Dependencies:** None

## Step 10: Extract launcher.py
**Source:** `/A_Coding/Test_App_PCC/tools/launch_app.py`
**Destination:** `EE/shared/sw_pcc/launcher.py`
**Test:** Launch app by name
**Dependencies:** Step 8

## Step 11: Create sw_core pyproject.toml
**Create:** `EE/shared/sw_core/pyproject.toml` with dependencies
**Test:** `pip install -e shared/sw_core`
**Dependencies:** Steps 1-7

## Step 12: Create sw_pcc pyproject.toml
**Create:** `EE/shared/sw_pcc/pyproject.toml` with dependencies
**Test:** `pip install -e shared/sw_pcc`
**Dependencies:** Steps 8-10

## Step 13: Update template to use sw_core
**Modify:** `templates/pyqt_app/` to import from sw_core
**Test:** Generate app, verify runs with libraries
**Dependencies:** Steps 11-12

## Step 14: Create test app from updated template
**Create:** Test app using updated template
**Test:** Full lifecycle (startup, mesh, shutdown)
**Dependencies:** Step 13

## Step 15: Validation testing
**Test:** All features work (mesh, spawning, settings, monitoring)
**Document:** Migration guide for existing apps
**Dependencies:** Step 14

---

**Total Steps:** 15
**Estimated Cycles:** 4-5 (3-4 steps per cycle)
**Always:** Finish current step before ending cycle
