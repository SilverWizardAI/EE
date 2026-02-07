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
python3 .C3/token_checker.py \$TOKENS --threshold X  # Check budget
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

---

# Cycle 1: Verify C3 Installation

**Expected steps:** 3

## Step 1: Verify C3 Tools

**Action:** Verify C3 is properly installed

```bash
ls -la .C3/
cat .C3/README.md | head -50
python3 .C3/ee_manager.py show
python3 .C3/send_to_monitor.py "Step 1: Verifying C3 installation"
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=1, DESCRIPTION="Verify C3 installation"

## Step 2: Test Token Checker

**Action:** Test token threshold checking

```bash
python3 .C3/token_checker.py 12000 --threshold 35
echo "Exit code: \$?"
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=2, DESCRIPTION="Test token checker"

## Step 3: Create Test File

**Action:** Create a test file

```bash
cat > test_result.txt << 'EOF'
# C3 Verification Results

All C3 tools functioning correctly.
EOF

cat test_result.txt
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=3, DESCRIPTION="Create test file"

**After Step 3:**
```bash
python3 .C3/send_to_monitor.py "End of Cycle 1"
python3 .C3/send_to_monitor.py "Plan Fully Executed"
```

---

**Version:** 1.0.0 (C3-enabled)
