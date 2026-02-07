# Plan 3: C3-Enabled Multi-Cycle Orchestration

**Your startup format:** `C{N}|{X}%|Plan_3.md`
- C{N} = Your cycle number
- {X}% = Your token limit (stay below this)

---

## 🛠️ C3 Tools Available

Your workspace is instrumented with **C3 (Claude Code Controller) v1.0.0**.

**All tools are in the `.C3/` directory.** Read `.C3/README.md` for full documentation.

**Quick reference:**
```bash
python3 .C3/send_to_monitor.py "message"           # Send status to CCM
python3 .C3/ee_manager.py show                      # Show current state
python3 .C3/ee_manager.py update --step-complete N  # Mark step done
python3 .C3/token_checker.py $TOKENS --threshold X  # Check budget
```

---

## 🚨 STARTUP PROTOCOL

**Step 1: Parse your startup message**
Example: `C1|35%|Plan_3.md` means:
- You are Cycle 1
- Token limit: 35%
- Read this file (you're doing it now)

**Step 2: Check your state**
```bash
python3 .C3/ee_manager.py show
cat cycle_state.json
```

**Step 3: Find your section below**
- Scroll to "## Cycle {N}"
- Find "### Step {M}" matching your cycle_state.json
- Execute that step IMMEDIATELY

**Step 4: Token awareness**
After EACH tool call:
- Check system message for token count
- Calculate: (tokens_used / 200000) * 100 = percent
- If percent > your limit: STOP and run close_cycle (see below)

---

## 🛑 CLOSE CYCLE COMMAND

**If tokens exceed your limit BEFORE starting a step:**
```bash
python3 .C3/ee_manager.py update --cycle-end "Token threshold"
python3 .C3/send_to_monitor.py "End of Cycle {N}: Token threshold {X.X}%"
exit 0
```

---

## 📋 STEP COMPLETION PROTOCOL

**After EVERY successful step:**
```bash
# 1. Update state
python3 .C3/ee_manager.py update --step-complete {STEP} --task "{DESCRIPTION}"

# 2. Commit (no push - test environment)
git add -A
git commit -m "Step {STEP}: {DESCRIPTION}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 3. Report (with your actual token %)
python3 .C3/send_to_monitor.py "Step {STEP} completed: Tokens: {X.X}%; Status: OK"
```

**Note:** No `git push` in test environments. Tools are pre-installed in `.C3/`.

---

# Cycle 1: Verify C3 Installation

**Expected steps:** 3
**Expected tokens:** ~5K (2.5% of budget)

---

## Step 1: Verify C3 Tools

**Check tokens first:** If > your limit, run close_cycle command above.

**Action:** Verify C3 is properly installed

```bash
# Check C3 directory
ls -la .C3/

# Read C3 documentation
cat .C3/README.md | head -50

# Show current state
python3 .C3/ee_manager.py show

# Test monitor communication
python3 .C3/send_to_monitor.py "Step 1: Verifying C3 installation"
```

**Expected output:**
- `.C3/` directory exists
- 4 tools present: send_to_monitor.py, ee_manager.py, token_checker.py, terminate_cycle.py
- README.md shows version 1.0.0
- State shows Cycle 1, Step 1
- Monitor receives test message

**Then:** Run STEP COMPLETION PROTOCOL above with STEP=1, DESCRIPTION="Verify C3 installation"

---

## Step 2: Test Token Checker

**Check tokens first:** If > your limit, run close_cycle command.

**Action:** Test token threshold checking

```bash
# Get current token count from system message
# Example: if you're at 12000 tokens:

# Test 1: Under threshold (should pass)
python3 .C3/token_checker.py 12000 --threshold 35
echo "Exit code: $?"  # Should be 0

# Test 2: Over threshold (should fail)
python3 .C3/token_checker.py 80000 --threshold 35
echo "Exit code: $?"  # Should be 1

# Test 3: At exact threshold
python3 .C3/token_checker.py 70000 --threshold 35
echo "Exit code: $?"  # Should be 1 (gate behavior)
```

**Expected behavior:**
- Under threshold: Exit code 0, message shows "OK to proceed"
- Over threshold: Exit code 1, message shows "Threshold exceeded"
- At threshold: Exit code 1 (gate behavior - don't start new work)

**Then:** Run STEP COMPLETION PROTOCOL with STEP=2, DESCRIPTION="Test token checker"

---

## Step 3: Create Test File

**Check tokens first:** If > your limit, run close_cycle command.

**Action:** Create a simple test file to verify git workflow

```bash
# Create test file
cat > test_result.txt << 'EOF'
# C3 Verification Results

## Test Summary
- C3 Version: 1.0.0
- Tools Present: 4/4
- Token Checker: Working
- Monitor Communication: Working
- State Management: Working

## Conclusion
All C3 tools functioning correctly. Ready for multi-cycle orchestration.

Generated: $(date -Iseconds)
EOF

# Verify file created
cat test_result.txt
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=3, DESCRIPTION="Create test file"

**After Step 3:** Check your token usage. If under limit, report cycle complete:
```bash
python3 .C3/ee_manager.py update --cycle-end "Cycle 1 complete"
python3 .C3/send_to_monitor.py "End of Cycle 1: All steps complete"
```

---

# Cycle 2: Build Simple Feature

**Expected steps:** 2
**Expected tokens:** ~8K (4% of budget)

---

## Step 1: Create Feature File

**Check tokens first:** Use token_checker.py before starting.

**Action:** Create a simple Python script

```bash
# Create feature
cat > feature.py << 'EOF'
#!/usr/bin/env python3
"""
Simple feature demonstrating C3-enabled development.
"""

def hello_c3():
    """Greet the C3 system."""
    return "Hello from C3-enabled workspace!"

if __name__ == "__main__":
    print(hello_c3())
EOF

chmod +x feature.py
python3 feature.py
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=1, DESCRIPTION="Create feature file"

---

## Step 2: Document Feature

**Check tokens first:** Use token_checker.py before starting.

**Action:** Create feature documentation

```bash
# Create docs
cat > FEATURE.md << 'EOF'
# Feature Documentation

## Overview
Simple demonstration feature for C3-enabled workflow.

## Usage
```bash
python3 feature.py
```

## Output
```
Hello from C3-enabled workspace!
```

## Development Notes
- Created in Cycle 2, Step 2
- Uses C3 tools for state management
- Demonstrates multi-cycle orchestration
EOF

cat FEATURE.md
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=2, DESCRIPTION="Document feature"

**After Step 2:** Report cycle complete:
```bash
python3 .C3/ee_manager.py update --cycle-end "Cycle 2 complete"
python3 .C3/send_to_monitor.py "End of Cycle 2: Feature complete"
python3 .C3/send_to_monitor.py "Plan Fully Executed"
```

---

## 🎉 Plan Complete

When you reach "Plan Fully Executed", your work is done.

CCM will detect plan completion and terminate gracefully.

---

## 📚 Additional Notes

### About C3 Tools

**send_to_monitor.py:**
- Sends messages to CCM via Unix socket
- Resets watchdog timer
- Logs progress

**ee_manager.py:**
- Manages cycle_state.json
- Tracks steps completed
- Handles cycle transitions

**token_checker.py:**
- Checks if tokens exceed threshold
- Returns exit code 0 (OK) or 1 (exceeded)
- Gate behavior: blocks new work at threshold

**terminate_cycle.py:**
- Emergency cycle termination
- Updates state and notifies CCM
- Optional (ee_manager.py --cycle-end is preferred)

### About Schema

`cycle_state.json` structure:
```json
{
  "cycle": 1,
  "next_step": 1,
  "history": [
    {
      "cycle": 1,
      "step": 1,
      "task": "Description",
      "completed_at": "ISO-timestamp"
    }
  ],
  "created_at": "ISO-timestamp",
  "last_updated": "ISO-timestamp"
}
```

---

**Version:** 1.0.0 (C3-enabled)
**Status:** Active
**Cycles:** 2
**Total Steps:** 5
