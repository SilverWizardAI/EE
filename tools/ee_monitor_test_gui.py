#!/usr/bin/env python3
"""EE Monitor TEST - Simple GUI to show incoming messages"""
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QFont

log_file = Path(__file__).parent.parent / "logs" / f"ee_monitor_test_{datetime.now().strftime('%Y%m%d')}.log"
log_file.parent.mkdir(exist_ok=True)

class Signals(QObject):
    message = pyqtSignal(str)

signals = Signals()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_POST(self):
        tool = self.path.split('/')[-1]
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        args = json.loads(body) if body else {}
        ts = datetime.now().strftime("%H:%M:%S")
        if tool == "log_message":
            msg = args.get("message", "")
            signals.message.emit(f"[{ts}] {msg}")
            with open(log_file, 'a') as f: f.write(f"[{ts}] {msg}\n")
            resp = {"content": [{"type": "text", "text": f"OK: {msg}"}]}
        else:
            resp = {"content": [{"type": "text", "text": f"Unknown: {tool}"}]}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EE Monitor TEST")
        self.setGeometry(100, 100, 800, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        title = QLabel("🧪 EE Monitor - TEST MODE")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        self.status = QLabel("Starting...")
        layout.addWidget(self.status)
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setStyleSheet("QTextEdit { background-color: black; color: #00ff00; font-family: 'Courier New'; font-size: 12pt; padding: 10px; }")
        layout.addWidget(self.display)
        signals.message.connect(self.display.append)
        threading.Thread(target=self.start_server, daemon=True).start()
    def start_server(self):
        try:
            srv = HTTPServer(('localhost', 9998), Handler)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            signals.message.emit("✅ HTTP server on port 9998")
            import httpx
            r = httpx.post("http://localhost:6001/register", json={"instance_name": "ee_monitor_test", "port": 9998, "tools": ["log_message"]}, timeout=5.0)
            if r.status_code == 200:
                signals.message.emit("✅ Registered with MM mesh")
                signals.message.emit("🎯 Ready!")
                self.status.setText("✅ Running")
            else:
                signals.message.emit(f"❌ Registration failed: {r.status_code}")
        except Exception as e:
            signals.message.emit(f"❌ Error: {e}")

app = QApplication(sys.argv)
win = Window()
win.show()
sys.exit(app.exec())
