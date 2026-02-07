# Token Management Guide

**Date:** 2026-02-07
**Version:** 1.0
**Status:** Production Ready

---

## Overview

This document describes EE's token management system that prevents mid-step cycle termination by enforcing configurable token thresholds.

**Key Principle:** Never start work you can't complete.

---

## Architecture

### Components

1. **EEM (EE Monitor)** - User interface with token threshold control
2. **ee_manager.py** - Cycle and step tracking
3. **token_checker.py** - Token threshold enforcement
4. **send_to_monitor.py** - Progress reporting

### Token Threshold Flow

```
User sets threshold in EEM GUI (default: 35%)
    ↓
EEM passes to TCC at cycle start
    ↓
TCC checks before EACH step
    ↓
If tokens > threshold: Close cycle gracefully
If tokens < threshold: Proceed with step
    ↓
After step completes: Check again
    ↓
Report: "Step X completed: Tokens: Y%; Status: OK/NOK, updated & pushed"
```

---

## User Interface (EEM)

### Token Threshold Control

**Location:** EEM GUI Configuration section

**Control:**
- Type: Spinbox
- Range: 20% - 95%
- Default: **35%**
- Effect: Passed to TCC at cycle start

**How to Use:**
1. Launch EEM: `python3 tools/ee_monitor_gui.py`
2. Adjust "Token Threshold %" before starting cycle
3. Click "START CYCLE"
4. Threshold is locked for this cycle
5. Adjust for next cycle if needed

**Example Values:**
- `25%` - Conservative (50K tokens **before starting step**) - More cycles, safer
- `35%` - **Default** (70K tokens **before starting step**) - Balanced
- `50%` - Aggressive (100K tokens **before starting step**) - Fewer cycles, riskier

**CRITICAL:** Threshold applies **BEFORE STARTING** each step, not before stopping!
- At 69,999 tokens: ✅ TCC can start new step
- At 70,000 tokens: ❌ TCC closes cycle instead

---

## TCC Implementation

### Pre-Step Token Check

**CRITICAL: Check BEFORE starting ANY step - this is the gate!**

At 35% threshold with 200K budget, that's 70,000 tokens. TCC checks:
- If current_tokens >= 70,000: **Don't start step** → Close cycle
- If current_tokens < 70,000: **OK to start** → Proceed with work

**Implementation:**

```python
from tools.token_checker import TokenChecker

# Initialize (values from cycle config)
checker = TokenChecker(
    token_budget=200000,
    max_token_percent=35  # From EEM
)

# Check before step
current_tokens = 55000  # Get from API metadata
can_proceed, current_percent, message = checker.can_start_step(current_tokens)

if not can_proceed:
    # Don't start step - close cycle instead
    print(message)
    close_cycle(checker.get_cycle_close_message(cycle_num, current_tokens))
    sys.exit(0)
else:
    # OK to proceed
    print(message)
    # Start step work...
```

### Step Completion Protocol

**After EVERY step completes:**

```bash
#!/bin/bash
# Full step completion protocol

STEP_NUM=1
STEP_DESC="Implement feature X"
CURRENT_TOKENS=62000

# 1. Update cycle status
python3 tools/ee_manager.py update \
  --step-complete $STEP_NUM \
  --step-desc "$STEP_DESC" \
  --tokens $CURRENT_TOKENS

# 2. Commit and push changes
git add -A
git commit -m "Step $STEP_NUM: $STEP_DESC

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push

# 3. Report to monitor (standardized format)
python3 tools/token_checker.py $CURRENT_TOKENS --threshold 35 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    STATUS="OK"
else
    STATUS="NOK"
fi

python3 tools/send_to_monitor.py \
  "Step $STEP_NUM completed: Tokens: $(python3 -c "print(round($CURRENT_TOKENS/200000*100, 1))")%; Status: $STATUS, updated & pushed"

# 4. Check if threshold exceeded (post-step)
python3 tools/token_checker.py $CURRENT_TOKENS --threshold 35
if [ $? -ne 0 ]; then
    # Threshold exceeded - close cycle
    python3 tools/send_to_monitor.py \
      "Cycle $CYCLE_NUM closed: Token threshold exceeded"
    python3 tools/ee_manager.py update \
      --cycle-end "Token threshold exceeded: $(python3 -c "print(round($CURRENT_TOKENS/200000*100, 1))")%"
    exit 0
fi
```

### Python Implementation Example

```python
from tools.token_checker import TokenChecker
import subprocess

class TCCWorker:
    def __init__(self, cycle_num: int, token_budget: int, max_token_percent: int):
        self.cycle_num = cycle_num
        self.checker = TokenChecker(token_budget, max_token_percent)
        self.current_step = 0

    def execute_cycle(self):
        """Execute work cycle with token management."""

        while True:
            # Get current token usage (from API metadata)
            current_tokens = self.get_token_usage()

            # Pre-step check
            can_proceed, percent, message = self.checker.can_start_step(current_tokens)

            if not can_proceed:
                # Close cycle gracefully
                self.close_cycle(current_tokens)
                break

            # Start next step
            self.current_step += 1
            self.send_to_monitor(f"Starting Step {self.current_step}: Tokens at {percent:.1f}%")

            # Do the work
            success, description = self.do_step_work(self.current_step)

            # Complete step
            if success:
                self.complete_step(self.current_step, description, current_tokens)

                # Check again after work
                current_tokens = self.get_token_usage()
                can_proceed, percent, _ = self.checker.can_start_step(current_tokens)

                if not can_proceed:
                    self.close_cycle(current_tokens)
                    break
            else:
                # Step failed
                self.send_to_monitor(
                    f"Step {self.current_step} completed: Tokens: {percent:.1f}%; Status: NOK, failed"
                )
                break

    def complete_step(self, step_num: int, description: str, tokens: int):
        """Complete step with full protocol."""

        # Update status
        subprocess.run([
            "python3", "tools/ee_manager.py", "update",
            "--step-complete", str(step_num),
            "--step-desc", description,
            "--tokens", str(tokens)
        ])

        # Commit and push
        subprocess.run(["git", "add", "-A"])
        commit_msg = f"Step {step_num}: {description}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        subprocess.run(["git", "commit", "-m", commit_msg])
        subprocess.run(["git", "push"])

        # Report with standardized format
        report = self.checker.format_status_report(
            step_number=step_num,
            current_tokens=tokens,
            status_ok=True,
            updated_and_pushed=True
        )
        self.send_to_monitor(report)

    def close_cycle(self, tokens: int):
        """Close cycle gracefully."""
        message = self.checker.get_cycle_close_message(self.cycle_num, tokens)
        self.send_to_monitor(message)
        subprocess.run([
            "python3", "tools/ee_manager.py", "update",
            "--cycle-end", message
        ])

    def send_to_monitor(self, message: str):
        """Send message to monitor."""
        subprocess.run(["python3", "tools/send_to_monitor.py", message])

    def get_token_usage(self) -> int:
        """Get current token usage from API metadata."""
        # In real implementation, extract from Claude API response
        # For now, return mock value
        return 50000

    def do_step_work(self, step_num: int) -> tuple[bool, str]:
        """Execute actual step work."""
        # Implementation specific to task
        return True, f"Step {step_num} work completed"
```

---

## CLI Tools

### token_checker.py

**Check if step can start:**

```bash
# Check current token usage
python3 tools/token_checker.py 50000 --threshold 35
# Output: ✅ Token budget OK: 25.0% (remaining: 10.0%) - 50,000/70,000 tokens
# Exit code: 0

# Check over threshold
python3 tools/token_checker.py 80000 --threshold 35
# Output: ❌ Token threshold exceeded: 40.0% (max: 35%) - 80,000/70,000 tokens
# Exit code: 1

# JSON output for parsing
python3 tools/token_checker.py 50000 --threshold 35 --json
# {
#   "can_proceed": true,
#   "current_tokens": 50000,
#   "current_percent": 25.0,
#   "threshold_percent": 35,
#   "threshold_tokens": 70000,
#   "message": "✅ Token budget OK: 25.0% (remaining: 10.0%) - 50,000/70,000 tokens"
# }
```

**Custom budget:**

```bash
python3 tools/token_checker.py 120000 --threshold 50 --budget 250000
```

### ee_manager.py

**Update with step completion:**

```bash
# Mark step as completed
python3 tools/ee_manager.py update \
  --step-complete 1 \
  --step-desc "Implement authentication" \
  --tokens 45000

# Mark cycle as ended
python3 tools/ee_manager.py update \
  --cycle-end "Token threshold exceeded: 38.5%"

# Regular progress update
python3 tools/ee_manager.py update \
  --task "Working on step 2" \
  --completed "Task A" "Task B" \
  --next "Complete task C"

# Check status
python3 tools/ee_manager.py status
```

---

## Status Reporting Format

### Step Completion Report (Standardized)

**Format:**
```
Step <N> completed: Tokens: <X.X>%; Status: <OK|NOK>, <action>
```

**Examples:**
```
Step 1 completed: Tokens: 12.3%; Status: OK, updated & pushed
Step 2 completed: Tokens: 24.7%; Status: OK, updated & pushed
Step 3 completed: Tokens: 38.2%; Status: NOK, commit failed
Step 4 completed: Tokens: 15.5%; Status: OK, updated & pushed
```

**Status Values:**
- `OK` - Step succeeded, status updated, changes committed/pushed
- `NOK` - Step failed or incomplete (explain what failed)

**Actions:**
- `updated & pushed` - Normal successful completion
- `not committed` - Work done but not saved to git
- `commit failed` - Commit operation failed
- `push failed` - Commit succeeded but push failed

### Cycle Close Report

**Format:**
```
Cycle <N> closed: <reason>
```

**Examples:**
```
Cycle 1 closed: Token threshold exceeded: 38.2%
Cycle 2 closed: All work completed
Cycle 3 closed: User requested
Cycle 4 closed: Error encountered
```

---

## Configuration

### EEM Configuration

**File:** `status/ee_config.json`

```json
{
  "handoff_threshold_percent": 35,
  "token_budget": 200000
}
```

**Managed by:** EEM GUI (auto-saved when user changes threshold)

### Cycle Status

**File:** `status/EE_CYCLE_STATUS.json`

```json
{
  "cycle_number": 4,
  "started_at": "2026-02-07T15:27:14.949404",
  "token_budget": 200000,
  "token_threshold": 70000,
  "current_task": "Implementing feature X",
  "tasks_completed": ["Task A", "Task B"],
  "steps_completed": [
    {
      "step": 1,
      "description": "Setup infrastructure",
      "completed_at": "2026-02-07T15:30:00.000000",
      "status": "OK",
      "tokens_used": 45000,
      "token_percent": 22.5
    },
    {
      "step": 2,
      "description": "Implement core logic",
      "completed_at": "2026-02-07T15:45:00.000000",
      "status": "OK",
      "tokens_used": 65000,
      "token_percent": 32.5
    }
  ],
  "next_action": "Test and validate",
  "last_updated": "2026-02-07T15:45:00.000000"
}
```

---

## Testing

### Unit Tests

```bash
# Test token checker with various inputs
python3 tools/token_checker.py 10000 --threshold 35  # Should pass (5%)
python3 tools/token_checker.py 50000 --threshold 35  # Should pass (25%)
python3 tools/token_checker.py 70000 --threshold 35  # Should pass (35% exactly)
python3 tools/token_checker.py 70001 --threshold 35  # Should fail (35.0005%)
python3 tools/token_checker.py 100000 --threshold 35 # Should fail (50%)
```

### Integration Test

```bash
# Full cycle test
cd /path/to/EE

# 1. Start cycle with test values
python3 tools/ee_manager.py start --task "Test cycle"

# 2. Simulate step completion
python3 tools/ee_manager.py update \
  --step-complete 1 \
  --step-desc "Test step 1" \
  --tokens 50000

# 3. Check status
python3 tools/ee_manager.py status | grep steps_completed -A 10

# 4. Verify step was recorded with token info
```

---

## Troubleshooting

### Problem: Token percentage seems wrong

**Check:**
1. Is token_budget correct? (default: 200000)
2. Are you using correct API token count?
3. Check cycle status: `python3 tools/ee_manager.py status`

### Problem: Steps not being recorded

**Check:**
1. Using `--step-complete` flag? Not just `--completed`
2. Is cycle active? Run `status` command first
3. Check file: `cat status/EE_CYCLE_STATUS.json`

### Problem: Threshold not being respected

**Check:**
1. Is TCC checking tokens before each step?
2. Verify threshold in EEM GUI matches code
3. Check token_checker.py logic with test values

---

## Best Practices

### For TCC Implementations

1. **Always check before step** - Never start work without token check
2. **Always check after step** - Token usage increases during work
3. **Use standardized reporting** - Consistent format helps monitoring
4. **Commit before checking** - Don't lose work if threshold exceeded
5. **Exit gracefully** - Clean shutdown, clear messaging

### For Users

1. **Start conservative** - Use 25-30% for critical work
2. **Adjust based on history** - Learn typical tokens-per-step
3. **Monitor trends** - Track token usage over multiple cycles
4. **Balance cycles vs. efficiency** - More cycles = more overhead

### For Monitoring

1. **Watch completion reports** - All steps should be "OK"
2. **Track token percentages** - Should increase linearly
3. **Note cycle closes** - Pattern of threshold exceeded = tune down
4. **Review step history** - Understand typical step costs

---

## Future Enhancements

### Planned Features

1. **Token Usage Visualization** - Graph in EEM showing usage over time
2. **Predictive Planning** - Estimate steps per cycle based on history
3. **Auto-Tuning** - Adjust threshold based on actual usage patterns
4. **Step Cost Estimation** - Predict token cost before starting step
5. **Multi-Cycle Analytics** - Compare cycles, identify patterns

### Possible Integrations

1. **Slack notifications** - Alert on threshold exceeded
2. **Prometheus metrics** - Export token usage for monitoring
3. **GitHub Actions** - Automated testing of token management
4. **Dashboard** - Web UI for historical analysis

---

## References

- **Plan3.md** - Complete architectural specification
- **ee_monitor_gui.py** - EEM implementation (lines 271-283)
- **ee_manager.py** - Cycle management (lines 35-52, 253-298)
- **token_checker.py** - Token enforcement utility
- **MEMORY.md** - Key learnings and patterns

---

**Version History:**
- 1.0 (2026-02-07) - Initial release with 35% default threshold
