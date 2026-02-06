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

### 3. Add Logging Methods

**Add these methods to the class:**

```python
def log_terminal_inject(self, command: str, prompt: str):
    """Log terminal injection sent to EE."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    html = f'<span style="color:#3b82f6;font-weight:bold;">[{timestamp}] TERMINAL INJECT → EE</span><br>'
    html += f'<span style="color:#60a5fa;">  Command: {command}</span><br>'
    html += f'<span style="color:#60a5fa;">  Prompt: {prompt[:100]}...</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

def log_mm_send(self, service: str, method: str, payload: dict):
    """Log MM message sent to EE."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    html = f'<span style="color:#8b5cf6;font-weight:bold;">[{timestamp}] MM SEND → {service}.{method}</span><br>'
    html += f'<span style="color:#a78bfa;">  {json.dumps(payload, indent=2)}</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

def log_mm_receive(self, service: str, method: str, payload: dict):
    """Log MM message received from EE."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    html = f'<span style="color:#10b981;font-weight:bold;">[{timestamp}] MM RECV ← {service}.{method}</span><br>'
    html += f'<span style="color:#34d399;">  {json.dumps(payload, indent=2)}</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

def log_end_of_cycle(self, cycle: int, last_step: int, next_step: int,
                     tokens_used: int, tokens_limit: int):
    """Log end of cycle report."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    pct = (tokens_used / tokens_limit) * 100
    html = f'<span style="color:#f59e0b;font-weight:bold;">[{timestamp}] ═══ END CYCLE {cycle} ═══</span><br>'
    html += f'<span style="color:#fbbf24;">  Last Step: {last_step}</span><br>'
    html += f'<span style="color:#fbbf24;">  Next Step: {next_step}</span><br>'
    html += f'<span style="color:#fbbf24;">  Tokens: {tokens_used:,}/{tokens_limit:,} ({pct:.1f}%)</span><br>'
    html += f'<span style="color:#fbbf24;">  Status: Handoff successful</span><br><br>'
    self.comms_log.append(html)
    self._scroll_to_bottom()

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

### 5. Add MM Mesh Receive Handler (Future)

**When EE reports back via MM mesh, log it:**

```python
def on_mm_message_received(self, message: dict):
    """Handle MM mesh messages from EE."""
    service = message.get("service", "unknown")
    action = message.get("action", "unknown")

    self.log_mm_receive(service, action, message)

    # Handle specific actions
    if action == "step_start":
        step = message.get("step")
        self.log_info(f"EE started Step {step}")

    elif action == "step_complete":
        step = message.get("step")
        self.log_info(f"EE completed Step {step}")

    elif action == "handoff":
        cycle = message.get("cycle", 1)
        last_step = message.get("last_step")
        next_step = message.get("next_step")
        tokens_used = message.get("tokens_used", 0)
        tokens_limit = message.get("tokens_limit", 200000)

        self.log_end_of_cycle(cycle, last_step, next_step, tokens_used, tokens_limit)
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
