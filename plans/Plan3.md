# Plan 3: Multi-Cycle CC Orchestration with Token Management

**Date:** 2026-02-07
**Status:** In Progress
**Goal:** Build CCM (Cycle Control Manager) + TCC (Technical Claude Clone) orchestration with token-aware cycle management

---

## Overview

This plan implements a complete CC orchestration system where:
- **CCM** (Cycle Control Manager) spawns and manages TCC instances
- **TCC** (Technical Claude Clone) executes work and reports progress
- **EEM** (EE Monitor) provides UI for user control and monitoring
- **Token Management** prevents mid-step cycle termination

---

## Key Requirements

### 1. Token Threshold Management ✅

**User Control:**
- EEM UI has "Token Threshold %" spinbox (default: **35%**)
- User can adjust before starting cycle
- Threshold passed to TCC at cycle start
- Stored in cycle config for persistence

**How it works:**
```
User sets: 35% → TCC gets max_token_percent=35
At 200K budget: 35% = 70,000 tokens

CRITICAL: This is the threshold BEFORE STARTING a step!
- At 69,999 tokens: ✅ Can start new step
- At 70,000 tokens: ❌ Cannot start new step, close cycle instead
```

**Purpose:** Prevents starting work that can't be completed within token budget

---

### 2. Pre-Step Token Gate 🆕

**Before starting ANY step, TCC must:**

```python
# Check current token usage
current_tokens = get_current_token_count()  # From API metadata
current_percent = (current_tokens / token_budget) * 100

# Gate check
if current_percent > max_token_percent:
    # DON'T start new step
    log_to_monitor(f"⚠️ Token threshold exceeded: {current_percent:.1f}% (max: {max_token_percent}%)")
    close_cycle(reason=f"Token threshold exceeded: {current_percent:.1f}%")
    sys.exit(0)
else:
    # OK to proceed
    log_to_monitor(f"✅ Starting Step {N}: Tokens at {current_percent:.1f}%")
```

**Critical:** This prevents starting work that might be interrupted mid-step

---

### 3. Step Completion Protocol 🆕

**After EVERY step completes, TCC must:**

```bash
# 1. Update cycle status
python3 tools/ee_manager.py update --step-complete <N> --task "<description>"

# 2. Commit and push changes
git add -A
git commit -m "Step <N>: <description>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push

# 3. Report to monitor with standardized format
python3 tools/send_to_monitor.py "Step <N> completed: Tokens: X.X%; Status: OK, updated & pushed"

# 4. Check token threshold (post-step)
current_percent = (current_tokens / token_budget) * 100
if current_percent > max_token_percent:
    log_to_monitor(f"Cycle {cycle_num} closed: Token threshold exceeded: {current_percent:.1f}%")
    close_cycle()
```

**Status Values:**
- `OK` - Step succeeded, status updated, changes committed/pushed
- `NOK` - Step failed or incomplete (explain what failed)

**Format Examples:**
```
Step 1 completed: Tokens: 12.3%; Status: OK, updated & pushed
Step 2 completed: Tokens: 24.7%; Status: OK, updated & pushed
Step 3 completed: Tokens: 38.2%; Status: NOK, commit failed
```

---

### 4. Post-Step Threshold Check 🆕

**After completing step, before starting next:**

```python
# Calculate current usage
current_percent = (current_tokens / token_budget) * 100

# Check threshold
if current_percent > max_token_percent:
    # Close cycle gracefully
    message = f"Cycle {cycle_num} closed: Token threshold exceeded: {current_percent:.1f}% (max: {max_token_percent}%)"

    # Report to monitor
    send_to_monitor(message)

    # Update cycle status
    ee_manager.update("--cycle-end", message)

    # Exit cleanly
    sys.exit(0)
```

**Purpose:** Ensures cycle ends gracefully after completing step, not mid-step

---

### 5. CCM 10-Second Timeout Before Killing TCC 🆕

**Requirement:** When CCM ends a cycle, user should see TCC's final state before window closes

**Implementation in CCM:**

```python
def end_cycle(self, reason: str):
    """End current cycle and prepare for next."""

    # 1. Send end_cycle signal to TCC
    self.log(f"🔴 Ending cycle: {reason}")
    self.send_to_tcc("end_cycle", {"reason": reason})

    # 2. WAIT 10 SECONDS (observer window)
    self.log("⏸️  Waiting 10 seconds (observer window)...")
    time.sleep(10)

    # 3. Now kill TCC terminal
    self.log("🔪 Terminating TCC terminal")
    self.kill_tcc_process()

    # 4. Clean up and prepare for next cycle
    self.cleanup_cycle()
    self.log("✅ Cycle ended, ready for next")
```

**User Experience:**
- TCC finishes step
- TCC reports completion
- User has 10 seconds to review TCC window
- Then TCC window closes
- CCM starts next cycle

---

## Architecture Components

### EEM (EE Monitor) - User Interface

**Responsibilities:**
- Display real-time progress
- Show MM mesh status
- Provide cycle controls
- **New:** Token Threshold % control (default 35%)

**UI Changes:**
```python
# Already exists in ee_monitor_gui.py lines 271-283
# UPDATE DEFAULT VALUE:
self.token_target_spinbox.setValue(35)  # Changed from 20 to 35
```

**Cycle Start Flow:**
```python
def start_cycle(self):
    token_threshold = self.token_target_spinbox.value()

    # Pass to TCC in initial prompt
    prompt = f"""
    Cycle {cycle_num} - Token threshold: {token_threshold}%

    CRITICAL: Check tokens before EACH step:
    - If tokens > {token_threshold}%, DON'T start step
    - Close cycle with report instead

    [Rest of prompt...]
    """
```

---

### CCM (Cycle Control Manager) - Orchestrator

**Responsibilities:**
- Spawn TCC instances
- Monitor TCC progress (via MM mesh)
- Handle cycle transitions
- **New:** 10-second timeout before killing TCC

**Key Features:**
- Heartbeat protocol (polls TCC every 30s)
- Automatic cycle transitions
- Terminal management
- Clean shutdown

**Files to Create:**
- `templates/ccm_template/` - CCM application template
- `templates/ccm_template/ccm_main.py` - Main CCM logic
- `templates/ccm_template/ccm_config.json` - Configuration

---

### TCC (Technical Claude Clone) - Worker

**Responsibilities:**
- Execute work tasks
- Report progress via MM mesh
- Respond to status polls
- **New:** Token-aware step management
- **New:** Step completion protocol

**Token Management Logic:**

```python
class TCCWorker:
    def __init__(self, cycle_num, token_budget, max_token_percent):
        self.cycle_num = cycle_num
        self.token_budget = token_budget
        self.max_token_percent = max_token_percent
        self.current_step = 0

    def can_start_step(self) -> tuple[bool, float]:
        """Check if we have token budget for new step."""
        current_tokens = self.get_current_tokens()
        current_percent = (current_tokens / self.token_budget) * 100

        return current_percent <= self.max_token_percent, current_percent

    def execute_step(self, step_num: int, description: str):
        """Execute a single step with token checking."""

        # PRE-STEP: Check token budget
        can_proceed, token_pct = self.can_start_step()

        if not can_proceed:
            self.close_cycle(f"Token threshold exceeded: {token_pct:.1f}%")
            return False

        # Log start
        self.send_to_monitor(f"Starting Step {step_num}: Tokens at {token_pct:.1f}%")

        # DO THE WORK
        success = self.do_step_work(step_num, description)

        # POST-STEP: Complete and check again
        if success:
            self.complete_step(step_num, description)

            # Check if threshold exceeded after work
            _, token_pct = self.can_start_step()
            if token_pct > self.max_token_percent:
                self.close_cycle(f"Token threshold exceeded: {token_pct:.1f}%")
                return False

        return success

    def complete_step(self, step_num: int, description: str):
        """Complete step with full protocol."""

        # Update status
        subprocess.run([
            "python3", "tools/ee_manager.py", "update",
            "--step-complete", str(step_num),
            "--task", description
        ])

        # Commit and push
        subprocess.run(["git", "add", "-A"])
        subprocess.run([
            "git", "commit", "-m",
            f"Step {step_num}: {description}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        ])
        subprocess.run(["git", "push"])

        # Report
        _, token_pct = self.can_start_step()
        self.send_to_monitor(
            f"Step {step_num} completed: Tokens: {token_pct:.1f}%; Status: OK, updated & pushed"
        )

    def close_cycle(self, reason: str):
        """Close cycle gracefully."""
        message = f"Cycle {self.cycle_num} closed: {reason}"
        self.send_to_monitor(message)
        subprocess.run(["python3", "tools/ee_manager.py", "update", "--cycle-end", message])
        sys.exit(0)
```

**Files to Create:**
- `templates/tcc_template/` - TCC application template
- `templates/tcc_template/tcc_worker.py` - Worker logic
- `templates/tcc_template/tcc_config.json` - Configuration

---

## Implementation Phases

### Phase 1: Foundation (Current) ✅
- [x] EEM with token threshold UI
- [x] ee_manager.py with config support
- [x] MM mesh integration
- [x] File logging infrastructure

### Phase 2: Token Management (In Progress) 🔄
- [ ] Update EEM default to 35%
- [ ] Add step completion tracking to ee_manager.py
- [ ] Create token checking utilities
- [ ] Test token threshold enforcement

### Phase 3: CCM Template 📋
- [ ] Create CCM template structure
- [ ] Implement TCC spawning logic
- [ ] Add heartbeat protocol
- [ ] Implement 10-second timeout
- [ ] Test cycle transitions

### Phase 4: TCC Template 📋
- [ ] Create TCC template structure
- [ ] Implement token-aware step execution
- [ ] Add step completion protocol
- [ ] Implement status reporting
- [ ] Test end-to-end workflow

### Phase 5: Integration Testing 🧪
- [ ] Test full CCM → TCC → EEM flow
- [ ] Test token threshold enforcement
- [ ] Test 10-second timeout
- [ ] Test multi-cycle transitions
- [ ] Test failure recovery

---

## File Changes Required

### Immediate (Phase 2)

**1. `tools/ee_monitor_gui.py`**
```python
# Line 280: Change default value
self.token_target_spinbox.setValue(35)  # Was: 20
```

**2. `tools/ee_manager.py`**
```python
# Add step completion tracking
def update_progress(..., step_completed: Optional[int] = None):
    if step_completed:
        status.steps_completed.append({
            'step': step_completed,
            'completed_at': datetime.now().isoformat(),
            'tokens_used': get_current_tokens()  # If available
        })
```

**3. `tools/send_to_monitor.py`**
```python
# Already exists, just document standard format
# Format: "Step X completed: Tokens: Y%; Status: OK/NOK, updated & pushed"
```

### Future (Phases 3-4)

**4. `templates/ccm_template/` (New)**
- Complete CCM application template
- Includes 10-second timeout logic
- Heartbeat protocol implementation

**5. `templates/tcc_template/` (New)**
- Complete TCC application template
- Token-aware step execution
- Step completion protocol

---

## Testing Strategy

### Unit Tests
- Token percentage calculation
- Step completion protocol
- Threshold checking logic

### Integration Tests
- EEM → CCM communication
- CCM → TCC spawning
- TCC → EEM status reporting
- Full cycle with token threshold

### End-to-End Tests
1. **Normal Cycle:** Start → Execute 3 steps → Complete below threshold
2. **Threshold Hit:** Start → Execute until threshold → Auto-close
3. **Multi-Cycle:** Cycle 1 closes → Cycle 2 starts → Continue work
4. **10-Second Timeout:** Watch TCC window stay visible for 10s before close

---

## Success Metrics

### Functional Requirements ✅
- [ ] Token threshold configurable in UI (default 35%)
- [ ] TCC checks tokens before each step
- [ ] TCC reports completion with token %
- [ ] TCC auto-closes if threshold exceeded
- [ ] CCM waits 10 seconds before killing TCC
- [ ] All changes committed/pushed after each step

### Quality Metrics ✅
- [ ] Zero mid-step interruptions
- [ ] 100% step completion tracking
- [ ] All cycles end gracefully
- [ ] Clean git history (no orphaned work)
- [ ] Clear user visibility (10-second window)

---

## Refinements from User Feedback

**2026-02-07 - Key Refinements:**

1. **CCM 10-Second Timeout** - User can observe TCC final state before termination
2. **Step Completion Reporting** - Standardized format with token % and OK/NOK status
3. **Token Threshold in UI** - User-configurable, default 35% (was 20%)
4. **Pre-Step Token Check** - Prevents starting work that can't complete
5. **Post-Step Token Check** - Closes cycle after completing step, not mid-step

**Rationale:**
- Prevents wasted work (starting steps without budget to complete)
- Clean cycle boundaries (complete step before closing)
- User visibility (10-second observer window)
- Clear status reporting (standardized format with token %)
- Flexible configuration (user can adjust threshold per cycle)

---

## Next Steps

**Immediate:**
1. Update EEM default token threshold to 35%
2. Add step completion tracking to ee_manager.py
3. Document step completion protocol
4. Test threshold enforcement with mock cycle

**Short Term:**
1. Create CCM template with 10-second timeout
2. Create TCC template with token management
3. Build token checking utilities
4. Integration testing

**Long Term:**
1. Add token usage visualization to EEM
2. Historical token usage analysis
3. Predictive cycle planning (estimate steps per cycle)
4. Automatic threshold tuning based on history

---

## References

- **EEM Implementation:** `tools/ee_monitor_gui.py`
- **Cycle Management:** `tools/ee_manager.py`
- **Monitor Updates:** `tools/send_to_monitor.py`
- **MEMORY.md:** Key learnings and patterns

---

**Status:** Phase 2 in progress - Implementing token management foundation
