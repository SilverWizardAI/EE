# EE Startup Guide - MM Mesh Integration

**For:** EE (Enterprise Architect) Claude Code instances
**Version:** 1.0
**Updated:** 2026-02-06

---

## Quick Start (Copy-Paste Ready)

When you start as an EE cycle, **immediately run this as your FIRST action:**

```python
from tools.ee_http_server import init_server, update_status
server = init_server(cycle_number=4)  # Use your actual cycle number
```

That's it! You're now registered with MM mesh and EEM can monitor you.

---

## Throughout Your Work

Update your status as you progress:

```python
# Starting a step
update_status(step=1, task="Reading NextSteps.md", progress="5%")

# Mid-step
update_status(step=1, task="Analyzing codebase", progress="15%", tokens_used=15000)

# Completing a step
update_status(step=2, task="Extracting components", progress="45%", tokens_used=50000)

# Near end
update_status(step=15, task="Final validation", progress="95%", tokens_used=180000)

# When completely done
update_status(cycle_status="complete", progress="100%", tokens_used=195000)
```

---

## What Happens

1. **You call `init_server()`:**
   - HTTP server starts on port 5001-5099
   - Registers with MM mesh as `ee_cycle_N`
   - Exposes tools: `get_status`, `get_progress`, `get_cycle_info`
   - Heartbeat starts (every 30s)

2. **EEM polls you every 30 seconds:**
   - Calls `get_status` via MM mesh
   - Displays your progress in GUI
   - Updates: step number, task description, progress %, tokens used

3. **When you mark `cycle_status="complete"`:**
   - EEM detects completion on next heartbeat
   - EEM kills your terminal
   - EEM starts next cycle (fresh EE instance)

---

## Status Fields

```python
update_status(
    step=5,                          # Current step number (int)
    task="Extracting sw_core module",  # What you're doing (str)
    progress="45%",                  # Progress percentage (str)
    tokens_used=50000,               # Token count (int)
    cycle_status="running",          # "running" or "complete" (str)
    next_action="Next: Step 6"       # What comes next (str)
)
```

**Required for completion:** `cycle_status="complete"` and `progress="100%"`

---

## Example: Full Cycle

```python
# === STARTUP ===
from tools.ee_http_server import init_server, update_status

# Start server (FIRST THING!)
server = init_server(cycle_number=4)

# Confirm registration
print(f"✅ Registered as {server.instance_name}")
print(f"📡 EEM will poll me every 30s for status")

# === WORK ===
# Step 1
update_status(step=1, task="Reading plans", progress="10%", tokens_used=5000)
# ... do actual work ...

# Step 2
update_status(step=2, task="Implementing fix", progress="35%", tokens_used=25000)
# ... do actual work ...

# Step 3
update_status(step=3, task="Testing", progress="70%", tokens_used=60000)
# ... do actual work ...

# === COMPLETION ===
update_status(
    step=15,
    task="All steps complete",
    cycle_status="complete",  # ← This triggers EEM to start next cycle
    progress="100%",
    tokens_used=95000
)

print("🏁 Cycle complete! EEM will detect this and start next cycle.")
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'tools'"

**Fix:** Run from EE root directory:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "tools"))
from ee_http_server import init_server, update_status
```

### "Port already in use"

The server auto-finds an available port (5001-5099). If all are taken:
- Check: `lsof -i :5001-5099`
- Kill stale servers

### "Failed to register with MM mesh"

Check MM mesh is running:
```bash
curl http://localhost:6001/services
```

If not running:
```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/MM
python3 -m mcp_mesh.proxy.server --http-only --http-port 6001 &
```

### "EEM not seeing my updates"

- Check you called `init_server()` first
- Verify registration: `curl http://localhost:6001/services | grep ee_cycle`
- Check MM mesh logs: `/tmp/mm_mesh.log`

---

## Best Practices

✅ **DO:**
- Call `init_server()` as your very first action
- Update status regularly (every major step)
- Set `cycle_status="complete"` when done
- Include meaningful task descriptions

❌ **DON'T:**
- Forget to call `init_server()` (EEM can't monitor you!)
- Update status too frequently (every 5+ minutes is fine)
- Exit without marking complete (EEM will timeout after 2min)
- Use progress > 100% or progress without % sign

---

## Architecture Reference

```
┌─────────────────────────────────────────────────┐
│  EEM (Monitor GUI)                              │
│  - MeshClient                                   │
│  - Heartbeat timer (30s)                        │
│  - Calls get_status via MM mesh                 │
└──────────────────┬──────────────────────────────┘
                   │ HTTP POST to /call
                   │ (via MM mesh)
                   ▼
┌─────────────────────────────────────────────────┐
│  MM Mesh (Central Proxy)                        │
│  - Port 6001                                    │
│  - Routes calls to instance servers             │
│  - POST to http://localhost:{port}/tools/{tool} │
└──────────────────┬──────────────────────────────┘
                   │ HTTP POST
                   ▼
┌─────────────────────────────────────────────────┐
│  EE HTTP Server (ee_http_server.py)             │
│  - Port 5001-5099                               │
│  - Handles: /tools/get_status                   │
│  - Returns JSON with current status             │
└─────────────────────────────────────────────────┘
```

---

## Related Docs

- `docs/MM_MESH_INTEGRATION.md` - Full integration documentation
- `tools/test_eem_cycle.py` - Integration test (all 10 steps passing)
- `tools/ee_http_server.py` - HTTP server implementation

---

**Remember:** Call `init_server()` FIRST, update status regularly, mark complete when done!
