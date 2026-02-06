#!/usr/bin/env python3
"""
EE HTTP Server - Simple HTTP server for MM mesh integration

Since MM mesh's HTTP routing is not fully implemented yet, this provides
a simple HTTP server that EE can run to handle tool calls from EEM.

Architecture:
- Finds available port (5000-5099)
- Registers with MM mesh proxy (HTTP port 6001)
- Runs HTTP server to handle tool calls
- Sends heartbeats to stay registered

Usage:
    from tools.ee_http_server import EEHTTPServer
    server = EEHTTPServer(cycle_number=4)
    server.start()  # Runs in background thread
    server.update_status(step=1, task="Working")
"""

import sys
import json
import logging
import threading
import socket
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class EERequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for EE tools"""

    def log_message(self, format, *args):
        """Override to use logging"""
        logger.debug(f"{self.address_string()} - {format % args}")

    def _send_json(self, status: int, data: Dict[str, Any]):
        """Send JSON response"""
        json_data = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data)
        self.wfile.flush()  # Ensure data is sent

    def _read_json(self) -> Dict[str, Any]:
        """Read JSON from request body"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode()) if body else {}

    def do_POST(self):
        """Handle POST requests"""
        logger.info(f"POST request to {self.path}")

        if self.path == '/tools/get_status':
            self._handle_get_status()
        elif self.path == '/tools/get_progress':
            self._handle_get_progress()
        elif self.path == '/tools/get_cycle_info':
            self._handle_get_cycle_info()
        else:
            logger.warning(f"Unknown endpoint: {self.path}")
            self._send_json(404, {"error": f"Unknown endpoint: {self.path}"})

    def _handle_get_status(self):
        """Handle get_status tool call"""
        try:
            logger.info("Handling get_status request")
            server = self.server.ee_server
            uptime = (datetime.now() - server.start_time).total_seconds()

            result = {
                "step": server.current_step,
                "task": server.current_task,
                "cycle_status": server.cycle_status,
                "progress": server.progress,
                "tokens_used": server.tokens_used,
                "instance": server.instance_name,
                "uptime_seconds": uptime,
                "completed_steps": server.completed_steps,
                "next_action": server.next_action
            }

            logger.info(f"Sending status response: {result}")
            self._send_json(200, result)
            logger.info("Status response sent successfully")
        except Exception as e:
            logger.error(f"get_status error: {e}", exc_info=True)
            try:
                self._send_json(500, {"error": str(e)})
            except Exception as e2:
                logger.error(f"Failed to send error response: {e2}")

    def _handle_get_progress(self):
        """Handle get_progress tool call"""
        try:
            server = self.server.ee_server

            result = {
                "cycle_number": server.cycle_number,
                "instance_name": server.instance_name,
                "current_step": server.current_step,
                "current_task": server.current_task,
                "status": server.cycle_status,
                "progress_percent": server.progress,
                "tokens_used": server.tokens_used,
                "steps_completed": len(server.completed_steps),
                "completed_steps": server.completed_steps,
                "next_action": server.next_action,
                "start_time": server.start_time.isoformat(),
                "uptime": (datetime.now() - server.start_time).total_seconds()
            }

            self._send_json(200, result)
        except Exception as e:
            logger.error(f"get_progress error: {e}")
            self._send_json(500, {"error": str(e)})

    def _handle_get_cycle_info(self):
        """Handle get_cycle_info tool call"""
        try:
            server = self.server.ee_server

            result = {
                "cycle_number": server.cycle_number,
                "instance_name": server.instance_name,
                "version": "1.0.0",
                "start_time": server.start_time.isoformat()
            }

            self._send_json(200, result)
        except Exception as e:
            logger.error(f"get_cycle_info error: {e}")
            self._send_json(500, {"error": str(e)})


class EEHTTPServer:
    """
    Simple HTTP server for EE to handle MM mesh tool calls

    Runs HTTP server on available port (5000-5099) and registers with MM mesh.
    """

    def __init__(self, cycle_number: int):
        """
        Initialize EE HTTP server

        Args:
            cycle_number: Current cycle number
        """
        self.cycle_number = cycle_number
        self.instance_name = f"ee_cycle_{cycle_number}"

        # Status tracking
        self.current_step = 0
        self.current_task = "Initializing"
        self.cycle_status = "running"
        self.progress = "0%"
        self.tokens_used = 0
        self.start_time = datetime.now()
        self.completed_steps = []
        self.next_action = "Starting up"

        # HTTP server (start at 5001 to avoid macOS Control Center on 5000)
        self.port = self._find_available_port(start=5001)
        self.httpd = None
        self.server_thread = None
        self.running = False

        # Heartbeat
        self.heartbeat_thread = None
        self.registered = False

        logger.info(f"EE HTTP Server initialized: {self.instance_name} on port {self.port}")

    def _find_available_port(self, start: int = 5000, end: int = 5099) -> int:
        """Find available port in range"""
        for port in range(start, end + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('localhost', port))
                sock.close()
                return port
            except OSError:
                continue
        raise RuntimeError(f"No available ports in range {start}-{end}")

    def update_status(
        self,
        step: Optional[int] = None,
        task: Optional[str] = None,
        cycle_status: Optional[str] = None,
        progress: Optional[str] = None,
        tokens_used: Optional[int] = None,
        next_action: Optional[str] = None
    ):
        """Update current status"""
        if step is not None and step != self.current_step:
            if self.current_step > 0:
                self.completed_steps.append({
                    "step": self.current_step,
                    "task": self.current_task,
                    "completed_at": datetime.now().isoformat()
                })
            self.current_step = step

        if task is not None:
            self.current_task = task
        if cycle_status is not None:
            self.cycle_status = cycle_status
        if progress is not None:
            self.progress = progress
        if tokens_used is not None:
            self.tokens_used = tokens_used
        if next_action is not None:
            self.next_action = next_action

    def _register_with_mesh(self) -> bool:
        """Register with MM mesh proxy"""
        if not httpx:
            logger.error("httpx not available")
            return False

        try:
            response = httpx.post(
                "http://localhost:6001/register",
                json={
                    "instance_name": self.instance_name,
                    "port": self.port,
                    "tools": ["get_status", "get_progress", "get_cycle_info"]
                },
                timeout=5.0
            )

            if response.status_code == 200:
                self.registered = True
                logger.info(f"✅ Registered {self.instance_name} with MM mesh (port {self.port})")
                return True
            else:
                logger.error(f"Registration failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False

    def _send_heartbeat(self):
        """Send heartbeat to MM mesh"""
        if not httpx or not self.registered:
            return

        try:
            response = httpx.post(
                "http://localhost:6001/heartbeat",
                json={"instance_name": self.instance_name},
                timeout=5.0
            )
            if response.status_code == 200:
                logger.debug(f"Heartbeat sent for {self.instance_name}")
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    def _heartbeat_loop(self):
        """Heartbeat loop (runs in background thread)"""
        while self.running:
            self._send_heartbeat()
            time.sleep(30)  # Heartbeat every 30 seconds

    def start(self):
        """Start HTTP server and register with mesh"""
        if self.running:
            logger.warning("Server already running")
            return

        # Create HTTP server
        self.httpd = HTTPServer(('localhost', self.port), EERequestHandler)
        self.httpd.ee_server = self  # Pass reference to handler

        self.running = True

        # Start HTTP server thread
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever,
            daemon=True,
            name=f"EEHTTPServer-{self.cycle_number}"
        )
        self.server_thread.start()
        logger.info(f"HTTP server started on port {self.port}")

        # Register with mesh
        if self._register_with_mesh():
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                daemon=True,
                name=f"EEHeartbeat-{self.cycle_number}"
            )
            self.heartbeat_thread.start()
            logger.info("Heartbeat thread started")

    def stop(self):
        """Stop server"""
        self.running = False
        self.cycle_status = "stopped"

        if self.httpd:
            self.httpd.shutdown()
            logger.info(f"HTTP server stopped: {self.instance_name}")


# Global instance
_current_server: Optional[EEHTTPServer] = None


def init_server(cycle_number: int) -> EEHTTPServer:
    """Initialize and start HTTP server for current cycle"""
    global _current_server

    if _current_server:
        logger.warning("Stopping previous server")
        _current_server.stop()

    _current_server = EEHTTPServer(cycle_number)
    _current_server.start()

    return _current_server


def get_server() -> Optional[EEHTTPServer]:
    """Get current HTTP server"""
    return _current_server


def update_status(**kwargs):
    """Update status on current server"""
    if _current_server:
        _current_server.update_status(**kwargs)
    else:
        logger.warning("No server initialized - status update ignored")


if __name__ == "__main__":
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="EE HTTP Server")
    parser.add_argument("--cycle", type=int, required=True, help="Cycle number")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    server = EEHTTPServer(args.cycle)
    server.start()

    print(f"✓ EE HTTP Server running: {server.instance_name}")
    print(f"  Port: {server.port}")
    print(f"  Registered with MM mesh")
    print(f"  Press Ctrl+C to stop")

    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while server.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()
