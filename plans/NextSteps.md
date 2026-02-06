# Next Steps

**Last completed:** EEM heartbeat protocol implementation + monitor integration debugging
**Next step:** Implement EE instance MM mesh registration with get_status tool

**Cycle:** Next
**Target tokens:** 20% (~40K tokens)

---

## Current Step Details

**PRIORITY: Implement EE Instance MM Mesh Integration**

When EEM spawns EE instance, the startup prompt now includes:
```
FIRST: Register with MM mesh as 'ee_cycle_N' and expose get_status tool.
THEN: Report your starting step number via MM mesh to ee_monitor.
```

**EE Instance Must:**
1. Register with MM mesh on startup:
```python
import httpx

def register_with_mm_mesh(cycle_number: int):
    instance_name = f"ee_cycle_{cycle_number}"
    tools = [{
        "name": "get_status",
        "description": "Get current cycle status",
        "inputSchema": {"type": "object", "properties": {}}
    }]

    response = httpx.post(
        "http://localhost:6001/register",
        json={
            "instance_name": instance_name,
            "port": 9999,
            "tools": tools
        },
        timeout=5.0
    )
    return response.status_code == 200
```

2. Implement get_status tool that returns:
```python
{
    "step": 8,                    # Current step number
    "task": "Extracting registry.py",  # What you're doing
    "cycle_status": "running",     # or "complete"
    "progress": "60%",             # Optional progress indicator
    "tokens_used": 35000           # Current token count
}
```

3. EEM will call this tool every 120 seconds (configurable)

4. When step completes, EEM detects by comparing responses

5. When cycle completes, set `cycle_status: "complete"`

---

**THEN Continue with library extraction:**

**Step 13: Update template to use sw_core**
- Location: `templates/pyqt_app/main.py` and other template files
- Change: Update imports from direct imports to `from sw_core import ...`
- Test: Generate app from template, verify imports work

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
