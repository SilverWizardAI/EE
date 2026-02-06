# EE Monitor GUI Modifications Needed

## Current Status
✅ Simplified plan structure created and committed
✅ Comms protocol defined
❌ GUI needs updating for 60% logging window

---

## Required Changes to `tools/ee_monitor_gui.py`

### 1. Enlarge Logging Window to 60% of Screen

**Current:** Small ~100px text areas
**Needed:** Single large scrollable log ~550-600px (60% of 900px screen)

**Change lines 236-256:**
```python
# DELETE the small "Cycle Reports Log" section
# DELETE the small "Progress" section

# ADD new Communications Log section:
log_group = QGroupBox("📡 Communications Log")
log_layout = QVBoxLayout()

self.comms_log = QTextEdit()
self.comms_log.setReadOnly(True)
self.comms_log.setMinimumHeight(550)  # 60% of screen
self.comms_log.setStyleSheet("""
    QTextEdit {
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-family: 'Courier New', 'Consolas', monospace;
        font-size: 10pt;
        padding: 10px;
    }
""")
log_layout.addWidget(self.comms_log)

log_group.setLayout(log_layout)
layout.addWidget(log_group)
```

---

### 2. Rename "Handoff Threshold" to "Token Target"

**Change lines 145-175:**
```python
# Configuration Panel
config_group = QGroupBox("⚙️ Configuration")
config_layout = QHBoxLayout()

token_label = QLabel("Token Target %:")  # ← CHANGED from "Handoff Threshold"
token_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
config_layout.addWidget(token_label)

self.token_target_spinbox = QSpinBox()  # ← RENAMED variable
self.token_target_spinbox.setMinimum(20)
self.token_target_spinbox.setMaximum(95)
self.token_target_spinbox.setValue(85)  # ← Default 85%
self.token_target_spinbox.setSuffix("%")
config_layout.addWidget(self.token_target_spinbox)

tokens_equiv = QLabel("(170K tokens)")
tokens_equiv.setStyleSheet("color: #666;")
config_layout.addWidget(tokens_equiv)

config_group.setLayout(config_layout)
layout.addWidget(config_group)
```

---

### 3. Initialize File Logging

**Add to `__init__` method:**

```python
def __init__(self, ee_root: Path):
    super().__init__()

    self.ee_root = ee_root
    self.next_steps_file = ee_root / "plans" / "NextSteps.md"
    self.current_cycle = 1  # Track cycle number in App

    # Setup file logging
    self.log_dir = ee_root / "logs"
    self.log_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    self.log_file = self.log_dir / f"ee_monitor_{today}.log"

    # Open log file in append mode
    self.log_fh = open(self.log_file, 'a', encoding='utf-8')

    self.init_ui()
    # ... rest of init
```

**Add cleanup on close:**

```python
def closeEvent(self, event):
    """Clean up on close."""
    if hasattr(self, 'log_fh'):
        self.log_fh.close()
    event.accept()
```

### 4. Add Logging Methods

**Add these methods to the class:**

```python
def log_terminal_inject(self, command: str, prompt: str):
    """Log terminal injection sent to EE (screen + file)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Screen log (HTML, color-coded)
    html = f'<span style="color:#3b82f6;font-weight:bold;">[{timestamp}] CYCLE {self.current_cycle} | TERMINAL INJECT → EE</span><br>'
    html += f'<span style="color:#60a5fa;">  Command: {command}</span><br>'
    html += f'<span style="color:#60a5fa;">  Prompt: {prompt[:100]}...</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

    # File log (plain text)
    self.log_fh.write(f"[{full_timestamp}] CYCLE {self.current_cycle} | TERMINAL INJECT → EE\n")
    self.log_fh.write(f"Command: {command}\n")
    self.log_fh.write(f"Prompt: {prompt}\n\n")
    self.log_fh.flush()

def log_mm_send(self, service: str, method: str, payload: dict):
    """Log MM message sent to EE."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    html = f'<span style="color:#8b5cf6;font-weight:bold;">[{timestamp}] MM SEND → {service}.{method}</span><br>'
    html += f'<span style="color:#a78bfa;">  {json.dumps(payload, indent=2)}</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

def log_mm_receive(self, service: str, method: str, payload: dict):
    """Log MM message received from EE (screen + file)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract display message if present
    display_msg = payload.get("message", "")

    # Screen log (HTML, color-coded)
    html = f'<span style="color:#10b981;font-weight:bold;">[{timestamp}] CYCLE {self.current_cycle} | MM RECV ← {service}.{method}</span><br>'
    if display_msg:
        html += f'<span style="color:#34d399;font-weight:bold;">  → {display_msg}</span><br>'
    html += f'<span style="color:#34d399;">  {json.dumps(payload, indent=2)}</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

    # File log (plain text)
    self.log_fh.write(f"[{full_timestamp}] CYCLE {self.current_cycle} | MM RECV ← {service}.{method}\n")
    self.log_fh.write(f"Payload: {json.dumps(payload)}\n")
    if display_msg:
        self.log_fh.write(f"Display: {display_msg}\n")
    self.log_fh.write("\n")
    self.log_fh.flush()

def log_end_of_cycle(self, cycle: int, last_step: int, next_step: int,
                     total_steps: int, tokens_used: int, tokens_limit: int):
    """Log end of cycle report (screen + file)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pct = (tokens_used / tokens_limit) * 100

    # Screen log (HTML, color-coded)
    html = f'<span style="color:#f59e0b;font-weight:bold;">[{timestamp}] ═══ END CYCLE {cycle} ═══</span><br>'
    html += f'<span style="color:#fbbf24;">  Last Step: {last_step} of {total_steps}</span><br>'
    html += f'<span style="color:#fbbf24;">  Next Step: {next_step} of {total_steps}</span><br>'
    html += f'<span style="color:#fbbf24;">  Tokens: {tokens_used:,}/{tokens_limit:,} ({pct:.1f}%)</span><br>'
    html += f'<span style="color:#fbbf24;">  Status: Handoff successful</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

    # File log (plain text)
    self.log_fh.write(f"[{full_timestamp}] {'='*50}\n")
    self.log_fh.write(f"END CYCLE {cycle}\n")
    self.log_fh.write(f"Last step: {last_step} of {total_steps}\n")
    self.log_fh.write(f"Next step: {next_step} of {total_steps}\n")
    self.log_fh.write(f"Tokens: {tokens_used:,}/{tokens_limit:,} ({pct:.1f}%)\n")
    self.log_fh.write(f"Status: Handoff successful\n")
    self.log_fh.write(f"{'='*50}\n\n")
    self.log_fh.flush()

def log_error(self, message: str):
    """Log error message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    html = f'<span style="color:#ef4444;font-weight:bold;">[{timestamp}] ❌ ERROR</span><br>'
    html += f'<span style="color:#f87171;">  {message}</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

def log_info(self, message: str):
    """Log info message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    html = f'<span style="color:#9ca3af;">[{timestamp}] ℹ️  {message}</span><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

def _scroll_to_bottom(self):
    """Auto-scroll to bottom of log."""
    from PyQt6.QtGui import QTextCursor
    cursor = self.comms_log.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    self.comms_log.setTextCursor(cursor)
```

---

### 4. Modify `start_cycle()` to Pass Token Target and Log

**Update the `start_cycle()` method:**

```python
def start_cycle(self):
    """Start EE cycle."""
    try:
        tm = get_terminal_manager()

        # Get token target from spinbox
        token_target_pct = self.token_target_spinbox.value()

        # Build prompt with token target
        prompt = (
            f"Library extraction - Cycle 1.\n"
            f"Read plans/NextSteps.md for current step.\n"
            f"Token target: {token_target_pct}%\n"
            f"Report progress via MM mesh."
        )

        # LOG TERMINAL INJECTION
        self.log_terminal_inject(
            command=f"cd {self.ee_root}",
            prompt=prompt
        )

        # Spawn terminal
        terminal_info = tm.spawn_claude_terminal(
            project_path=self.ee_root,
            session_id="ee_cycle_1",
            label="EE CYCLE 1",
            position="left"
        )

        # Inject prompt
        tm.inject_initialization_command(
            terminal_id=terminal_info["terminal_id"],
            session_id="ee_cycle_1",
            command=prompt
        )

        # LOG MM SEND (simulated - actual MM mesh call would go here)
        self.log_mm_send(
            service="ee_control",
            method="proceed",
            payload={"token_target_pct": token_target_pct}
        )

        # Update UI
        self.start_btn.setEnabled(False)
        self.start_btn.setText("✅ Cycle Running")

        self.log_info(f"Spawned Cycle 1 (Token target: {token_target_pct}%)")

    except Exception as e:
        self.log_error(f"Failed to start cycle: {str(e)}")
```

---

### 5. Add MM Mesh Receive Handler

**When EE reports back via MM mesh, log it and update display:**

```python
def on_mm_message_received(self, message: dict):
    """Handle MM mesh messages from EE."""
    service = message.get("service", "unknown")
    action = message.get("action", "unknown")

    self.log_mm_receive(service, action, message)

    # Handle specific actions
    if action == "step_start":
        step = message.get("step")
        total = message.get("total_steps", 15)
        step_name = message.get("step_name", "")

        # Update status display
        self.step_label.setText(f"Current: Step {step} of {total}")
        if step_name:
            self.step_label.setToolTip(step_name)

    elif action == "step_complete":
        step = message.get("step")
        total = message.get("total_steps", 15)

        # Update status display
        self.step_label.setText(f"Completed: Step {step} of {total}")

    elif action == "handoff":
        last_step = message.get("last_step")
        next_step = message.get("next_step")
        total = message.get("total_steps", 15)
        tokens_used = message.get("tokens_used", 0)
        tokens_limit = message.get("tokens_limit", 200000)

        # Log end of cycle
        self.log_end_of_cycle(
            self.current_cycle,
            last_step,
            next_step,
            total,
            tokens_used,
            tokens_limit
        )

        # Increment cycle number for next spawn
        self.current_cycle += 1

        # Update status
        self.cycle_label.setText(f"Cycle: {self.current_cycle - 1} (handoff)")
        self.step_label.setText(f"Next: Step {next_step} of {total}")
```

### 6. Update Status Display Section

**Modify the status group to show cycle and step:**

```python
# Status Display
status_group = QGroupBox("Current Status")
status_layout = QVBoxLayout()

self.cycle_label = QLabel("Cycle: 1")
self.cycle_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
self.cycle_label.setStyleSheet("color: #2196F3;")
status_layout.addWidget(self.cycle_label)

self.step_label = QLabel("Step: Waiting to start")
self.step_label.setFont(QFont("Arial", 12))
status_layout.addWidget(self.step_label)

status_group.setLayout(status_layout)
layout.addWidget(status_group)
```

---

## Visual Layout

```
┌─────────────────────────────────────────┐
│   🏛️ EE Monitor                         │  10%
│                                          │
│   🚀 START CYCLE 🚀                     │  10%
│                                          │
│   ⚙️ Configuration                       │
│   Token Target %: [85] (170K tokens)    │  10%
│                                          │
│   Current Status                         │
│   Cycle: 1 | Step: 3                    │  10%
├─────────────────────────────────────────┤
│   📡 Communications Log                  │
│                                          │
│   [10:15:23] TERMINAL INJECT → EE       │
│     Command: cd /A_Coding/EE            │
│     Prompt: Library extraction...       │
│                                          │
│   [10:15:45] MM SEND → ee_control       │
│     {"token_target_pct": 85}            │
│                                          │
│   [10:15:50] MM RECV ← ee_status        │
│     {"action": "step_start", "step": 1} │
│                                          │
│   [10:16:30] MM RECV ← ee_status        │  60%
│     {"action": "step_complete"...}      │
│                                          │
│   [12:45:30] ═══ END CYCLE 1 ═══        │
│     Last Step: 3                        │
│     Next Step: 4                        │
│     Tokens: 178K/200K (89%)             │
│     Status: Handoff successful          │
│                                          │
│   [Scrollable - more logs above/below]  │
│                                          │
└─────────────────────────────────────────┘
```

---

## Color Coding

- **Blue** (#3b82f6): Terminal injection sent
- **Purple** (#8b5cf6): MM send
- **Green** (#10b981): MM receive
- **Orange** (#f59e0b): End of cycle
- **Red** (#ef4444): Errors
- **Gray** (#9ca3af): Info messages

---

## Summary

**User controls:**
- Token target % (20-95%)
- START button (spawns with target)

**App logs:**
1. ✅ Terminal injection sent
2. ✅ MM send
3. ✅ MM receive
4. ✅ End of cycle reports

**Log window:**
- 60% of screen
- Scrollable
- Color-coded
- Auto-scroll to bottom

---

**Next:** Apply these changes to `tools/ee_monitor_gui.py` or use the v2 file I tried to create above.
