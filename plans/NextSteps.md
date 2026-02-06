# Next Steps

**Last completed:** Steps 1-12 (sw_core + sw_pcc libraries extracted)
**Next step:** Step 13 (Update template to use sw_core imports)

**Cycle:** 1 (Library Extraction)
**Target tokens:** 20% (~40K tokens)
**Current tokens:** ~53K (26.4%) - Cycle 1 complete

---

## Current Step Details

**Step 13: Update template to use sw_core**
- Location: `templates/pyqt_app/main.py` and other template files
- Change: Update imports from direct imports to `from sw_core import ...`
- Test: Generate app from template, verify imports work

### Required Import Changes:
```python
# OLD (direct imports)
from base_application import BaseApplication, create_application
from parent_cc_protocol import ParentCCProtocol
from version_info._version_data import VERSION

# NEW (library imports)
from sw_core import BaseApplication, create_application
from sw_core import ParentCCProtocol
from sw_core.version_info._version_data import VERSION
```

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

✅ **Steps 8-10**: sw_pcc components (JUST COMPLETED)
- registry.py (325 lines)
- create_app.py (545 lines)
- launcher.py (308 lines)

✅ **Step 12**: sw_pcc pyproject.toml + __init__.py + README (JUST COMPLETED)

---

**See full plan:** `plans/LIBRARY_EXTRACTION_PLAN.md`
