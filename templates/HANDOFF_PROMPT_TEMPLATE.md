# Handoff Prompt Template for C3lite → EE Spawning

**Purpose:** Exact prompt sequence that C3lite should send when spawning next EE instance

**Critical:** Claude Code prioritizes terminal input over startup instructions, so prompts must be sent in this order via AppleScript/terminal injection

---

## 📋 Three-Prompt Sequence

### Prompt 1: Directory Navigation (Required)

**Timing:** First prompt (before anything else)
**Purpose:** Navigate to correct working directory

```applescript
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE
```

**Why first:** Must be in correct directory before Claude Code reads config files

---

### Prompt 2: Claude Context (Optional but Recommended)

**Timing:** Second prompt (after directory, before task)
**Purpose:** Provide context about the handoff

```
You are continuing work from a previous EE instance.

Previous instance reached:
• Token usage: <TOKENS_USED> / 200,000 (<PERCENTAGE>%)
• Cycle: <CYCLE_NUMBER>
• Last completed: <LAST_TASK>

This is a fresh instance with full context window available.
```

**Variables to substitute:**
- `<TOKENS_USED>`: Actual tokens from previous instance
- `<PERCENTAGE>`: Calculate percentage
- `<CYCLE_NUMBER>`: Current cycle number (from CURRENT_CYCLE.md)
- `<LAST_TASK>`: Brief description of last completed work

---

### Prompt 3: Initial Task (Required)

**Timing:** Third prompt (the main instruction)
**Purpose:** Tell EE what to do

```
Continue library extraction.

Read plans/CURRENT_CYCLE.md (Step 2) for current status.
Read plans/IMMEDIATE_NEXT.md (Step 3) for next action.

Previous cycle progress:
<PROGRESS_SUMMARY>

Continue where previous instance left off.
```

**Variables to substitute:**
- `<PROGRESS_SUMMARY>`: Read from CURRENT_CYCLE.md "Completed" section

---

## 🎯 Complete Example (What C3lite Should Send)

### Scenario: Cycle 1, extracted 2/4 components, 175K tokens used

**Prompt 1 (Directory):**
```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE
```

**Prompt 2 (Context):**
```
You are continuing work from a previous EE instance.

Previous instance reached:
• Token usage: 175,000 / 200,000 (87.5%)
• Cycle: 1
• Last completed: Extracted settings_manager.py

This is a fresh instance with full context window available.
```

**Prompt 3 (Task):**
```
Continue library extraction - Cycle 1 (Foundation Components).

Read plans/CURRENT_CYCLE.md (Step 2) for current status.
Read plans/IMMEDIATE_NEXT.md (Step 3) for next action.

Previous cycle progress:
✅ mesh_integration.py extracted
✅ settings_manager.py extracted
⏳ spawn_claude.py - NEXT
⏳ version_info/ - pending

Continue where previous instance left off.
```

---

## 🔧 Implementation in C3lite

### Using spawn_claude.py (Recommended)

```python
from services.spawn_claude import spawn_claude_instance
from pathlib import Path

# Read current state
ee_path = Path("/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE")
current_cycle = read_file(ee_path / "plans" / "CURRENT_CYCLE.md")
immediate_next = read_file(ee_path / "plans" / "IMMEDIATE_NEXT.md")

# Extract cycle number and progress
cycle_num = extract_cycle_number(current_cycle)  # e.g., 1
last_completed = extract_last_completed(current_cycle)  # e.g., "settings_manager.py"
progress_summary = extract_progress_summary(current_cycle)

# Build prompts
context_prompt = f"""You are continuing work from a previous EE instance.

Previous instance reached:
• Token usage: {previous_tokens} / 200,000 ({previous_percentage}%)
• Cycle: {cycle_num}
• Last completed: {last_completed}

This is a fresh instance with full context window available."""

task_prompt = f"""Continue library extraction - Cycle {cycle_num}.

Read plans/CURRENT_CYCLE.md (Step 2) for current status.
Read plans/IMMEDIATE_NEXT.md (Step 3) for next action.

Previous cycle progress:
{progress_summary}

Continue where previous instance left off."""

# Spawn with three-prompt sequence
result = spawn_claude_instance(
    app_folder=ee_path,
    app_name="EE",
    initial_prompt=task_prompt,  # This becomes Prompt 3
    context_prompt=context_prompt,  # This becomes Prompt 2
    # Prompt 1 (cd) is handled automatically by spawn_claude_instance
    background=True
)
```

---

### Using Terminal Manager (Alternative)

```python
from services.terminal_manager import get_terminal_manager

terminal_mgr = get_terminal_manager()

# Spawn with sequential prompts
terminal_info = terminal_mgr.spawn_monitored_session(
    project_path=Path("/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE"),
    phase_name="EE_continuation",
    project_name="EE",
    step_data={
        'step_title': f'Library Extraction - Cycle {cycle_num} (Continuation)',
        'goal': 'Continue library extraction from previous instance',
        'tasks': ['Continue from IMMEDIATE_NEXT.md'],
        'success_criteria': ['Work continues successfully'],
        'monitoring_frequency': 5
    },
    initial_prompt=task_prompt,
    context_prompt=context_prompt
)
```

---

## 📝 Helper Functions to Extract State

### Extract Cycle Number

```python
def extract_cycle_number(current_cycle_content: str) -> int:
    """Extract cycle number from CURRENT_CYCLE.md."""
    import re
    match = re.search(r'\*\*Cycle Number:\*\*\s+(\d+)', current_cycle_content)
    return int(match.group(1)) if match else 1
```

### Extract Last Completed Task

```python
def extract_last_completed(current_cycle_content: str) -> str:
    """Extract last completed item from CURRENT_CYCLE.md."""
    import re

    # Find "✅ Completed This Cycle" section
    completed_section = re.search(
        r'### ✅ Completed This Cycle\n(.*?)(?=###|\Z)',
        current_cycle_content,
        re.DOTALL
    )

    if not completed_section:
        return "Unknown"

    # Find last checkbox item
    completed_items = re.findall(r'- \[x\] (.+)', completed_section.group(1))

    return completed_items[-1] if completed_items else "Unknown"
```

### Extract Progress Summary

```python
def extract_progress_summary(current_cycle_content: str) -> str:
    """Extract progress summary from CURRENT_CYCLE.md."""
    import re

    summary_lines = []

    # Extract completed items
    completed_section = re.search(
        r'### ✅ Completed This Cycle\n(.*?)(?=###|\Z)',
        current_cycle_content,
        re.DOTALL
    )
    if completed_section:
        completed_items = re.findall(r'- \[x\] (.+)', completed_section.group(1))
        for item in completed_items[-5:]:  # Last 5 items
            summary_lines.append(f"✅ {item}")

    # Extract in-progress items
    in_progress_section = re.search(
        r'### 🚧 In Progress\n(.*?)(?=###|\Z)',
        current_cycle_content,
        re.DOTALL
    )
    if in_progress_section:
        in_progress_items = re.findall(r'- \[ \] (.+)', in_progress_section.group(1))
        if in_progress_items:
            summary_lines.append(f"⏳ {in_progress_items[0]} - NEXT")
            for item in in_progress_items[1:3]:  # Next 2 items
                summary_lines.append(f"⏳ {item} - pending")

    return "\n".join(summary_lines) if summary_lines else "See CURRENT_CYCLE.md for details"
```

---

## 🎯 Validation Checklist

**Before spawning, ensure:**
- ✅ CURRENT_CYCLE.md exists and is updated
- ✅ IMMEDIATE_NEXT.md exists and is updated
- ✅ All changes committed and pushed
- ✅ Token usage recorded (for context prompt)
- ✅ Cycle number correct
- ✅ Progress summary accurate

**After spawning, verify:**
- ✅ New terminal window opened
- ✅ In correct directory (`/A_Coding/EE`)
- ✅ Claude Code started
- ✅ Received context prompt
- ✅ Received task prompt
- ✅ Instance starts reading CURRENT_CYCLE.md

---

## 🔄 Alternate Minimal Version (Quick Handoff)

**If you just need quick continuation without full context:**

**Single Prompt:**
```
Continue library extraction for EE project.

Previous instance reached token limit. Read:
- plans/CURRENT_CYCLE.md (Step 2)
- plans/IMMEDIATE_NEXT.md (Step 3)

Continue from there.
```

**Pros:** Simple, fast
**Cons:** Less context about what happened

---

## 💡 Pro Tips

### Tip 1: Include Token Stats
Always include token usage in context prompt - helps new instance understand urgency and pacing

### Tip 2: Keep It Concise
Don't repeat info that's in CURRENT_CYCLE.md - just point to it

### Tip 3: Highlight Next Action
Explicitly state "NEXT" task so new instance knows where to start

### Tip 4: Test the Sequence
Test the three-prompt sequence manually first:
1. Open new terminal
2. Send directory prompt
3. Send context prompt
4. Send task prompt
5. Verify EE starts correctly

### Tip 5: Log Everything
C3lite should log all spawned instances with:
- Previous token count
- Cycle number
- Continuation prompt used
- New instance PID

---

## 📊 Example Session Log

```
[2026-02-06 03:15:23] EE Handoff Initiated
  Previous Instance: ee_98234
  Tokens Used: 175,234 / 200,000 (87.6%)
  Cycle: 1
  Last Completed: settings_manager.py extracted

[2026-02-06 03:15:24] Spawning Continuation
  Working Dir: /A_Coding/EE
  Context: Cycle 1 continuation
  Next Task: Extract spawn_claude.py

[2026-02-06 03:15:27] Spawn Successful
  New Instance: ee_98451
  PID: 98451
  Terminal ID: C3_EE_continuation_1

[2026-02-06 03:15:30] New Instance Active
  Confirmed: Reading CURRENT_CYCLE.md
  Status: Healthy
```

---

**This template ensures seamless handoffs between EE instances with full context preservation!** 🚀
