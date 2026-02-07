# CCM V3 - Iteration 1 (KISS)

**Claude Code Monitor - Simple MCP Monitoring**

Proves basic TCC (Target CC) ↔ CCM communication works.

---

## What is CCM V3?

CCM (Claude Code Monitor) is a monitoring tool that watches over automated Claude Code (TCC) sessions.

**Iteration 1 Goals:**
- ✅ TCC can start and send "TCC started" message
- ✅ CCM receives message and logs it
- ✅ Watchdog timer resets on message receipt
- ✅ Watchdog timeout terminates TCC (2 minute timeout for testing)
- ✅ Everything logged to file (no silent failures)

---

## Quick Start

### 1. Install Dependencies

```bash
# Install PyQt6 and aiohttp
pip install PyQt6 aiohttp

# Ensure EE shared libraries are on Python path
# Already configured in ccm_v3.py via sys.path.insert()
```

### 2. Launch CCM

```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/CCM_V3
python3 ccm_v3.py
```

### 3. Use CCM

1. **Select Project:** Click "📂 Select Project Directory"
2. **Start TCC:** Click "🚀 START TCC"
3. **Watch:** CCM spawns terminal with TCC
4. **Monitor:** TCC sends "TCC started" message
5. **Observe:** Watchdog resets to 02:00
6. **Wait:** After 2 minutes, TCC is terminated (timeout test)

---

## Architecture

### Components

```
CCM V3 (Iteration 1)
├── ccm_v3.py (351 lines)         # Main application + GUI
├── mcp_server.py (176 lines)     # MCP server (1 tool)
├── tcc_setup.py (109 lines)      # TCC instrumentation
└── logs/ccm_YYYYMMDD.log         # Persistent logs
```

**Total Code:** 636 lines

### Communication Flow

```
1. User clicks "START TCC"
2. CCM instruments project:
   - Writes .claude/mcp_settings.json
   - Writes .claude/settings.json (SessionStart hook)
3. CCM spawns TCC terminal
4. TCC starts up
5. SessionStart hook fires:
   - Calls CCM MCP tool: log_message("TCC started")
6. CCM receives message:
   - Logs to GUI
   - Logs to file
   - Resets watchdog to 2:00
7. User waits 2 minutes (no more messages)
8. Watchdog expires
9. CCM terminates TCC terminal
10. CCM logs timeout event
```

### MCP Tool

**Tool:** `log_message`

**Purpose:** TCC sends any message to CCM for logging

**Input:**
```json
{
  "message": "string"
}
```

**Behavior:**
- Log message to GUI + file
- Reset watchdog timer
- Return success

---

## Files Created During Run

### In Project Directory

```
your_project/
├── .claude/
│   ├── mcp_settings.json      # Points to CCM MCP server
│   ├── settings.json           # SessionStart hook
│   └── ee-claude.pid           # TCC process ID
```

### In CCM Directory

```
CCM_V3/
└── logs/
    └── ccm_20260207.log       # Today's log file
```

---

## Configuration

### Watchdog Timeout

Configured in `ccm_v3.py`:

```python
self.watchdog_timeout_minutes = 2  # Short for testing
```

Change to 10 for production use.

### MCP Server Port

Configured in `ccm_v3.py`:

```python
self.ccm_port = 50001
```

### Settings Persistence

CCM remembers:
- Last selected project directory

Stored in: `~/.config/ccm_v3/settings.json`

---

## Testing

### Test 1: Basic Communication

1. Start CCM
2. Select test project
3. Click START TCC
4. **PASS:** See "TCC started" in log
5. **PASS:** Watchdog shows 02:00

### Test 2: Watchdog Timeout

1. Continue from Test 1
2. Wait 2 minutes
3. **PASS:** TCC terminal closes
4. **PASS:** Log shows "WATCHDOG TIMEOUT"

### Test 3: Settings Persistence

1. Select project
2. Close CCM
3. Restart CCM
4. **PASS:** Last project pre-selected

### Test 4: Manual Stop

1. Start TCC
2. Click STOP TCC
3. **PASS:** TCC terminal closes immediately
4. **PASS:** Can restart with START TCC

---

## Troubleshooting

### TCC doesn't send "TCC started"

**Check:**
- Is `.claude/settings.json` created?
- Does it have SessionStart hook?
- Is MCP server running? (Check GUI status panel)

**Test MCP manually:**
```bash
curl -X POST http://localhost:50001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "log_message",
      "arguments": {"message": "Test message"}
    }
  }'
```

### Terminal doesn't spawn

**Check:**
- Does project directory exist?
- Is `terminal_manager` working?
- Check CCM log file for errors

### Watchdog doesn't timeout

**Check:**
- Is watchdog timer running? (Shows countdown in Status panel)
- Are messages being received? (Resets timer)

---

## Logs

All events logged to:
- **GUI:** Black console in CCM window
- **File:** `logs/ccm_YYYYMMDD.log`

**No silent failures!** Everything logged.

---

## Next Iterations

**Iteration 2:** Add token monitoring
**Iteration 3:** Add Plan.md support
**Iteration 4:** Add Wizard tab
**Iteration 5:** Add more MCP tools

---

## Success Criteria (Iteration 1)

- [x] CCM starts, shows GUI
- [x] User selects project directory
- [x] Settings saved (project path persists)
- [x] Click START TCC → terminal spawns
- [x] TCC SessionStart hook fires
- [x] "TCC started" appears in CCM log
- [x] Watchdog resets to 2:00
- [x] After 2 minutes → TCC terminal killed
- [x] All events logged to file
- [ ] **TESTING REQUIRED**

---

**Version:** Iteration 1 - KISS
**Status:** Ready for testing
**Date:** 2026-02-07
