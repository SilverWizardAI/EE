# Plan 3 v2: Multi-Cycle CC Orchestration

**Your startup message format:** `C{N}|{X}%|plans/Plan3_v2.md`
- C{N} = Your cycle number
- {X}% = Your token limit (stay below this)

---

## 🚨 STARTUP PROTOCOL - READ THIS FIRST

**Step 1: Parse your startup message**
Example: `C1|35%|plans/Plan3_v2.md` means:
- You are Cycle 1
- Token limit: 35%
- Read this file (you're doing it now)

**Step 2: Check your state**
```bash
cat cycle_state.json
```
This shows your current step number.

**Step 3: Find your section**
- Scroll to "## Cycle {N}" below
- Find "### Step {M}" matching cycle_state.json
- Execute that step IMMEDIATELY

**Step 4: Token awareness**
After EACH tool call:
- Check system message for token count
- Calculate: (tokens_used / 200000) * 100 = percent
- If percent > your limit: STOP and run close_cycle (see below)

---

## 🛑 CRITICAL RULES

**DO:**
- Check tokens after EVERY tool call
- Execute steps exactly as written
- Commit after each step
- Report progress to monitor

**DON'T:**
- Read files not explicitly listed in your step
- Explore or "understand" the codebase first
- Start a new step if tokens > limit
- Skip the completion protocol

---

## 📋 CLOSE CYCLE COMMAND

**If tokens exceed your limit BEFORE starting a step:**
```bash
python3 tools/ee_manager.py update --cycle-end "Token threshold"
python3 tools/send_to_monitor.py "End of Cycle {N}: Token threshold {X.X}%"
exit 0
```

Replace {N} with your cycle number and {X.X} with your actual token percent.

---

## 📋 STEP COMPLETION PROTOCOL

**After EVERY successful step:**
```bash
# 1. Update state
python3 tools/ee_manager.py update --step-complete {STEP} --task "{DESCRIPTION}"

# 2. Commit
git add -A
git commit -m "Step {STEP}: {DESCRIPTION}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 3. Push
git push

# 4. Report (with your actual token %)
python3 tools/send_to_monitor.py "Step {STEP} completed: Tokens: {X.X}%; Status: OK"
```

---

# Cycle 1: Foundation Tools

**Expected steps:** 3
**Expected tokens:** ~9K (4.5% of budget)

---

## Step 1: Create send_to_monitor.py

**Check tokens first:** If > your limit, run close_cycle command above.

**Action:** Create monitoring utility

```bash
mkdir -p tools
```

Create file `tools/send_to_monitor.py` with this EXACT content:

```python
#!/usr/bin/env python3
import sys, json, socket, glob

def send_to_monitor(message: str) -> bool:
    sockets = glob.glob('/tmp/ccm_session_*.sock')
    if not sockets:
        print(f"⚠️  No monitor: {message}")
        return True

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(sockets[0])
        payload = json.dumps({"method": "log_message", "message": message})
        sock.sendall((payload + '\n').encode('utf-8'))
        sock.close()
        print(f"✅ Sent: {message}")
        return True
    except Exception as e:
        print(f"⚠️  Monitor error: {e}")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 send_to_monitor.py 'message'")
        sys.exit(1)
    send_to_monitor(sys.argv[1])
```

**Verify:**
```bash
chmod +x tools/send_to_monitor.py
python3 tools/send_to_monitor.py "Test"
```

**Then:** Run STEP COMPLETION PROTOCOL (see above) with STEP=1, DESCRIPTION="Create send_to_monitor.py"

---

## Step 2: Create update_cycle_state.py

**Check tokens first:** If > your limit, run close_cycle command.

**Action:** Create state management utility

Create file `tools/update_cycle_state.py`:

```python
#!/usr/bin/env python3
import sys, json, argparse
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("cycle_state.json")

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "cycle": 1,
        "next_step": 1,
        "token_threshold_percent": 35,
        "history": [],
        "created_at": datetime.now().isoformat()
    }

def save_state(state):
    state['last_updated'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step-complete', type=int)
    parser.add_argument('--cycle-end', type=str)
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()

    state = load_state()

    if args.status:
        print(f"Cycle: {state['cycle']}, Next Step: {state['next_step']}")
        return

    if args.step_complete:
        state['history'].append({
            'cycle': state['cycle'],
            'step': args.step_complete,
            'completed_at': datetime.now().isoformat()
        })
        state['next_step'] = args.step_complete + 1
        save_state(state)
        print(f"✅ Step {args.step_complete} complete")

    if args.cycle_end:
        print(f"🔄 Cycle {state['cycle']} ended: {args.cycle_end}")
        state['cycle'] += 1
        state['next_step'] = 1
        save_state(state)

if __name__ == "__main__":
    main()
```

**Verify:**
```bash
chmod +x tools/update_cycle_state.py
python3 tools/update_cycle_state.py --status
```

**Then:** Run STEP COMPLETION PROTOCOL with STEP=2, DESCRIPTION="Create update_cycle_state.py"

---

## Step 3: Initialize cycle state

**Check tokens first:** If > your limit, run close_cycle command.

**Action:** Create initial state file

```bash
python3 tools/update_cycle_state.py --status
cat cycle_state.json
```

This creates cycle_state.json automatically.

**Verify it contains:**
- "cycle": 1
- "next_step": should be 3 (after Step 2 completion)
- "history": array with 2 entries

**Then:** Run STEP COMPLETION PROTOCOL with STEP=3, DESCRIPTION="Initialize cycle state"

---

## Post-Cycle 1: Check Tokens

After Step 3 completes, check your token usage.

**If tokens > your limit:**
```bash
python3 tools/update_cycle_state.py --cycle-end "Foundation complete"
python3 tools/send_to_monitor.py "End of Cycle 1: Token threshold {X.X}%"
exit 0
```

CCM will start Cycle 2 automatically.

---

# Cycle 2: EE Manager

**Expected steps:** 3
**Expected tokens:** ~20K (10% of budget)

---

## Step 1: Create ee_manager.py

**Check tokens first:** If > limit, close cycle.

**Action:** Create cycle management tool

Create file `tools/ee_manager.py`:

```python
#!/usr/bin/env python3
import json, argparse
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path("ee_config.json")
STATE_FILE = Path("cycle_state.json")

class EEManager:
    def __init__(self):
        self.config = self.load_config()
        self.state = self.load_state()

    def load_config(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
        config = {
            "project_name": "CCM_Test",
            "token_budget": 200000,
            "token_threshold_percent": 35,
            "created_at": datetime.now().isoformat()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return config

    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {"cycle": 1, "next_step": 1, "history": []}

    def save_state(self):
        self.state['last_updated'] = datetime.now().isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def update_progress(self, step_completed=None, task=None, cycle_end=None):
        if step_completed:
            entry = {
                'cycle': self.state['cycle'],
                'step': step_completed,
                'completed_at': datetime.now().isoformat()
            }
            if task:
                entry['task'] = task
            self.state['history'].append(entry)
            self.state['next_step'] = step_completed + 1
            self.save_state()
            print(f"✅ Step {step_completed}: {task or 'No description'}")

        if cycle_end:
            print(f"🔄 Cycle {self.state['cycle']} ended: {cycle_end}")
            self.state['cycle'] += 1
            self.state['next_step'] = 1
            self.save_state()

    def show_status(self):
        print(f"Project: {self.config['project_name']}")
        print(f"Cycle: {self.state['cycle']}, Step: {self.state['next_step']}")
        print(f"Completed: {len(self.state['history'])} steps")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    update_parser = subparsers.add_parser('update')
    update_parser.add_argument('--step-complete', type=int)
    update_parser.add_argument('--task', type=str)
    update_parser.add_argument('--cycle-end', type=str)

    subparsers.add_parser('show')

    args = parser.parse_args()
    manager = EEManager()

    if args.command == 'update':
        manager.update_progress(
            step_completed=args.step_complete,
            task=args.task,
            cycle_end=args.cycle_end
        )
    elif args.command == 'show':
        manager.show_status()

if __name__ == "__main__":
    main()
```

**Verify:**
```bash
chmod +x tools/ee_manager.py
python3 tools/ee_manager.py show
```

**Then:** STEP COMPLETION PROTOCOL with STEP=1, DESCRIPTION="Create ee_manager.py"

---

## Step 2: Create basic documentation

**Check tokens first:** If > limit, close cycle.

**Action:** Document what's been built

```bash
mkdir -p docs
```

Create file `docs/architecture.md`:

```markdown
# CCM/TCC Architecture

## Components Built

### Cycle 1: Foundation
- send_to_monitor.py - Send messages to CCM
- update_cycle_state.py - State management
- cycle_state.json - Persistent state

### Cycle 2: EE Manager
- ee_manager.py - Cycle configuration and tracking
- ee_config.json - Configuration file

## State Flow

cycle_state.json tracks:
- Current cycle number
- Next step to execute
- History of completed steps

## Token Management

Each cycle stays under token threshold (default 35%).
TCC checks tokens before each step.
If over threshold: close cycle, CCM spawns next TCC.
```

**Then:** STEP COMPLETION PROTOCOL with STEP=2, DESCRIPTION="Document architecture"

---

## Step 3: Test utilities

**Check tokens first:** If > limit, close cycle.

**Action:** Verify all utilities work

```bash
# Test state manager
python3 tools/update_cycle_state.py --status

# Test EE manager
python3 tools/ee_manager.py show

# Test monitor
python3 tools/send_to_monitor.py "Cycle 2 utilities tested"
```

All commands should execute without errors.

**Then:** STEP COMPLETION PROTOCOL with STEP=3, DESCRIPTION="Test utilities"

---

## Post-Cycle 2: Check Tokens

If tokens > limit:
```bash
python3 tools/ee_manager.py update --cycle-end "EE Manager complete"
python3 tools/send_to_monitor.py "End of Cycle 2"
exit 0
```

---

# Cycle 3: Placeholder for Future Work

**Note:** Cycle 3+ implementation depends on testing results from Cycles 1-2.

Future cycles will add:
- CCM orchestrator template
- TCC worker template
- Integration testing
- Full documentation

These will be added after validating the low-overhead startup pattern works correctly.

---

# Summary

## Cycle Checklist

**Cycle 1:**
- [ ] send_to_monitor.py created
- [ ] update_cycle_state.py created
- [ ] cycle_state.json initialized

**Cycle 2:**
- [ ] ee_manager.py created
- [ ] Basic docs created
- [ ] Utilities tested

## Token Targets

| Cycle | Expected | Actual |
|-------|----------|--------|
| 1 | ~9K (4.5%) | ___ |
| 2 | ~20K (10%) | ___ |

## Success Criteria

- ✅ Startup < 1K tokens per cycle
- ✅ All steps execute in order
- ✅ Token checks before each step
- ✅ Clean commits after each step
- ✅ Graceful cycle closures

---

**End of Plan**
