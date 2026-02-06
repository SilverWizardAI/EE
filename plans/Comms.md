# Communication Protocol (App ↔ EE via MM Mesh)

## Cycle Startup

1. **App spawns EE instance** (AppleScript terminal injection)
   - Sends directory command
   - Sends initial prompt with token target %
   - **Logs:** Terminal injection sent

2. **EE starts, reads NextSteps.md** → identifies next step number

3. **EE reports to App via MM:**
   ```json
   {
     "service": "ee_status",
     "action": "cycle_start",
     "cycle": 1,
     "next_step": 1
   }
   ```
   - **App logs:** MM received

4. **App acknowledges via MM:**
   ```json
   {
     "service": "ee_control",
     "action": "proceed",
     "token_target_pct": 85
   }
   ```
   - **App logs:** MM sent
   - **EE logs:** MM received

---

## During Work

5. **EE starts step X:**
   ```json
   {
     "service": "ee_status",
     "action": "step_start",
     "step": X,
     "total_steps": 15,
     "step_name": "Extract mesh_integration.py",
     "message": "Starting step X of 15"
   }
   ```
   - **App displays:** "Starting step X of 15"
   - **App logs:** MM received

6. **EE completes step X:**
   ```json
   {
     "service": "ee_status",
     "action": "step_complete",
     "step": X,
     "total_steps": 15,
     "step_name": "Extract mesh_integration.py",
     "status": "success",
     "message": "Completed step X of 15"
   }
   ```
   - **App displays:** "Completed step X of 15"
   - **App logs:** MM received

7. **EE checks token usage:**
   - If < target%: Go back to step 5 (start next step)
   - If >= target%: Go to Handoff

---

## Handoff Sequence

8. **EE reports handoff needed:**
   ```json
   {
     "service": "ee_status",
     "action": "handoff",
     "tokens_used": 175000,
     "tokens_limit": 200000,
     "tokens_pct": 87.5,
     "last_step": X,
     "next_step": X+1,
     "total_steps": 15,
     "last_step_name": "Extract settings_manager.py",
     "next_step_name": "Extract spawn_claude.py",
     "message": "Handoff: completed step X of 15, next is step X+1 of 15"
   }
   ```
   - **App displays:** "Handoff: completed step X of 15"
   - **App logs:** MM received (End of cycle report)

9. **EE updates NextSteps.md:**
   - Last completed: X
   - Next step: X+1

10. **EE commits changes and exits gracefully**

11. **App spawns new EE instance** (continuation cycle)
    - Repeats from step 1 with new token target

---

## MM Mesh Services

### EE provides: `ee_status`

**Methods:**
- `report_cycle_start(cycle, next_step)`
- `report_step_start(step, step_name)`
- `report_step_complete(step, step_name, status)`
- `report_handoff(tokens_used, tokens_limit, last_step, next_step)`
- `get_status()` → Returns current status

### App provides: `ee_control`

**Methods:**
- `proceed(token_target_pct)` → Confirm EE can proceed
- `pause()` → Request EE to pause
- `get_config()` → Get runtime config

---

## App Logging Requirements

**App must log ALL communications to BOTH screen AND file:**

### Screen Log (60% of window)
- Scrollable text area
- Color-coded: INJECT (blue), SEND (purple), RECV (green), CYCLE (orange), ERROR (red)
- Auto-scroll to bottom

### File Log (for analysis)
**Location:** `EE/logs/ee_monitor_YYYYMMDD.log`

**Format:** Plain text with timestamps

1. **Terminal Injection Log:**
   ```
   [2026-02-06 10:15:23] CYCLE 1 | TERMINAL INJECT → EE
   Command: cd /A_Coding/EE
   Prompt: Library extraction - Cycle 1. Read NextSteps.md. Token target: 85%
   ```

2. **MM Send Log:**
   ```
   [2026-02-06 10:15:45] CYCLE 1 | MM SEND → ee_control.proceed
   Payload: {"token_target_pct": 85}
   ```

3. **MM Receive Log:**
   ```
   [2026-02-06 10:15:50] CYCLE 1 | MM RECV ← ee_status.step_start
   Payload: {"step": 1, "total_steps": 15, "message": "Starting step 1 of 15"}
   Display: Starting step 1 of 15

   [2026-02-06 10:16:30] CYCLE 1 | MM RECV ← ee_status.step_complete
   Payload: {"step": 1, "total_steps": 15, "message": "Completed step 1 of 15", "status": "success"}
   Display: Completed step 1 of 15
   ```

4. **End of Cycle Log:**
   ```
   [2026-02-06 12:45:30] ═══════════════════════════════════════
   END CYCLE 1
   Last step: 3 of 15 (Extract spawn_claude.py)
   Next step: 4 of 15 (Extract version_info/)
   Tokens: 178,000/200,000 (89%)
   Status: Handoff successful
   ═══════════════════════════════════════
   ```

### Log File Management
- Create new log file daily: `ee_monitor_20260206.log`
- Append to existing file if same day
- Keep last 30 days of logs
- Auto-rotate on startup if > 30 days old
