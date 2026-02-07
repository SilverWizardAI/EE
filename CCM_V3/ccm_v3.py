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
    QLabel, QTextEdit, QGroupBox, QPushButton, QFileDialog
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor, QIcon, QPixmap, QPainter, QColor

# Add EE shared libraries to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from sw_core.terminal_manager import TerminalManager
from sw_core.settings_manager import SettingsManager

from mcp_server import MCPServer
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
        self.ccm_port = 50001
        self.watchdog_timeout_minutes = 2  # Short for testing

        # State
        self.project_dir = None
        self.tcc_session_id = None  # For terminal_manager.close_terminal()
        self.tcc_terminal_id = None  # For display only
        self.tcc_pid = None
        self.watchdog_deadline = None

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

        # MCP Server
        self.mcp_server = MCPServer(
            port=self.ccm_port,
            on_message=self._on_mcp_message
        )
        self.mcp_server.start()

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
        self._log(f"🌐 MCP server on http://localhost:{self.ccm_port}/mcp")
        self._log(f"📂 Select project directory to begin")

    def _build_gui(self):
        """Build simple single-panel GUI."""
        self.setWindowTitle(f"🖥️ CCM V3 - Iteration 1 (port {self.ccm_port})")

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

        self.mcp_label = QLabel(f"MCP Server: localhost:{self.ccm_port}")
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

        try:
            # Instrument project
            self._log("🔧 Instrumenting project...")
            TCCSetup.instrument_project(self.project_dir, self.ccm_port)
            self._log("✅ Project instrumented (MCP + SessionStart hook)")

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
            startup_prompt = "Read Plan.md and execute it immediately and completely."
            self.terminal_manager.inject_initialization_command(
                terminal_id=self.tcc_terminal_id,
                session_id=self.tcc_session_id,
                command=startup_prompt
            )
            self._log("✅ Startup prompt injected")

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

        # Reset watchdog
        if self.watchdog_deadline:
            self.watchdog_deadline = datetime.now() + timedelta(minutes=self.watchdog_timeout_minutes)
            self._log(f"⏱️  Watchdog reset to {self.watchdog_timeout_minutes:02d}:00")

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
        """Handle watchdog timeout - kill TCC."""
        self._log("⏰ WATCHDOG TIMEOUT - No messages for 2 minutes")
        self._log("🛑 Terminating TCC...")

        self._stop_tcc()

        self._log("✅ TCC terminated due to timeout")

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

        self.mcp_server.stop()
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
