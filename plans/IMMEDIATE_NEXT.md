# Immediate Next Steps

**Last Updated:** 2026-02-06 (Token Limit Handoff)
**Status:** Library extraction complete, documentation enhanced
**Next Priority:** Testing and validation

---

## Current State

### ✅ Completed
- Library extraction (sw_core + sw_pcc) - PRODUCTION READY
- Parent CC template updated to use libraries
- EE Monitor enhanced with HTTP server capabilities
- Documentation updated with prerequisites
- Architecture analysis documented

### 🎯 Next Session Priorities

#### 1. Validate Parent CC Template End-to-End
**Why:** Template has been heavily modified. Need full lifecycle test.

**Tasks:**
1. Generate fresh test app from parent_cc template
2. Verify all library imports work
3. Test app creation workflow
4. Test Claude spawning
5. Test MM mesh registration
6. Test heartbeat protocol
7. Verify clean shutdown

**Success Criteria:**
- App generates without errors
- All sw_core/sw_pcc imports resolve
- Full lifecycle works (create → launch → run → shutdown)
- No zombies, no stale entries
- Registry updates correctly

#### 2. Test EE Monitor HTTP Server
**Why:** Added new HTTP server capability, needs validation.

**Tasks:**
1. Start EE Monitor
2. Test `log_message` tool via HTTP POST
3. Test `end_cycle` tool via HTTP POST
4. Verify thread-safe signal handling
5. Check GUI updates correctly

**Command:**
```bash
# Test log_message
curl -X POST http://localhost:8765/tools/log_message \
  -H "Content-Type: application/json" \
  -d '{"message": "Test from curl"}'

# Test end_cycle
curl -X POST http://localhost:8765/tools/end_cycle \
  -H "Content-Type: application/json" \
  -d '{"reason": "Testing cycle end"}'
```

#### 3. Clean Up Untracked Files
**Why:** Several test apps and logs not in git.

**Review:**
- `apps/` - Check if any test apps should be kept
- `logs/` - Add to .gitignore or commit important logs
- `tools/ee_monitor_test*.py` - Decide if these are permanent tools or temporary tests

---

## Known Issues

### 1. Template Customization
**Issue:** Some placeholders may not be replaced in generated apps
**Location:** `templates/parent_cc/tools/create_app.py`
**Impact:** Generated apps might have placeholder text instead of actual values
**Fix:** Verify and test template substitution logic

### 2. Module Size Monitoring
**Status:** Monitor built into template but not tested recently
**Action:** Verify module monitor still works with library imports

---

## File Changes Pending Commit

```
Modified:
  .claude/ee-claude.pid
  templates/parent_cc/README.md
  templates/parent_cc/tools/__init__.py
  templates/parent_cc/tools/create_app.py
  templates/parent_cc/tools/launch_app.py
  templates/parent_cc/tools/registry.py
  templates/parent_cc/tools/spawn_claude.py
  tools/ee_monitor_gui.py

New (needs review):
  apps/
  docs/ARCHITECTURE_ANALYSIS.md
  logs/
  tools/ee_monitor_test.py
  tools/ee_monitor_test_gui.py
```

---

## Architecture Notes

### Library Dependencies
All Parent CC instances now depend on:
- **sw_core** (8 modules, 3,461 lines)
- **sw_pcc** (3 modules, 1,210 lines)

Both must be on Python path via:
```bash
echo "/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared" > \
  /opt/homebrew/lib/python3.13/site-packages/_sw_manual.pth
```

### EE Monitor Architecture
- Main GUI thread (PyQt6)
- HTTP server thread (handles tool calls)
- Thread-safe signals (EEMSignals QObject)
- Mesh client integration (port 6001)

---

## Testing Protocol

For next session, follow "Test Until CLEAN" standard:

1. **Generate test app**
2. **Launch app (headless)**
3. **Verify full lifecycle**
4. **Check mesh registration**
5. **Test heartbeat**
6. **Graceful shutdown**
7. **Verify cleanup** (no zombies, no stale entries)

**Only after ALL pass → Ready for production use**

---

## Quick Start Commands

```bash
# Check library installation
python3 -c "import sw_core, sw_pcc; print('✓ Libraries OK')"

# Generate test app
cd templates/parent_cc
python3 tools/create_app.py --name TestPCC --output ../../apps/

# Launch test app
python3 tools/launch_app.py --app TestPCC --action launch --headless

# Monitor logs
tail -f logs/parent_cc_*.log

# Check registry
python3 tools/registry.py --list

# Clean up
python3 tools/launch_app.py --app TestPCC --action stop
```

---

**Next instance:** Start with validation testing, then clean up untracked files, then proceed with any backlog items.
