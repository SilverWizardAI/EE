#!/usr/bin/env python3
"""
EE Monitor GUI - Communications Logging Version

60% screen = Communications log (scrollable, file-backed)
40% screen = Control panel (START, token target, status)

Logs ALL communications to screen + file
Module Size: ~550 lines
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QGroupBox, QPushButton, QSpinBox, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QTextCursor

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from sw_core import get_terminal_manager


class EEMonitorWindow(QMainWindow):
    """EE Monitor with comprehensive communications logging."""

    def __init__(self, ee_root: Path):
        super().__init__()

        self.ee_root = ee_root
        self.next_steps_file = ee_root / "plans" / "NextSteps.md"
        self.current_cycle = 1  # App tracks cycle number

        # Setup file logging
        self.log_dir = ee_root / "logs"
        self.log_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"ee_monitor_{today}.log"
        self.log_fh = open(self.log_file, 'a', encoding='utf-8')
        
        self.log_to_file(f"{'='*60}")
        self.log_to_file(f"EE Monitor started at {datetime.now().isoformat()}")
        self.log_to_file(f"{'='*60}\n")

        self.init_ui()

        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.check_ee_status)
        self.monitor_timer.start(5000)

    def closeEvent(self, event):
        self.log_to_file(f"\n{'='*60}")
        self.log_to_file(f"EE Monitor closed")
        self.log_to_file(f"{'='*60}\n")
        if hasattr(self, 'log_fh'):
            self.log_fh.close()
        event.accept()

    def log_to_file(self, text: str):
        self.log_fh.write(f"{text}\n")
        self.log_fh.flush()

    def init_ui(self):
        self.setWindowTitle("🏛️ EE Monitor")
        self.setGeometry(100, 100, 900, 1000)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("🏛️ EE Monitor")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # START BUTTON
        self.start_btn = QPushButton("🚀 START CYCLE 🚀")
        self.start_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.start_btn.setMinimumHeight(70)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                color: white;
                padding: 20px;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #CC0000; }
        """)
        self.start_btn.clicked.connect(self.start_cycle)
        layout.addWidget(self.start_btn)

        # Token Target
        control_group = QGroupBox("⚙️ Configuration")
        control_layout = QHBoxLayout()
        
        token_label = QLabel("Token Target %:")
        token_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        control_layout.addWidget(token_label)

        self.token_target_spinbox = QSpinBox()
        self.token_target_spinbox.setMinimum(20)
        self.token_target_spinbox.setMaximum(95)
        self.token_target_spinbox.setValue(85)
        self.token_target_spinbox.setSuffix("%")
        control_layout.addWidget(self.token_target_spinbox)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Status
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()

        self.cycle_label = QLabel("Cycle: 1")
        self.cycle_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        status_layout.addWidget(self.cycle_label)

        self.step_label = QLabel("Step: Waiting")
        status_layout.addWidget(self.step_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Communications Log (60%)
        log_group = QGroupBox("📡 Communications Log")
        log_layout = QVBoxLayout()

        self.comms_log = QTextEdit()
        self.comms_log.setReadOnly(True)
        self.comms_log.setMinimumHeight(550)
        self.comms_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.comms_log)

        clear_btn = QPushButton("🗑️ Clear Screen Log")
        clear_btn.clicked.connect(self.clear_screen_log)
        log_layout.addWidget(clear_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.log_info("EE Monitor started")
        self.log_info(f"Log file: {self.log_file}")

    # Logging methods
    def log_terminal_inject(self, command: str, prompt: str):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f'<span style="color:#3b82f6;font-weight:bold;">[{ts}] CYCLE {self.current_cycle} | TERMINAL INJECT</span><br>'
        html += f'<span style="color:#60a5fa;">  {command}</span><br>'
        html += f'<span style="color:#60a5fa;">  {prompt[:100]}...</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"[{full_ts}] CYCLE {self.current_cycle} | TERMINAL INJECT")
        self.log_to_file(f"Command: {command}")
        self.log_to_file(f"Prompt: {prompt}\n")

    def log_mm_send(self, service: str, method: str, payload: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f'<span style="color:#8b5cf6;font-weight:bold;">[{ts}] CYCLE {self.current_cycle} | MM SEND</span><br>'
        html += f'<span style="color:#a78bfa;">  {json.dumps(payload)}</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"[{full_ts}] CYCLE {self.current_cycle} | MM SEND → {service}.{method}")
        self.log_to_file(f"Payload: {json.dumps(payload)}\n")

    def log_mm_receive(self, service: str, method: str, payload: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        display_msg = payload.get("message", "")

        html = f'<span style="color:#10b981;font-weight:bold;">[{ts}] CYCLE {self.current_cycle} | MM RECV</span><br>'
        if display_msg:
            html += f'<span style="color:#34d399;font-weight:bold;">  → {display_msg}</span><br>'
        html += f'<span style="color:#34d399;">  {json.dumps(payload)}</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"[{full_ts}] CYCLE {self.current_cycle} | MM RECV ← {service}.{method}")
        self.log_to_file(f"Payload: {json.dumps(payload)}")
        if display_msg:
            self.log_to_file(f"Display: {display_msg}")
        self.log_to_file("")

    def log_end_of_cycle(self, cycle: int, last_step: int, next_step: int,
                         total_steps: int, tokens_used: int, tokens_limit: int):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pct = (tokens_used / tokens_limit) * 100

        html = f'<span style="color:#f59e0b;font-weight:bold;">[{ts}] ═══ END CYCLE {cycle} ═══</span><br>'
        html += f'<span style="color:#fbbf24;">  Last: {last_step}/{total_steps} | Next: {next_step}/{total_steps}</span><br>'
        html += f'<span style="color:#fbbf24;">  Tokens: {tokens_used:,}/{tokens_limit:,} ({pct:.1f}%)</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"[{full_ts}] {'='*50}")
        self.log_to_file(f"END CYCLE {cycle}")
        self.log_to_file(f"Last step: {last_step} of {total_steps}")
        self.log_to_file(f"Next step: {next_step} of {total_steps}")
        self.log_to_file(f"Tokens: {tokens_used:,}/{tokens_limit:,} ({pct:.1f}%)")
        self.log_to_file(f"{'='*50}\n")

    def log_error(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#ef4444;font-weight:bold;">[{ts}] ❌ ERROR: {message}</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()
        self.log_to_file(f"[{datetime.now().isoformat()}] ERROR: {message}\n")

    def log_info(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#9ca3af;">[{ts}] ℹ️  {message}</span><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()
        self.log_to_file(f"[{datetime.now().isoformat()}] INFO: {message}")

    def _scroll_to_bottom(self):
        cursor = self.comms_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.comms_log.setTextCursor(cursor)

    def clear_screen_log(self):
        self.comms_log.clear()
        self.log_info("Screen cleared")

    # Cycle management
    def start_cycle(self):
        try:
            tm = get_terminal_manager()

            if self._is_ee_running():
                reply = QMessageBox.question(self, "Already Running", 
                    "Start NEW SPAWNING CYCLE?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._spawn_continuation(tm)
                return

            self._spawn_new_cycle(tm)

        except Exception as e:
            self.log_error(f"Start failed: {str(e)}")

    def _spawn_new_cycle(self, tm):
        token_target = self.token_target_spinbox.value()

        prompt = f"Library extraction - Cycle {self.current_cycle}.\nRead plans/NextSteps.md.\nToken target: {token_target}%"

        self.log_terminal_inject(f"cd {self.ee_root}", prompt)

        terminal_info = tm.spawn_claude_terminal(
            project_path=self.ee_root,
            session_id=f"ee_cycle_{self.current_cycle}",
            label=f"EE CYCLE {self.current_cycle}",
            position="left"
        )

        tm.inject_initialization_command(
            terminal_id=terminal_info["terminal_id"],
            session_id=f"ee_cycle_{self.current_cycle}",
            command=prompt
        )

        self.log_mm_send("ee_control", "proceed", {"token_target_pct": token_target})

        self.cycle_label.setText(f"Cycle: {self.current_cycle}")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("✅ Running")

        self.log_info(f"Spawned Cycle {self.current_cycle}")

    def _spawn_continuation(self, tm):
        self.current_cycle += 1
        token_target = self.token_target_spinbox.value()

        prompt = f"Continue - Cycle {self.current_cycle} (CONTINUATION).\nRead plans/NextSteps.md.\nToken target: {token_target}%"

        self.log_terminal_inject(f"cd {self.ee_root}", prompt)

        terminal_info = tm.spawn_claude_terminal(
            project_path=self.ee_root,
            session_id=f"ee_cycle_{self.current_cycle}_cont",
            label=f"EE CYCLE {self.current_cycle} - CONT",
            position="left"
        )

        tm.inject_initialization_command(
            terminal_id=terminal_info["terminal_id"],
            session_id=f"ee_cycle_{self.current_cycle}_cont",
            command=prompt
        )

        self.cycle_label.setText(f"Cycle: {self.current_cycle}")
        self.log_info(f"Spawned continuation {self.current_cycle}")

    def _is_ee_running(self) -> bool:
        if self.next_steps_file.exists():
            import os
            mtime = os.path.getmtime(self.next_steps_file)
            age = (datetime.now().timestamp() - mtime) / 60
            return age < 5
        return False

    def on_mm_message_received(self, message: dict):
        service = message.get("service", "unknown")
        action = message.get("action", "unknown")

        self.log_mm_receive(service, action, message)

        if action == "step_start":
            step = message.get("step")
            total = message.get("total_steps", 15)
            self.step_label.setText(f"Current: Step {step} of {total}")

        elif action == "step_complete":
            step = message.get("step")
            total = message.get("total_steps", 15)
            self.step_label.setText(f"Completed: Step {step} of {total}")

        elif action == "handoff":
            self.log_end_of_cycle(
                self.current_cycle,
                message.get("last_step"),
                message.get("next_step"),
                message.get("total_steps", 15),
                message.get("tokens_used", 0),
                message.get("tokens_limit", 200000)
            )
            self.current_cycle += 1
            self.cycle_label.setText(f"Cycle: {self.current_cycle}")
            self.start_btn.setEnabled(True)
            self.start_btn.setText("🚀 START NEXT CYCLE 🚀")

    def check_ee_status(self):
        if not self.next_steps_file.exists():
            return
        try:
            import re
            content = self.next_steps_file.read_text()
            next_match = re.search(r'\*\*Next step:\*\*\s*Step (\d+)', content)
            if next_match and "Current:" not in self.step_label.text():
                self.step_label.setText(f"Next: Step {next_match.group(1)} of 15")
        except:
            pass


def main():
    app = QApplication(sys.argv)
    window = EEMonitorWindow(Path(__file__).parent.parent)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
