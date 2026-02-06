# Next Steps

**Last completed:** Step 13 - Update templates to use sw_core imports ✅
**Next step:** Step 14 - Create test app and validate full lifecycle

**Cycle:** Next
**Target tokens:** 20% (~40K tokens)

---

## Step 13 Completion Summary ✅

**COMPLETED in Cycle 1:**

### What Was Done:

1. **MM Mesh Integration**
   - Created `tools/ee_mesh_client.py` for EE instance registration
   - Registered as 'ee_cycle_1' with get_status tool
   - Integrated with monitor for progress updates

2. **Template Updates**
   - Updated `main.py` to import from sw_core
   - Updated `__init__.py` to import from sw_core
   - Updated `test_mm_integration.py` imports
   - Updated `version_manager.py` imports
   - Fixed VERSION import to use `get_version()` function

3. **Removed Duplicates**
   - Deleted `base_application.py` (now in sw_core)
   - Deleted `mesh_integration.py` (now in sw_core)
   - Deleted `parent_cc_protocol.py` (now in sw_core)
   - Deleted `version_info/` directory (now in sw_core)

4. **Library Fixes**
   - Fixed `sw_pcc/pyproject.toml` build configuration
   - Created manual .pth file: `/opt/homebrew/lib/python3.13/site-packages/_sw_manual.pth`
   - Points to: `/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared`

5. **Testing**
   - Generated test app (TestLib2) from updated template
   - Verified all sw_core imports work correctly
   - Verified all sw_pcc imports work correctly

### Result:
✅ Template now uses shared libraries instead of duplicating code
✅ All imports working correctly
✅ Code duplication eliminated

---

## Current Step: Step 14 - Create Test App and Validate

**Goal:** Generate a complete test application and validate full lifecycle.

**Tasks:**
1. Generate test app from updated template
2. Fix template customization (main.py placeholders not being replaced)
3. Run test app (headless mode)
4. Test mesh integration
5. Test Parent CC protocol
6. Test settings manager
7. Test module monitor
8. Validate full lifecycle (startup → register → heartbeat → shutdown)
9. Check for clean state (no zombies, no stale entries)

**Known Issues to Fix:**
- Template customization only updates: `version.json`, `__init__.py`, `README.md`
- Need to add `main.py` to customization list in `create_app.py`
- Placeholders like `{APP_NAME}` not being replaced in main.py

---

## Completed in Cycle 1

✅ **Steps 1-7**: sw_core components (already existed)
- mesh_integration.py
- settings_manager.py
- spawn_claude.py
- version_info/
- base_application.py
- parent_cc_protocol.py
- module_monitor.py

✅ **Step 11**: sw_core pyproject.toml (already existed)

✅ **Steps 8-10**: sw_pcc components (Completed earlier)
- registry.py (325 lines)
- create_app.py (545 lines)
- launcher.py (308 lines)

✅ **Step 12**: sw_pcc pyproject.toml + __init__.py + README (Completed earlier)

✅ **Step 13**: Template updates (JUST COMPLETED)
- All imports now use sw_core
- Duplicate files removed
- Libraries installed and tested

---

## Installation Notes

**Python Version:** Use Python 3.13+
```bash
python3.13 -m pip install --break-system-packages -e shared/sw_core
python3.13 -m pip install --break-system-packages -e shared/sw_pcc
```

**Or use manual .pth file** (CURRENT APPROACH):
```bash
echo "/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared" > \
  /opt/homebrew/lib/python3.13/site-packages/_sw_manual.pth
```

**Import Test:**
```python
from sw_core.base_application import BaseApplication
from sw_core.version_info import get_version
from sw_pcc.create_app import create_app_from_template
```

---

**See full plan:** `plans/LIBRARY_EXTRACTION_PLAN.md`
