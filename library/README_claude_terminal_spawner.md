# Claude Terminal Spawner Library

**Source:** Extracted from C3 project (`services/terminal_manager.py`)
**Validation:** Proven in C3's cycle tests (Step1-Step9.sh)
**File:** `library/claude_terminal_spawner.py`

## Overview

Complete protocol for spawning new macOS Terminal windows running Claude Code, injecting text to auto-start sessions, and providing **foolproof termination without approval dialogs**.

## Key Features

### 1. Terminal Spawning
- ✅ Creates **NEW windows** (not tabs) using AppleScript + System Events (Cmd+N)
- ✅ Captures PID using `echo $$ > .claude/claude-terminal.pid`
- ✅ Returns macOS window ID for precise window control
- ✅ Optional window positioning (left/right half-screen)
- ✅ Bypasses trust prompts with `--permission-mode dontAsk`

### 2. Text Injection
- ✅ Injects text into terminal as if user typed it
- ✅ Handles long text by breaking into chunks (avoids keystroke drops)
- ✅ Optional auto-submit (presses Enter after typing)
- ✅ Configurable wait time for Claude initialization

### 3. Foolproof Termination
- ✅ Uses **SIGKILL (signal 9)** - forceful, no confirmation dialogs
- ✅ Kills child processes first (MCP servers, Node.js, etc.)
- ✅ Closes Terminal window via AppleScript
- ✅ Cleans up PID files
- ✅ **NEVER** triggers "Do you want to terminate?" dialog

## Usage

### Basic Example

```python
from pathlib import Path
from library.claude_terminal_spawner import ClaudeTerminalSpawner

# Create spawner
spawner = ClaudeTerminalSpawner()

# Spawn terminal
info = spawner.spawn_terminal(
    project_path=Path("/path/to/project"),
    terminal_id="task_1",
    label="Task 1",
    position="left"  # Optional: "left" or "right"
)

# Inject text to auto-start Claude
spawner.inject_text(
    window_id=info['window_id'],
    text="Please analyze the codebase and create a summary.",
    submit=True
)

# Later... close without approval dialog
spawner.close_terminal(
    pid=info['pid'],
    window_id=info['window_id'],
    terminal_id=info['terminal_id']
)
```

### Advanced Example: Multiple Terminals

```python
spawner = ClaudeTerminalSpawner()

# Spawn terminals on left and right
left_info = spawner.spawn_terminal(
    project_path=Path("/projects/app1"),
    terminal_id="left_terminal",
    label="Frontend",
    position="left"
)

right_info = spawner.spawn_terminal(
    project_path=Path("/projects/app2"),
    terminal_id="right_terminal",
    label="Backend",
    position="right"
)

# Inject different commands
spawner.inject_text(left_info['window_id'], "Work on the UI components", submit=True)
spawner.inject_text(right_info['window_id'], "Review the API endpoints", submit=True)

# Check if still alive
if spawner.is_terminal_alive("left_terminal"):
    print("Left terminal is running")

# List all active
print(f"Active terminals: {spawner.list_active_terminals()}")

# Close both (no approval dialogs!)
spawner.close_terminal(left_info['pid'], left_info['window_id'], "left_terminal")
spawner.close_terminal(right_info['pid'], right_info['window_id'], "right_terminal")
```

### Tracked vs Untracked Mode

```python
# Tracked mode (recommended)
info = spawner.spawn_terminal(
    project_path=Path("/path/to/project"),
    terminal_id="tracked_terminal",  # Provide ID for tracking
    label="My Task"
)
# Spawner keeps track, can check status later
print(spawner.is_terminal_alive("tracked_terminal"))

# Untracked mode (manual management)
info = spawner.spawn_terminal(
    project_path=Path("/path/to/project"),
    terminal_id="temp_terminal",  # Still need ID for spawn
    label="Quick Task"
)
# Close immediately with just PID and window_id
spawner.close_terminal(info['pid'], info['window_id'])
# No tracking cleanup needed
```

## API Reference

### `ClaudeTerminalSpawner`

#### `spawn_terminal()`

```python
spawn_terminal(
    project_path: Path,
    terminal_id: str,
    label: Optional[str] = None,
    position: Optional[str] = None,
    permission_mode: str = "dontAsk",
    additional_flags: str = ""
) -> dict
```

**Returns dict with:**
- `terminal_id`: Your identifier
- `window_id`: macOS window ID (for AppleScript)
- `pid`: Process ID
- `project_path`: Path to project
- `pid_file`: Path to PID file

**Raises:** `RuntimeError` if spawn fails

#### `inject_text()`

```python
inject_text(
    window_id: str,
    text: str,
    submit: bool = True,
    wait_before_inject: float = 8.0
) -> bool
```

Injects text into terminal. Returns `True` if successful.

**Note:** Claude needs ~8 seconds to initialize before accepting input.

#### `close_terminal()`

```python
close_terminal(
    pid: int,
    window_id: str,
    terminal_id: Optional[str] = None
) -> bool
```

**Foolproof termination using SIGKILL - NEVER shows approval dialog.**

Returns `True` if successful.

#### `is_terminal_alive()`

```python
is_terminal_alive(terminal_id: str) -> bool
```

Check if a tracked terminal's process is still running.

#### `get_terminal_info()`

```python
get_terminal_info(terminal_id: str) -> Optional[dict]
```

Get info dict for a tracked terminal, or `None` if not found.

#### `list_active_terminals()`

```python
list_active_terminals() -> list
```

Returns list of terminal IDs currently tracked.

#### `cleanup_dead_terminals()`

```python
cleanup_dead_terminals() -> int
```

Remove dead terminals from tracking and clean up PID files.
Returns count of terminals cleaned up.

## Technical Details

### Why SIGKILL Works

**SIGKILL (signal 9)** cannot be caught, blocked, or ignored by the target process. It's handled directly by the kernel which forcefully terminates the process. This means:

1. No cleanup handlers run in the target process
2. Terminal.app doesn't get a chance to show confirmation dialog
3. Process dies immediately without interaction

This is exactly what we want for automated terminal management.

### AppleScript Window Creation

The protocol uses:

```applescript
-- Press Cmd+N to create NEW window (not tab)
tell application "System Events"
    keystroke "n" using command down
end tell
```

This ensures a **new window** is created, not a tab. Important for:
- Window positioning (left/right)
- Independent window closure
- Avoiding interference with user's existing Terminal tabs

### PID Capture Mechanism

The command chain includes:

```bash
cd '/path/to/project' && echo $$ > .claude/claude-terminal.pid && claude --permission-mode dontAsk
```

`$$` is the shell's PID, which becomes the parent PID of the Claude process. We use this for:
- Process existence checking (`os.kill(pid, 0)`)
- Process termination (`os.kill(pid, 9)`)
- Child process cleanup (`pkill -9 -P <pid>`)

### Permission Mode

`--permission-mode dontAsk` bypasses Claude's trust prompts. This is essential for:
- Automated spawning without user interaction
- Running multiple Claude instances simultaneously
- Background/unattended operation

## Integration Patterns

### With EE Cycle Manager

```python
# In handoff automation
spawner = ClaudeTerminalSpawner()

# Spawn fresh instance
info = spawner.spawn_terminal(
    project_path=Path.cwd(),
    terminal_id="ee_cycle_next",
    label=f"EE Cycle {next_cycle_num}"
)

# Inject handoff prompt
spawner.inject_text(
    window_id=info['window_id'],
    text=f"Continue from Cycle {current_cycle}: {handoff_context}",
    submit=True
)

# Old instance can self-terminate
# (spawner.close_terminal() can be called from any process)
```

### With PyQt App Template

```python
# In app launcher/manager
spawner = ClaudeTerminalSpawner()

# Spawn Claude for development assistance
dev_terminal = spawner.spawn_terminal(
    project_path=app_project_path,
    terminal_id="dev_assistant",
    label="Dev Assistant",
    position="right"
)

# Auto-start with context
spawner.inject_text(
    window_id=dev_terminal['window_id'],
    text="I'm working on the PyQt app. Review the recent changes.",
    submit=True
)
```

### With MM Mesh

```python
# Spawn Claude instances for distributed tasks
spawner = ClaudeTerminalSpawner()

tasks = [
    ("task_1", "Review security", Path("/projects/app1")),
    ("task_2", "Write tests", Path("/projects/app2")),
    ("task_3", "Update docs", Path("/projects/app3"))
]

for task_id, instruction, path in tasks:
    info = spawner.spawn_terminal(
        project_path=path,
        terminal_id=task_id,
        label=task_id.replace("_", " ").title()
    )

    spawner.inject_text(
        window_id=info['window_id'],
        text=instruction,
        submit=True
    )

# Monitor progress via MM mesh registration
# Close when tasks complete
for task_id, _, _ in tasks:
    if task_complete(task_id):
        info = spawner.get_terminal_info(task_id)
        if info:
            spawner.close_terminal(info['pid'], info['window_id'], task_id)
```

## Testing

Run the built-in example:

```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE
python3 library/claude_terminal_spawner.py /path/to/test/project
```

This will:
1. Spawn a Claude terminal on the left half
2. Inject "Hello Claude! Please list the files in the current directory."
3. Wait for ENTER
4. Close the terminal (no approval dialog!)

## Validation History

- **Source:** C3 project (`services/terminal_manager.py`)
- **Testing:** Proven in C3's `cycle_tests/` (Step1-Step9.sh)
- **Validation:**
  - ✅ Multiple concurrent terminals
  - ✅ Selective closure (close T1, T2 stays running)
  - ✅ Window ID isolation
  - ✅ SIGKILL termination (no dialogs)
  - ✅ PID tracking accuracy
  - ✅ Safe operation alongside user's Claude sessions

## Known Limitations

1. **macOS Only:** Uses AppleScript and Terminal.app
2. **Claude CLI Required:** Requires `claude` command in PATH
3. **Initialization Wait:** Claude needs ~8s to initialize before accepting text injection
4. **Long Text Chunking:** Very long text (>1000 chars) should be split into multiple `inject_text()` calls

## Best Practices

1. **Always provide `terminal_id`** for tracking and cleanup
2. **Use `position` parameter** when spawning multiple terminals for visibility
3. **Wait for initialization** before injecting text (default 8s is usually sufficient)
4. **Clean up on exit** using `cleanup_dead_terminals()` or explicit `close_terminal()`
5. **Check `is_terminal_alive()`** before operating on terminals
6. **Use `--permission-mode dontAsk`** (default) for automation

## Security Considerations

- **SIGKILL is forceful** - no data save prompts, no cleanup
- **Text injection is visible** - typed text appears in Terminal (not secret)
- **PID files in `.claude/`** - ensure proper permissions
- **Trust bypass** - `--permission-mode dontAsk` skips security prompts

Use responsibly and only in trusted environments.

---

**Questions? Issues?**
See C3 project for reference implementation: `services/terminal_manager.py`
