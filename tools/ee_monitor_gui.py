#!/usr/bin/env python3
"""
CCM GUI - Heartbeat-Driven Protocol

Monitor actively polls EE instance (not passive waiting).
EE instance is purely reactive - responds only when prompted.

Features:
- Heartbeat protocol (configurable interval)
- MM mesh monitoring window
- Proper startup injection with register commands
- Terminal termination before new cycle

Module Size: ~650 lines
"""

import json
import sys
import subprocess
import time
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QGroupBox, QPushButton, QSpinBox, QMessageBox,
    QTabWidget, QComboBox
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from sw_core import get_terminal_manager

# Add MM mesh to path
mm_path = Path.home() / "Library/CloudStorage/Dropbox/A_Coding/MM"
if mm_path.exists():
    sys.path.insert(0, str(mm_path))
    try:
        from mcp_mesh.client import MeshClient
        MESH_CLIENT_AVAILABLE = True
    except ImportError:
        MESH_CLIENT_AVAILABLE = False
        MeshClient = None
else:
    MESH_CLIENT_AVAILABLE = False
    MeshClient = None


class EEMSignals(QObject):
    """Signals for thread-safe GUI updates."""
    message_received = pyqtSignal(str, str, dict)  # service, method, payload


class EEMRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for incoming messages to EEM."""

    window = None  # Will be set by EEMonitorWindow

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass

    def do_POST(self):
        """Handle tool calls - MM proxy routes by path /tools/{tool_name}."""
        try:
            # Parse tool name from path
            tool_name = self.path.split('/')[-1] if self.path.startswith('/tools/') else 'unknown'

            # Read arguments from body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            args = json.loads(body) if body else {}

            # Handle tools
            if tool_name == "log_message" and self.window:
                message = args.get("message", "")
                # Log via window (thread-safe)
                self.window.log_mm_receive("external", "log_message", {"message": message})

                response = {
                    "content": [{
                        "type": "text",
                        "text": f"✅ EEM received: {message}"
                    }]
                }
            elif tool_name == "end_cycle" and self.window:
                # End current cycle and start new one
                cycle_num = self.window.current_cycle
                self.window.log_mm_receive("external", "end_cycle", args)
                self.window.log_info(f"🔴 Cycle {cycle_num} ending - starting new cycle...")

                # Terminate current EE terminal and start new cycle
                # Use QTimer to run in GUI thread
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self.window._handle_cycle_end_and_restart())

                response = {
                    "content": [{
                        "type": "text",
                        "text": f"✅ Cycle {cycle_num} ended, starting Cycle {cycle_num + 1}"
                    }]
                }
            else:
                response = {
                    "content": [{
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }]
                }

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()


class EEMonitorWindow(QMainWindow):
    """CCM (Cycle Control Manager) with heartbeat-driven protocol."""

    def __init__(self, ee_root: Path):
        super().__init__()

        self.ee_root = ee_root
        self.next_steps_file = ee_root / "plans" / "NextSteps.md"
        self.current_cycle = 1
        self.ee_instance_name = None  # Current EE instance name (e.g., "ee_cycle_4")
        self.ee_terminal_id = None    # Current terminal ID for termination
        self.last_status = {}         # Last status from EE

        # Setup file logging
        self.log_dir = ee_root / "logs"
        self.log_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"ee_monitor_{today}.log"
        self.log_fh = open(self.log_file, 'a', encoding='utf-8')

        self.log_to_file(f"EEM: {'='*60}")
        self.log_to_file(f"CCM: CCM started at {datetime.now().isoformat()}")
        self.log_to_file(f"EEM: {'='*60}\n")

        # MM Mesh Setup with MeshClient
        self.mesh = None
        self.mm_connected = False

        if MESH_CLIENT_AVAILABLE and HTTPX_AVAILABLE:
            self.log_to_file("EEM: Checking if MM mesh is running...")

            if not self._check_mm_running():
                self.log_to_file("EEM: MM mesh NOT running - starting it...")
                if not self._start_mm_mesh():
                    self.log_to_file("EEM: ❌ Failed to start MM mesh!")
                else:
                    self.log_to_file("EEM: ✅ MM mesh started successfully")
            else:
                self.log_to_file("EEM: ✅ MM mesh already running")

            # Initialize MeshClient
            if self._check_mm_running():
                try:
                    self.mesh = MeshClient(proxy_host="localhost", proxy_port=6001)
                    self.mm_connected = True
                    self.log_to_file("EEM: ✅ MeshClient initialized")
                except Exception as e:
                    self.log_to_file(f"EEM: ⚠️ Failed to initialize MeshClient: {e}")
        else:
            reasons = []
            if not MESH_CLIENT_AVAILABLE:
                reasons.append("MeshClient not available")
            if not HTTPX_AVAILABLE:
                reasons.append("httpx not available")
            self.log_to_file(f"EEM: ⚠️ MM mesh integration disabled: {', '.join(reasons)}\n")

        # Start HTTP server to receive messages
        self.httpd = None
        if HTTPX_AVAILABLE and self._check_mm_running():
            try:
                self.httpd = HTTPServer(('localhost', 9999), EEMRequestHandler)
                EEMRequestHandler.window = self  # Pass reference to handler
                server_thread = threading.Thread(
                    target=self.httpd.serve_forever,
                    daemon=True,
                    name="EEM-HTTPServer"
                )
                server_thread.start()
                self.log_to_file("EEM: ✅ HTTP server started on port 9999")

                # Register with MM mesh
                if self._register_with_mm():
                    self.log_to_file("EEM: ✅ Ready to receive messages via MM mesh")
                else:
                    self.log_to_file("EEM: ⚠️ Registration with MM mesh failed")
            except Exception as e:
                self.log_to_file(f"EEM: ❌ Failed to start HTTP server: {e}")

        self.init_ui()

        # Heartbeat timer (polls EE instance for status)
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self._heartbeat_check)
        # Don't start until EE is running

        # MM stats monitoring (every 2 seconds)
        self.mm_stats_timer = QTimer(self)
        self.mm_stats_timer.timeout.connect(self._update_mm_status)
        self.mm_stats_timer.start(2000)
        self.mm_stats_file = Path.home() / ".mm_mesh_stats.json"

    def closeEvent(self, event):
        self.log_to_file(f"EEM: \n{'='*60}")
        self.log_to_file(f"CCM: CCM closed")
        self.log_to_file(f"EEM: {'='*60}\n")
        if hasattr(self, 'log_fh'):
            self.log_fh.close()
        event.accept()

    def log_to_file(self, text: str):
        """Log to file. Prefix with EEM: if not already prefixed."""
        if not text.startswith("EEM:") and not text.startswith("EE:"):
            self.log_fh.write(f"EEM: {text}\n")
        else:
            self.log_fh.write(f"{text}\n")
        self.log_fh.flush()

    def init_ui(self):
        self.setWindowTitle("🏛️ CCM")
        self.setGeometry(100, 100, 1000, 1200)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("🏛️ CCM")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # START BUTTON (always visible)
        self.start_btn = QPushButton("🚀 START CYCLE 🚀")
        self.start_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.start_btn.setMinimumHeight(60)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                color: white;
                padding: 15px;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #CC0000; }
        """)
        self.start_btn.clicked.connect(self.start_cycle)
        layout.addWidget(self.start_btn)

        # Plan Selector
        plan_group = QGroupBox("📋 Plan Selection")
        plan_layout = QHBoxLayout()

        plan_label = QLabel("Plan:")
        plan_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        plan_layout.addWidget(plan_label)

        self.plan_selector = QComboBox()
        self.plan_selector.setFont(QFont("Arial", 12))
        self.plan_selector.setMinimumHeight(35)
        self._load_available_plans()
        plan_layout.addWidget(self.plan_selector, 1)

        plan_group.setLayout(plan_layout)
        layout.addWidget(plan_group)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #666;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #444;
                color: white;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 5px;
                font-size: 12pt;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #FF0000;
            }
        """)

        # Monitor Tab
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)

        # Status Group (compact)
        status_group = QGroupBox("📊 Status")
        status_layout = QHBoxLayout()

        self.cycle_label = QLabel("Cycle: 1")
        self.cycle_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.cycle_label)

        status_layout.addSpacing(30)

        self.step_label = QLabel("Step: Waiting")
        self.step_label.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.step_label)

        status_layout.addStretch()

        status_group.setLayout(status_layout)
        monitor_layout.addWidget(status_group)

        # MM Monitoring Window (compact)
        mm_group = QGroupBox("🔗 MM Mesh")
        mm_layout = QVBoxLayout()

        self.mm_display = QTextEdit()
        self.mm_display.setReadOnly(True)
        self.mm_display.setMaximumHeight(80)
        self.mm_display.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: white;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
                padding: 5px;
            }
        """)
        mm_layout.addWidget(self.mm_display)

        mm_group.setLayout(mm_layout)
        monitor_layout.addWidget(mm_group)

        # Communications Log (70% of screen)
        log_group = QGroupBox("📡 Communications Log")
        log_layout = QVBoxLayout()

        self.comms_log = QTextEdit()
        self.comms_log.setReadOnly(True)
        self.comms_log.setMinimumHeight(700)  # 70% of 1000px height
        self.comms_log.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: white;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.comms_log)

        clear_btn = QPushButton("🗑️ Clear Log")
        clear_btn.setMinimumHeight(30)
        clear_btn.clicked.connect(self.clear_screen_log)
        log_layout.addWidget(clear_btn)

        log_group.setLayout(log_layout)
        monitor_layout.addWidget(log_group)

        # Add 20pt bottom border/spacing
        monitor_layout.addSpacing(20)

        self.tabs.addTab(monitor_tab, "📊 Monitor")

        # Settings Tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        # Configuration Group
        config_group = QGroupBox("⚙️ Cycle Configuration")
        config_layout = QVBoxLayout()

        # Token Threshold
        token_row = QHBoxLayout()
        token_label = QLabel("Token Threshold (before starting step):")
        token_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        token_row.addWidget(token_label)

        self.token_target_spinbox = QSpinBox()
        self.token_target_spinbox.setMinimum(20)
        self.token_target_spinbox.setMaximum(95)
        self.token_target_spinbox.setValue(35)  # Default: 35% threshold
        self.token_target_spinbox.setSuffix("%")
        self.token_target_spinbox.setFont(QFont("Arial", 12))
        token_row.addWidget(self.token_target_spinbox)
        token_row.addStretch()
        config_layout.addLayout(token_row)

        token_help = QLabel("At 35% (70K tokens), TCC stops before starting new step")
        token_help.setStyleSheet("color: #999; font-style: italic;")
        config_layout.addWidget(token_help)

        config_layout.addSpacing(20)

        # Heartbeat Interval
        heartbeat_row = QHBoxLayout()
        heartbeat_label = QLabel("Heartbeat Poll Interval:")
        heartbeat_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        heartbeat_row.addWidget(heartbeat_label)

        self.heartbeat_spinbox = QSpinBox()
        self.heartbeat_spinbox.setMinimum(30)
        self.heartbeat_spinbox.setMaximum(600)
        self.heartbeat_spinbox.setValue(120)  # Default 2 minutes
        self.heartbeat_spinbox.setSuffix(" sec")
        self.heartbeat_spinbox.setFont(QFont("Arial", 12))
        self.heartbeat_spinbox.valueChanged.connect(self._update_heartbeat_interval)
        heartbeat_row.addWidget(self.heartbeat_spinbox)
        heartbeat_row.addStretch()
        config_layout.addLayout(heartbeat_row)

        heartbeat_help = QLabel("How often EEM polls TCC for status updates")
        heartbeat_help.setStyleSheet("color: #999; font-style: italic;")
        config_layout.addWidget(heartbeat_help)

        config_group.setLayout(config_layout)
        settings_layout.addWidget(config_group)

        # Info Group
        info_group = QGroupBox("ℹ️ Information")
        info_layout = QVBoxLayout()

        info_text = QLabel("""
<b>Token Threshold:</b> TCC checks before EACH step<br>
• Below threshold: Start step<br>
• At/Above threshold: Close cycle gracefully<br>
<br>
<b>Examples (200K budget):</b><br>
• 25% = 50,000 tokens (conservative)<br>
• 35% = 70,000 tokens (default, balanced)<br>
• 50% = 100,000 tokens (aggressive)<br>
<br>
<b>Log File:</b> {0}
        """.format(self.log_file))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        info_layout.addWidget(info_text)

        info_group.setLayout(info_layout)
        settings_layout.addWidget(info_group)

        settings_layout.addStretch()

        self.tabs.addTab(settings_tab, "⚙️ Settings")

        layout.addWidget(self.tabs)

        self.log_info("CCM started")
        self.log_info(f"Log file: {self.log_file}")

    def _load_available_plans(self):
        """Load available plans from plans/ directory."""
        plans_dir = self.ee_root / "plans"

        # Default option
        self.plan_selector.addItem("NextSteps.md (Default)", "plans/NextSteps.md")

        # Load markdown plans from plans/ directory
        if plans_dir.exists():
            plan_files = sorted(plans_dir.glob("Plan*.md"))
            for plan_file in plan_files:
                plan_name = plan_file.name
                relative_path = f"plans/{plan_name}"
                self.plan_selector.addItem(plan_name, relative_path)

        # If no plans found, just use default
        if self.plan_selector.count() == 1:
            self.log_to_file("EEM: No Plan*.md files found in plans/ directory")

    # Logging methods
    def log_terminal_inject(self, command: str, prompt: str):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f'<span style="color:#3b82f6;font-weight:bold;">[{ts}] CYCLE {self.current_cycle} | TERMINAL INJECT</span><br>'
        html += f'<span style="color:#60a5fa;">  {command}</span><br>'
        html += f'<span style="color:#60a5fa;">  {prompt[:100]}...</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"EEM: [{full_ts}] CYCLE {self.current_cycle} | TERMINAL INJECT")
        self.log_to_file(f"EEM: Command: {command}")
        self.log_to_file(f"EEM: Prompt: {prompt}\n")

    def log_mm_send(self, service: str, method: str, payload: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f'<span style="color:#8b5cf6;font-weight:bold;">[{ts}] CYCLE {self.current_cycle} | MM SEND → {service}</span><br>'
        html += f'<span style="color:#a78bfa;">  {method}: {json.dumps(payload, indent=2)}</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"EEM: [{full_ts}] CYCLE {self.current_cycle} | MM SEND → {service}.{method}")
        self.log_to_file(f"EEM: Payload: {json.dumps(payload)}\n")

    def log_mm_receive(self, service: str, method: str, payload: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f'<span style="color:#10b981;font-weight:bold;">[{ts}] CYCLE {self.current_cycle} | MM RECV ← {service}</span><br>'
        html += f'<span style="color:#34d399;">  {method}: {json.dumps(payload, indent=2)}</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()

        self.log_to_file(f"EE: [{full_ts}] CYCLE {self.current_cycle} | MM RECV ← {service}.{method}")
        self.log_to_file(f"EE: Payload: {json.dumps(payload)}\n")

    def log_error(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#ef4444;font-weight:bold;">[{ts}] ❌ ERROR: {message}</span><br><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()
        self.log_to_file(f"EEM: [{datetime.now().isoformat()}] ERROR: {message}\n")

    def log_info(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#9ca3af;">[{ts}] ℹ️  {message}</span><br>'
        self.comms_log.append(html)
        self._scroll_to_bottom()
        self.log_to_file(f"EEM: [{datetime.now().isoformat()}] INFO: {message}")

    def _scroll_to_bottom(self):
        cursor = self.comms_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.comms_log.setTextCursor(cursor)

    def clear_screen_log(self):
        self.comms_log.clear()
        self.log_info("Screen cleared")

    # MM Mesh integration methods
    def _check_mm_running(self) -> bool:
        """Check if MM mesh is running on port 6001."""
        if not HTTPX_AVAILABLE:
            return False
        try:
            response = httpx.get("http://localhost:6001/services", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def _start_mm_mesh(self) -> bool:
        """Start MM mesh proxy in background."""
        try:
            mm_path = Path.home() / "Library/CloudStorage/Dropbox/A_Coding/MM"

            if not mm_path.exists():
                self.log_to_file(f"EEM: ❌ MM path not found: {mm_path}")
                return False

            subprocess.Popen(
                ["python3", "-m", "mcp_mesh.proxy.server",
                 "--http-only", "--http-port", "6001"],
                cwd=str(mm_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Wait for it to start (max 10 seconds)
            for i in range(20):
                time.sleep(0.5)
                if self._check_mm_running():
                    return True

            return False
        except Exception as e:
            self.log_to_file(f"EEM: Error starting MM: {e}")
            return False

    def _register_with_mm(self) -> bool:
        """Register EEM as a service with MM mesh."""
        if not HTTPX_AVAILABLE:
            return False
        try:
            response = httpx.post(
                "http://localhost:6001/register",
                json={
                    "instance_name": "ee_monitor",
                    "port": 9999,  # Different port from test monitor
                    "tools": ["log_message", "end_cycle"]  # Use strings, not objects!
                },
                timeout=5.0
            )
            if response.status_code == 200:
                self.log_to_file("EEM: ✅ Registered with MM mesh as 'ee_monitor'")
                return True
            else:
                self.log_to_file(f"EEM: Registration failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_to_file(f"EEM: Registration error: {e}")
            return False

    def _update_mm_status(self):
        """Update MM mesh status display."""
        if not HTTPX_AVAILABLE:
            self.mm_display.setPlainText("MM: httpx not available")
            return

        try:
            response = httpx.get("http://localhost:6001/services", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", [])

                lines = [f"MM Mesh: {len(services)} services registered"]
                lines.append("─" * 40)

                for svc in services:
                    name = svc.get("instance_name", "unknown")
                    tools_count = len(svc.get("tools", []))
                    status = svc.get("status", "unknown")
                    lines.append(f"  {name}: {tools_count} tools [{status}]")

                self.mm_display.setPlainText("\n".join(lines))
            else:
                self.mm_display.setPlainText(f"MM: Error {response.status_code}")
        except Exception as e:
            self.mm_display.setPlainText(f"MM: Connection error")

    def _update_heartbeat_interval(self, value: int):
        """Update heartbeat timer interval."""
        if self.heartbeat_timer.isActive():
            self.heartbeat_timer.setInterval(value * 1000)
            self.log_info(f"Heartbeat interval updated: {value}s")

    # Heartbeat Protocol
    def _heartbeat_check(self):
        """
        Heartbeat check - polls EE instance for status via MeshClient.

        This is the ONLY way status updates happen - EE is purely reactive.
        """
        if not self.ee_instance_name or not self.mesh:
            return

        try:
            # Call EE's get_status tool via MeshClient
            self.log_mm_send(self.ee_instance_name, "get_status", {})

            status = self.mesh.call_service(
                target_instance=self.ee_instance_name,
                tool_name="get_status",
                arguments={},
                timeout=10.0
            )

            # Success - process status
            self.log_mm_receive(self.ee_instance_name, "get_status", status)
            self._process_status_update(status)

        except Exception as e:
            error_str = str(e)
            self.log_error(f"Heartbeat failed: {error_str}")

            # Check if cycle is complete (service not found)
            if "not found" in error_str.lower() or "not available" in error_str.lower():
                self.log_info("EE instance no longer registered - cycle may be complete")
                self._handle_cycle_end()

    def _process_status_update(self, status: dict):
        """Process status update from EE."""
        step = status.get("step", "?")
        task = status.get("task", "Working")
        cycle_status = status.get("cycle_status", "running")

        # Update UI
        self.step_label.setText(f"Step {step}: {task}")

        # Check for step completion
        last_step = self.last_status.get("step")
        if last_step and last_step != step:
            self.log_info(f"✅ Step {last_step} complete, now on Step {step}")

        # Check for cycle completion
        if cycle_status == "complete":
            self._handle_cycle_end(status)

        self.last_status = status

    def _handle_cycle_end(self, final_status: dict = None):
        """Handle cycle completion."""
        self.log_info(f"🔴 Cycle {self.current_cycle} COMPLETE")

        if final_status:
            tokens = final_status.get("tokens_used", "?")
            progress = final_status.get("progress", "?")
            self.log_info(f"   Tokens: {tokens}, Progress: {progress}")

        # Stop heartbeat
        self.heartbeat_timer.stop()

        # 10-second observer window (user can see TCC final state)
        if self.ee_terminal_id:
            self.log_info("⏸️  Waiting 10 seconds (observer window)...")
            time.sleep(10)
            self._terminate_ee_terminal()

        # Enable start button for next cycle
        self.current_cycle += 1
        self.cycle_label.setText(f"Cycle: {self.current_cycle}")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 START NEXT CYCLE 🚀")

        self.ee_instance_name = None
        self.ee_terminal_id = None
        self.last_status = {}

    def _handle_cycle_end_and_restart(self):
        """Handle cycle end and automatically start next cycle."""
        try:
            # Log cycle end
            self.log_info(f"🔴 Ending Cycle {self.current_cycle}")

            # Stop heartbeat
            self.heartbeat_timer.stop()

            # 10-second observer window (user can see TCC final state)
            if self.ee_terminal_id:
                self.log_info("⏸️  Waiting 10 seconds (observer window)...")
                time.sleep(10)
                self._terminate_ee_terminal()
                time.sleep(1)  # Give it time to close

            # Increment cycle
            self.current_cycle += 1
            self.cycle_label.setText(f"Cycle: {self.current_cycle}")

            # Reset state
            self.ee_instance_name = None
            self.ee_terminal_id = None
            self.last_status = {}

            # Start new cycle
            self.log_info(f"🚀 Starting Cycle {self.current_cycle}")
            tm = get_terminal_manager()
            self._spawn_new_cycle(tm)

        except Exception as e:
            self.log_error(f"Failed to end cycle and restart: {e}")

    def _terminate_ee_terminal(self):
        """Terminate the EE terminal before starting new cycle."""
        try:
            tm = get_terminal_manager()

            if self.ee_terminal_id:
                self.log_info(f"Terminating terminal: {self.ee_terminal_id}")
                # Close the terminal
                tm.close_terminal(self.ee_terminal_id)
                self.log_info("✅ Terminal terminated")
        except Exception as e:
            self.log_error(f"Failed to terminate terminal: {e}")

    # Cycle management
    def start_cycle(self):
        """Start new EE cycle."""
        try:
            # Terminate previous terminal if exists
            if self.ee_terminal_id:
                self._terminate_ee_terminal()
                time.sleep(1)  # Give it time to close

            tm = get_terminal_manager()
            self._spawn_new_cycle(tm)

        except Exception as e:
            self.log_error(f"Start failed: {str(e)}")

    def _spawn_new_cycle(self, tm):
        """Spawn new EE cycle with proper initialization."""
        token_target = self.token_target_spinbox.value()
        self.ee_instance_name = f"ee_cycle_{self.current_cycle}"

        # Construct full prompt with MM mesh integration
        prompt = f"""EE Cycle {self.current_cycle} - Read plans/NextSteps.md
Token target: {token_target}%

CRITICAL FIRST STEP - Start HTTP Server for MM Mesh:
```python
from tools.ee_http_server import init_server, update_status
server = init_server(cycle_number={self.current_cycle})
# Server is now running as '{self.ee_instance_name}' on MM mesh
```

Throughout your work, update status:
```python
update_status(step=1, task="Description", progress="10%", tokens_used=15000)
update_status(step=2, task="Next task", progress="45%")
# When complete:
update_status(cycle_status="complete", progress="100%")
```

I (EEM) will poll your status every 30 seconds via MM mesh.
When you mark cycle_status="complete", I'll detect it and start the next cycle.

Now begin your work.
"""

        # Log what we're sending
        self.log_terminal_inject(
            f"cd {self.ee_root} && claude code",
            prompt
        )

        # Spawn terminal with initialization
        terminal_info = tm.spawn_claude_terminal(
            project_path=self.ee_root,
            session_id=self.ee_instance_name,
            label=f"EE CYCLE {self.current_cycle}",
            position="left"
        )

        self.ee_terminal_id = terminal_info["terminal_id"]

        # Inject initialization command
        tm.inject_initialization_command(
            terminal_id=self.ee_terminal_id,
            session_id=self.ee_instance_name,
            command=prompt
        )

        # Update UI
        self.cycle_label.setText(f"Cycle: {self.current_cycle}")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("✅ Running")

        # Start heartbeat timer
        interval_sec = self.heartbeat_spinbox.value()
        self.heartbeat_timer.start(interval_sec * 1000)

        self.log_info(f"🚀 Spawned Cycle {self.current_cycle}: {self.ee_instance_name}")
        self.log_info(f"📡 Heartbeat polling every {interval_sec}s via MM mesh")
        self.log_info(f"⏳ Waiting for EE to start HTTP server and register...")
        self.log_info(f"💡 EE will call: init_server(cycle_number={self.current_cycle})")


def main():
    app = QApplication(sys.argv)
    window = EEMonitorWindow(Path(__file__).parent.parent)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
