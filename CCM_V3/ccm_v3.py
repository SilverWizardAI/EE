#!/usr/bin/env python3
"""
CCM V3 - Iteration 1 (KISS)

Claude Code Monitor - Simple MCP monitoring.
Proves basic TCC ↔ CCM communication works.

Features:
- Project directory picker
- TCC spawning via terminal_manager
- Watchdog timer (2 minutes for testing)
- MCP server (1 tool: log_message)
- Settings persistence
- Persistent logging (GUI + file)

Module Size Target: <350 lines
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QGroupBox, QPushButton, QFileDialog, QComboBox,
    QMessageBox
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor, QIcon, QPixmap, QPainter, QColor

# Add EE shared libraries to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from sw_core.terminal_manager import TerminalManager
from sw_core.settings_manager import SettingsManager

from mcp_real_server import RealMCPServer
from tcc_setup import TCCSetup


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_ccm_icon():
    """Create custom CCM icon with green background and white text."""
    # Create a 128x128 pixmap
    pixmap = QPixmap(128, 128)
    pixmap.fill(QColor("#2E7D32"))  # Green background (Material Design Green 700)

    # Draw CCM text
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("white"))
    font = QFont("Arial", 48, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "CCM")
    painter.end()

    return QIcon(pixmap)


class CCMSignals(QObject):
    """Qt signals for thread-safe GUI updates."""
    tcc_message = pyqtSignal(str)  # Message from TCC


class CCMWindow(QMainWindow):
    """
    CCM V3 - Iteration 1

    Simple monitoring: TCC sends messages, CCM logs them.
    """

    def __init__(self):
        super().__init__()

        # Configuration
        self.watchdog_timeout_minutes = 2  # Short for testing

        # MCP Real Server socket path (unique per CCM instance)
        import uuid
        session_id = uuid.uuid4().hex[:8]
        self.mcp_socket_path = Path(f"/tmp/ccm_session_{session_id}.sock")

        # State
        self.project_dir = None
        self.tcc_session_id = None  # For terminal_manager.close_terminal()
        self.tcc_terminal_id = None  # For display only
        self.tcc_pid = None
        self.watchdog_deadline = None

        # Multi-cycle orchestration
        self.current_cycle = 0  # 0 = not started, 1+ = cycle number
        self.plan_active = False  # True when plan is being executed
        self.selected_plan = None  # Selected plan file name (e.g., "Plan_2.md")

        # Watchdog evidence tracking
        self.last_message = None  # Last message received from TCC
        self.last_message_time = None  # Timestamp of last message

        # Logging
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"ccm_{today}.log"
        self.log_fh = open(self.log_file, 'a', encoding='utf-8')

        # Components
        self.settings = SettingsManager("SilverWizard", "CCM_V3")
        self.terminal_manager = TerminalManager()
        self.signals = CCMSignals()
        self.signals.tcc_message.connect(self._handle_tcc_message)

        # Real MCP Server (background thread)
        self.mcp_real_server = RealMCPServer(
            socket_path=self.mcp_socket_path,
            on_message=self._on_mcp_message
        )
        self.mcp_real_server.start()

        # Build GUI
        self._build_gui()

        # Watchdog timer (1 second updates)
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.timeout.connect(self._check_watchdog)
        self.watchdog_timer.start(1000)

        # Load last project
        self._load_settings()

        # Startup message
        self._log("✅ CCM V3 - Iteration 1 started")
        self._log(f"🌐 Real MCP Server: {self.mcp_socket_path}")
        self._log(f"📂 Select project directory to begin")

    def _build_gui(self):
        """Build simple single-panel GUI."""
        self.setWindowTitle(f"🖥️ CCM V3 - Iteration 1 (MCP via Unix socket)")

        # Set custom icon
        self.setWindowIcon(create_ccm_icon())

        # Get screen geometry and position on left half
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        half_width = screen.width() // 2

        # Position window on left half of screen
        self.setGeometry(0, 0, half_width, screen.height())

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Add bottom margin to prevent log from running to screen edge
        layout.setContentsMargins(10, 10, 10, 40)  # left, top, right, bottom

        # Header
        header = QLabel("🖥️ CCM V3 - Iteration 1 (KISS)")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Project selection
        proj_group = QGroupBox("📂 Project")
        proj_layout = QVBoxLayout()

        self.project_label = QLabel("No project selected")
        self.project_label.setStyleSheet("color: #888; font-style: italic;")
        proj_layout.addWidget(self.project_label)

        self.select_btn = QPushButton("📂 Select Project Directory")
        self.select_btn.setMinimumHeight(40)
        self.select_btn.clicked.connect(self._select_project)
        proj_layout.addWidget(self.select_btn)

        proj_group.setLayout(proj_layout)
        layout.addWidget(proj_group)

        # Plan selection
        plan_group = QGroupBox("📋 Test Plan")
        plan_layout = QVBoxLayout()

        self.plan_combo = QComboBox()
        self.plan_combo.setMinimumHeight(35)
        self.plan_combo.currentTextChanged.connect(self._on_plan_selected)
        plan_layout.addWidget(self.plan_combo)

        self.plan_description = QLabel("No plan selected")
        self.plan_description.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        self.plan_description.setWordWrap(True)
        plan_layout.addWidget(self.plan_description)

        plan_group.setLayout(plan_layout)
        layout.addWidget(plan_group)

        # Status
        status_group = QGroupBox("📊 Status")
        status_layout = QVBoxLayout()

        self.tcc_status_label = QLabel("TCC: Not running")
        self.tcc_status_label.setFont(QFont("Courier", 11))
        status_layout.addWidget(self.tcc_status_label)

        self.watchdog_label = QLabel("Watchdog: --:--")
        self.watchdog_label.setFont(QFont("Courier", 11))
        self.watchdog_label.setStyleSheet("color: gray;")
        status_layout.addWidget(self.watchdog_label)

        self.mcp_label = QLabel(f"MCP Server: {self.mcp_socket_path.name}")
        self.mcp_label.setFont(QFont("Courier", 11))
        status_layout.addWidget(self.mcp_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Controls
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("🚀 START TCC")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.start_btn.clicked.connect(self._start_tcc)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("🛑 STOP TCC")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.stop_btn.clicked.connect(self._stop_tcc)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        layout.addLayout(control_layout)

        # Log
        log_group = QGroupBox("📝 Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: #00ff00;
                padding: 10px;
                padding-bottom: 30px;
            }
        """)
        log_layout.addWidget(self.log_text)

        clear_btn = QPushButton("🗑️ Clear Log")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Load available plans (after all widgets created)
        self._load_plans()

    def _load_settings(self):
        """Load persisted settings."""
        last_project = self.settings.get("last_project_path")
        if last_project and Path(last_project).exists():
            self.project_dir = Path(last_project)
            self.project_label.setText(f"✅ {self.project_dir}")
            self.project_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.start_btn.setEnabled(True)
            self._log(f"📂 Loaded last project: {self.project_dir.name}")

    def _save_settings(self):
        """Save current settings."""
        if self.project_dir:
            self.settings.set("last_project_path", str(self.project_dir))

    def _load_plans(self):
        """Load available plans from plans directory."""
        plans_dir = Path(__file__).parent / "plans"
        if not plans_dir.exists():
            self.plan_combo.addItem("No plans available")
            return

        # Find all plan files
        plan_files = sorted(plans_dir.glob("Plan_*.md"))
        if not plan_files:
            self.plan_combo.addItem("No plans available")
            return

        # Add plans to combo box
        for plan_file in plan_files:
            metadata = self._parse_plan_metadata(plan_file)
            display_name = f"{plan_file.stem} - {metadata['status']}"
            self.plan_combo.addItem(display_name, userData=plan_file.name)

        # Select first active plan (or first plan if none active)
        for i in range(self.plan_combo.count()):
            if "Active" in self.plan_combo.itemText(i) or "ACTIVE" in self.plan_combo.itemText(i):
                self.plan_combo.setCurrentIndex(i)
                break

    def _parse_plan_metadata(self, plan_file: Path) -> dict:
        """Parse plan file to extract metadata."""
        try:
            content = plan_file.read_text()
            lines = content.split('\n')

            metadata = {
                'title': plan_file.stem,
                'status': 'Unknown',
                'objective': 'No description available',
                'steps': 'Unknown',
                'cycles': 'Unknown'
            }

            # Parse metadata from plan file
            for i, line in enumerate(lines[:30]):  # Check first 30 lines
                if line.startswith('**Status:**'):
                    metadata['status'] = line.split('**Status:**')[1].strip()
                elif line.startswith('**Objective:**'):
                    metadata['objective'] = line.split('**Objective:**')[1].strip()
                elif line.startswith('**Total Steps:**'):
                    metadata['steps'] = line.split('**Total Steps:**')[1].strip()
                elif line.startswith('**Cycles:**'):
                    metadata['cycles'] = line.split('**Cycles:**')[1].strip()

            return metadata

        except Exception as e:
            logger.error(f"Failed to parse plan metadata: {e}")
            return {
                'title': plan_file.stem,
                'status': 'Unknown',
                'objective': 'Failed to read plan',
                'steps': 'Unknown',
                'cycles': 'Unknown'
            }

    def _on_plan_selected(self, text: str):
        """Handle plan selection change."""
        if not text or text == "No plans available":
            self.selected_plan = None
            self.plan_description.setText("No plan selected")
            return

        # Get plan file name from combo box userData
        idx = self.plan_combo.currentIndex()
        plan_filename = self.plan_combo.itemData(idx)
        self.selected_plan = plan_filename

        # Load and display plan metadata
        plans_dir = Path(__file__).parent / "plans"
        plan_file = plans_dir / plan_filename
        metadata = self._parse_plan_metadata(plan_file)

        # Format description
        description = (
            f"<b>Status:</b> {metadata['status']}<br>"
            f"<b>Steps:</b> {metadata['steps']} | <b>Cycles:</b> {metadata['cycles']}<br>"
            f"<b>Objective:</b> {metadata['objective']}"
        )
        self.plan_description.setText(description)

        self._log(f"📋 Plan selected: {plan_filename}")

    def _select_project(self):
        """Let user select project directory."""
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            str(self.project_dir or Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if not project_dir:
            return

        self.project_dir = Path(project_dir)
        self.project_label.setText(f"✅ {self.project_dir}")
        self.project_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.start_btn.setEnabled(True)

        self._save_settings()
        self._log(f"✅ Project selected: {self.project_dir.name}")

    def _start_tcc(self):
        """Start TCC - instrument project and spawn terminal."""
        if not self.project_dir:
            self._log("❌ No project selected")
            return

        if not self.selected_plan:
            self._log("❌ No plan selected")
            return

        try:
            # Instrument project
            self._log(f"🔧 Instrumenting project with {self.selected_plan}...")
            TCCSetup.instrument_project(
                self.project_dir,
                self.mcp_socket_path,
                plan_file=self.selected_plan
            )
            self._log(f"✅ Project instrumented (MCP + SessionStart hook + {self.selected_plan})")

            # Spawn terminal
            self._log("🚀 Spawning TCC terminal...")
            result = self.terminal_manager.spawn_claude_terminal(
                project_path=self.project_dir,
                session_id="tcc_session",
                label="TCC - Target CC"
            )

            self.tcc_session_id = result["session_id"]  # For close_terminal()
            self.tcc_terminal_id = result["terminal_id"]  # For display
            self.tcc_pid = result["pid"]

            self._log(f"✅ TCC spawned (PID: {self.tcc_pid})")
            self.tcc_status_label.setText(f"TCC: Running (PID: {self.tcc_pid})")
            self.tcc_status_label.setStyleSheet("color: #4CAF50;")

            # Inject startup prompt (C3 pattern)
            self._log("📝 Injecting startup prompt...")

            # Increment cycle counter
            self.current_cycle += 1
            self.plan_active = True

            # Cycle-aware startup prompt
            if self.current_cycle == 1:
                startup_prompt = "You are Cycle 1. Read Plan.md and execute it from the beginning."
            else:
                startup_prompt = f"You are Cycle {self.current_cycle}. Read Plan.md and Next_Steps.md. Continue from the next step indicated in Next_Steps.md."

            self.terminal_manager.inject_initialization_command(
                terminal_id=self.tcc_terminal_id,
                session_id=self.tcc_session_id,
                command=startup_prompt
            )
            self._log(f"✅ Startup prompt injected (Cycle {self.current_cycle})")

            # Start watchdog
            self.watchdog_deadline = datetime.now() + timedelta(minutes=self.watchdog_timeout_minutes)
            self._log(f"⏱️  Watchdog started ({self.watchdog_timeout_minutes} minutes)")

            # Update buttons
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

        except Exception as e:
            self._log(f"❌ Failed to start TCC: {e}")
            logger.error(f"TCC start failed: {e}", exc_info=True)

    def _stop_tcc(self):
        """Stop TCC - terminate terminal."""
        if not self.tcc_session_id:
            self._log("⚠️  No TCC running")
            return

        try:
            self._log("🛑 Stopping TCC...")
            self.terminal_manager.close_terminal(self.tcc_session_id)
            self._log(f"✅ TCC terminated (PID: {self.tcc_pid})")

            self._reset_tcc_state()

        except Exception as e:
            self._log(f"⚠️  Failed to stop TCC: {e}")
            logger.error(f"TCC stop failed: {e}", exc_info=True)

    def _reset_tcc_state(self):
        """Reset TCC state after termination."""
        self.tcc_session_id = None
        self.tcc_terminal_id = None
        self.tcc_pid = None
        self.watchdog_deadline = None

        self.tcc_status_label.setText("TCC: Not running")
        self.tcc_status_label.setStyleSheet("color: gray;")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_mcp_message(self, message: str):
        """Callback from MCP server (runs in MCP thread)."""
        # Emit signal for thread-safe GUI update
        self.signals.tcc_message.emit(message)

    def _handle_tcc_message(self, message: str):
        """Handle TCC message (runs in Qt main thread)."""
        self._log(f"📨 TCC: '{message}'")

        # Track last message for evidence
        self.last_message = message
        self.last_message_time = datetime.now()

        # Check for special orchestration messages
        if message.startswith("End of Cycle "):
            self._handle_end_of_cycle(message)
            return

        if message == "Plan Fully Executed":
            self._handle_plan_complete()
            return

        # Reset watchdog for normal messages
        if self.watchdog_deadline:
            self.watchdog_deadline = datetime.now() + timedelta(minutes=self.watchdog_timeout_minutes)
            self._log(f"⏱️  Watchdog reset to {self.watchdog_timeout_minutes:02d}:00")

    def _handle_end_of_cycle(self, message: str):
        """Handle 'End of Cycle X' message - terminate and spawn next cycle."""
        # Extract cycle number from message (format: "End of Cycle 1")
        try:
            cycle_num = int(message.split()[-1])
        except (ValueError, IndexError):
            self._log(f"⚠️  Invalid End of Cycle message: {message}")
            return

        self._log(f"🔄 End of Cycle {cycle_num} received")
        self._log(f"🛑 Terminating TCC for cycle transition...")

        # Stop current TCC
        self._stop_tcc()

        # Brief delay to ensure clean termination
        QTimer.singleShot(1000, self._start_tcc)  # Restart after 1 second

        self._log(f"🚀 Cycle {cycle_num + 1} will start in 1 second...")

    def _handle_plan_complete(self):
        """Handle 'Plan Fully Executed' message - terminate and stop orchestration."""
        self._log("🎉 Plan Fully Executed!")
        self._log("🛑 Terminating TCC...")

        # Stop TCC
        self._stop_tcc()

        # Reset orchestration state
        self.plan_active = False
        self.current_cycle = 0

        self._log("✅ TCC terminated - Workflow complete")
        self._log("📊 Orchestration stopped - Ready for next plan")

    def _check_watchdog(self):
        """Check watchdog timer (called every second)."""
        if not self.watchdog_deadline:
            self.watchdog_label.setText("Watchdog: --:--")
            self.watchdog_label.setStyleSheet("color: gray;")
            return

        remaining = (self.watchdog_deadline - datetime.now()).total_seconds()

        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            self.watchdog_label.setText(f"Watchdog: {mins:02d}:{secs:02d}")

            if remaining > 60:
                self.watchdog_label.setStyleSheet("color: green;")
            else:
                self.watchdog_label.setStyleSheet("color: orange;")
        else:
            # TIMEOUT!
            self.watchdog_label.setText("Watchdog: TIMEOUT!")
            self.watchdog_label.setStyleSheet("color: red;")
            self._handle_watchdog_timeout()

    def _handle_watchdog_timeout(self):
        """Handle watchdog timeout - ask user for confirmation before terminating."""
        self._log("⏰ WATCHDOG TIMEOUT - No messages for 2 minutes")

        # Gather evidence
        if self.last_message and self.last_message_time:
            elapsed = (datetime.now() - self.last_message_time).total_seconds()
            elapsed_mins = int(elapsed // 60)
            elapsed_secs = int(elapsed % 60)
            evidence = (
                f"Last message: \"{self.last_message}\"\n"
                f"Received: {self.last_message_time.strftime('%H:%M:%S')}\n"
                f"Time elapsed: {elapsed_mins}m {elapsed_secs}s\n"
                f"TCC PID: {self.tcc_pid}\n"
                f"Cycle: {self.current_cycle}"
            )
        else:
            evidence = (
                f"No messages received since startup\n"
                f"TCC PID: {self.tcc_pid}\n"
                f"Cycle: {self.current_cycle}"
            )

        # Log evidence
        self._log(f"📊 Evidence: Last message \"{self.last_message or 'None'}\" "
                  f"at {self.last_message_time.strftime('%H:%M:%S') if self.last_message_time else 'N/A'}")

        # Ask user for confirmation
        reply = QMessageBox.question(
            self,
            "⏰ Watchdog Timeout",
            f"TCC appears to be idle (no MCP messages for 2 minutes).\n\n"
            f"Evidence:\n{evidence}\n\n"
            f"TCC may still be working (thinking, reading files, etc.)\n"
            f"without sending progress messages.\n\n"
            f"What would you like to do?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Retry,
            QMessageBox.StandardButton.No
        )

        # Map buttons to actions
        reply.setButtonText(QMessageBox.StandardButton.Yes, "Terminate TCC")
        reply.setButtonText(QMessageBox.StandardButton.No, "Wait 2 More Minutes")
        reply.setButtonText(QMessageBox.StandardButton.Retry, "Disable Watchdog")

        if reply.button(reply.clickedButton()) == QMessageBox.StandardButton.Yes:
            # User confirmed termination
            self._log("👤 User confirmed: Terminating TCC")
            self._stop_tcc()
            self._log("✅ TCC terminated by user decision")

        elif clicked == disable_btn:
            # Disable watchdog
            self._log("👤 User chose: Disable watchdog")
            self.watchdog_deadline = None
            self.watchdog_label.setText("Watchdog: DISABLED")
            self.watchdog_label.setStyleSheet("color: gray;")
            self._log("⏱️  Watchdog disabled - TCC will run indefinitely")

        else:
            # Wait 2 more minutes
            self._log("👤 User chose: Wait 2 more minutes")
            self.watchdog_deadline = datetime.now() + timedelta(minutes=2)
            self.watchdog_label.setStyleSheet("color: #FFA500;")
            self._log("⏱️  Watchdog extended for 2 more minutes")

    def _log(self, message: str):
        """Log to GUI and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"

        # GUI - append and auto-scroll to bottom
        self.log_text.append(formatted)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        # Ensure scrollbar is at bottom (auto-scroll)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # File
        self.log_fh.write(formatted + "\n")
        self.log_fh.flush()

    def closeEvent(self, event):
        """Clean shutdown."""
        self._log("👋 CCM shutting down...")

        if self.tcc_session_id:
            self._stop_tcc()

        self.mcp_real_server.stop()
        self.log_fh.close()

        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application icon (appears in dock/taskbar)
    app.setWindowIcon(create_ccm_icon())

    window = CCMWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
