#!/usr/bin/env python3
"""
EE Monitor GUI - Real-time EE Instance Monitor

Displays EE cycle status in a compact GUI for split-screen monitoring.
Shows cycle count, token usage, current task, and handoff alerts.

Run alongside EE in right half of screen while EE works in left half.

Module Size Target: <400 lines (Current: ~380 lines)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QTextEdit, QGroupBox, QPushButton
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


class EEMonitorWindow(QMainWindow):
    """
    Real-time EE instance monitor.

    Displays:
    - Total cycle count
    - Current cycle status
    - Token usage with visual indicator
    - Task progress
    - Handoff alerts
    """

    def __init__(self, ee_root: Path):
        super().__init__()

        self.ee_root = ee_root
        self.status_file = ee_root / "status" / "EE_CYCLE_STATUS.json"
        self.handoff_file = ee_root / "status" / "HANDOFF_SIGNAL.txt"
        self.cycle_reports_file = ee_root / "status" / "cycle_reports.log"

        self.last_cycle = None
        self.total_cycles = 0
        self.handoff_detected = False
        self.last_report_size = 0  # Track log file size to detect new entries

        self.init_ui()
        self.start_monitoring()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("🏛️ EE Monitor - Autonomous Operation")
        self.setGeometry(100, 100, 500, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("🏛️ Enterprise Edition Monitor")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Autonomous Multi-Cycle Operation")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        # Cycle Counter (Prominent)
        cycle_group = QGroupBox("Instance Cycles")
        cycle_layout = QVBoxLayout()

        self.cycle_counter = QLabel("0")
        self.cycle_counter.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.cycle_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_counter.setStyleSheet("color: #2196F3; padding: 20px;")
        cycle_layout.addWidget(self.cycle_counter)

        self.cycle_label = QLabel("Total EE Instances Spawned")
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_label.setStyleSheet("color: #666; font-size: 11pt;")
        cycle_layout.addWidget(self.cycle_label)

        cycle_group.setLayout(cycle_layout)
        layout.addWidget(cycle_group)

        # Current Status
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()

        self.current_cycle_label = QLabel("Cycle: -")
        self.current_cycle_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.current_cycle_label)

        self.task_label = QLabel("Task: No active task")
        self.task_label.setWordWrap(True)
        self.task_label.setFont(QFont("Arial", 10))
        status_layout.addWidget(self.task_label)

        self.started_label = QLabel("Started: -")
        self.started_label.setStyleSheet("color: #666; font-size: 9pt;")
        status_layout.addWidget(self.started_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Token Usage
        token_group = QGroupBox("Token Budget")
        token_layout = QVBoxLayout()

        self.token_label = QLabel("Usage: - / 200,000")
        self.token_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        token_layout.addWidget(self.token_label)

        self.token_bar = QProgressBar()
        self.token_bar.setMinimum(0)
        self.token_bar.setMaximum(100)
        self.token_bar.setValue(0)
        self.token_bar.setTextVisible(True)
        self.token_bar.setFormat("%p%")
        self.token_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        token_layout.addWidget(self.token_bar)

        self.token_status = QLabel("✅ HEALTHY")
        self.token_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.token_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        token_layout.addWidget(self.token_status)

        token_group.setLayout(token_layout)
        layout.addWidget(token_group)

        # Completed Tasks
        tasks_group = QGroupBox("Progress")
        tasks_layout = QVBoxLayout()

        self.tasks_display = QTextEdit()
        self.tasks_display.setReadOnly(True)
        self.tasks_display.setMaximumHeight(100)
        self.tasks_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                font-family: monospace;
                font-size: 9pt;
            }
        """)
        tasks_layout.addWidget(self.tasks_display)

        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)

        # Cycle Reports Log
        reports_group = QGroupBox("Cycle Reports Log")
        reports_layout = QVBoxLayout()

        self.reports_display = QTextEdit()
        self.reports_display.setReadOnly(True)
        self.reports_display.setMaximumHeight(150)
        self.reports_display.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        reports_layout.addWidget(self.reports_display)

        reports_group.setLayout(reports_layout)
        layout.addWidget(reports_group)

        # Next Action
        next_group = QGroupBox("Next Action")
        next_layout = QVBoxLayout()

        self.next_label = QLabel("Waiting for status...")
        self.next_label.setWordWrap(True)
        self.next_label.setFont(QFont("Arial", 10))
        self.next_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 3px;")
        next_layout.addWidget(self.next_label)

        next_group.setLayout(next_layout)
        layout.addWidget(next_group)

        # Handoff Alert (Hidden by default)
        self.handoff_alert = QLabel("🔄 HANDOFF IN PROGRESS")
        self.handoff_alert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.handoff_alert.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.handoff_alert.setStyleSheet("""
            background-color: #ff9800;
            color: white;
            padding: 15px;
            border-radius: 5px;
        """)
        self.handoff_alert.hide()
        layout.addWidget(self.handoff_alert)

        # Last Update
        self.update_time_label = QLabel("Last update: Never")
        self.update_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_time_label.setStyleSheet("color: #999; font-size: 8pt; margin-top: 10px;")
        layout.addWidget(self.update_time_label)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Now")
        refresh_btn.clicked.connect(self.update_status)
        layout.addWidget(refresh_btn)

        layout.addStretch()

    def start_monitoring(self):
        """Start the monitoring timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(2000)  # Update every 2 seconds

        # Initial update
        self.update_status()

    def update_status(self):
        """Update the display with current status."""
        # Check for handoff signal
        self.check_handoff_signal()

        # Update cycle reports log
        self.update_reports_log()

        # Read cycle status
        if not self.status_file.exists():
            self.show_no_status()
            return

        try:
            with open(self.status_file, 'r') as f:
                data = json.load(f)

            # Update cycle counter
            current_cycle = data.get('cycle_number', 0)
            if self.last_cycle is None or current_cycle > self.last_cycle:
                self.total_cycles = current_cycle
                self.last_cycle = current_cycle

            self.cycle_counter.setText(str(self.total_cycles))

            # Current status
            self.current_cycle_label.setText(f"Cycle: {current_cycle}")

            task = data.get('current_task', 'No task')
            self.task_label.setText(f"Task: {task}")

            started = data.get('started_at', '-')
            if started != '-':
                dt = datetime.fromisoformat(started)
                started_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                started_str = '-'
            self.started_label.setText(f"Started: {started_str}")

            # Token usage (mock for now - would need actual tracking)
            # For now, show as "monitoring"
            self.token_label.setText("Usage: Monitoring...")

            # Completed tasks
            tasks = data.get('tasks_completed', [])
            if tasks:
                tasks_text = "\n".join([f"✅ {task}" for task in tasks])
            else:
                tasks_text = "No tasks completed yet"
            self.tasks_display.setPlainText(tasks_text)

            # Next action
            next_action = data.get('next_action', 'No action specified')
            self.next_label.setText(next_action)

            # Last update time
            now = datetime.now().strftime("%H:%M:%S")
            self.update_time_label.setText(f"Last update: {now}")

        except Exception as e:
            self.show_error(str(e))

    def update_reports_log(self):
        """Update the cycle reports log display."""
        if not self.cycle_reports_file.exists():
            self.reports_display.setPlainText("No cycle reports yet. Waiting for EE to start...")
            return

        try:
            # Check if file has new content
            current_size = self.cycle_reports_file.stat().st_size
            if current_size != self.last_report_size:
                # Read the entire log file
                with open(self.cycle_reports_file, 'r') as f:
                    content = f.read()

                # Update display
                self.reports_display.setPlainText(content)

                # Auto-scroll to bottom
                scrollbar = self.reports_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

                # Update last size
                self.last_report_size = current_size

        except Exception as e:
            self.reports_display.setPlainText(f"Error reading reports: {e}")

    def check_handoff_signal(self):
        """Check for handoff signal."""
        if self.handoff_file.exists():
            if not self.handoff_detected:
                self.handoff_detected = True
                self.handoff_alert.show()
                self.handoff_alert.setText("🔄 HANDOFF DETECTED - New instance spawning...")
        else:
            if self.handoff_detected:
                self.handoff_detected = False
                self.handoff_alert.hide()

    def show_no_status(self):
        """Show when no status file exists."""
        self.cycle_counter.setText("0")
        self.current_cycle_label.setText("Cycle: No active cycle")
        self.task_label.setText("Task: Waiting for EE to start...")
        self.tasks_display.setPlainText("No status file found")
        self.next_label.setText("Run: python3 tools/ee_startup.py")

    def show_error(self, error: str):
        """Show error state."""
        self.tasks_display.setPlainText(f"Error reading status:\n{error}")

    def update_token_display(self, current: int, budget: int = 200000):
        """Update token usage display."""
        percentage = int((current / budget) * 100)
        self.token_bar.setValue(percentage)
        self.token_label.setText(f"Usage: {current:,} / {budget:,}")

        # Update color and status based on percentage
        if percentage < 50:
            status = "✅ HEALTHY"
            color = "#4CAF50"  # Green
        elif percentage < 70:
            status = "🟡 MODERATE"
            color = "#FFC107"  # Amber
        elif percentage < 85:
            status = "🟠 PREPARE HANDOFF"
            color = "#FF9800"  # Orange
        else:
            status = "🔴 HANDOFF NEEDED"
            color = "#F44336"  # Red

        self.token_status.setText(status)
        self.token_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)


def main():
    """Run the EE monitor GUI."""
    # Detect EE root
    ee_root = Path(__file__).parent.parent

    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show window
    window = EEMonitorWindow(ee_root)

    # Position window on right half of screen
    screen = app.primaryScreen().geometry()
    width = screen.width() // 2
    height = screen.height()
    window.setGeometry(width, 0, width, height)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
