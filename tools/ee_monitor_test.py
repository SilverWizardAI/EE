#!/usr/bin/env python3
"""
EE Monitor - TEST MODE

Simple version that:
1. Registers with MM mesh
2. Exposes log_message tool
3. Logs all incoming messages
4. No cycle management, no polling - just listening
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Setup paths
ee_root = Path(__file__).parent.parent
log_dir = ee_root / "logs"
log_dir.mkdir(exist_ok=True)

# Log file
today = datetime.now().strftime("%Y%m%d")
log_file = log_dir / f"ee_monitor_test_{today}.log"


def log_message(msg: str):
    """Log to both console and file."""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


class EEMHandler(BaseHTTPRequestHandler):
    """HTTP handler for EEM test mode."""

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass

    def do_POST(self):
        """Handle tool calls - MM proxy routes by path /tools/{tool_name}."""
        try:
            # Parse path to get tool name
            tool_name = self.path.split('/')[-1] if self.path.startswith('/tools/') else 'unknown'

            # Read arguments from body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            args = json.loads(body) if body else {}

            log_message(f"📥 Tool: {tool_name}")
            log_message(f"   Args: {json.dumps(args, indent=2)}")

            # Handle log_message tool
            if tool_name == "log_message":
                message = args.get("message", "")
                log_message(f"💬 MESSAGE: {message}")

                response = {
                    "content": [{
                        "type": "text",
                        "text": f"✅ Logged: {message}"
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
            log_message(f"❌ Error handling request: {e}")
            self.send_response(500)
            self.end_headers()


def start_http_server(port: int = 9998):
    """Start HTTP server."""
    server = HTTPServer(('localhost', port), EEMHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log_message(f"✅ HTTP server started on port {port}")
    return server


def register_with_mm(port: int = 9998) -> bool:
    """Register with MM mesh."""
    try:
        import httpx

        response = httpx.post(
            "http://localhost:6001/register",
            json={
                "instance_name": "ee_monitor_test",
                "port": port,
                "tools": ["log_message"]
            },
            timeout=5.0
        )

        if response.status_code == 200:
            log_message("✅ Registered with MM mesh as 'ee_monitor_test'")
            return True
        else:
            log_message(f"❌ Registration failed: {response.status_code}")
            return False

    except ImportError:
        log_message("❌ httpx not available")
        return False
    except Exception as e:
        log_message(f"❌ Registration error: {e}")
        return False


def main():
    """Run EEM test mode."""
    log_message("=" * 60)
    log_message("EE Monitor - TEST MODE")
    log_message("=" * 60)
    log_message(f"Log file: {log_file}")
    log_message("")

    # Start HTTP server
    port = 9998
    server = start_http_server(port)

    # Register with MM
    if not register_with_mm(port):
        log_message("⚠️  Failed to register with MM mesh")
        log_message("   Make sure MM mesh is running on port 6001")
        sys.exit(1)

    log_message("")
    log_message("🎯 Ready to receive messages!")
    log_message("   Test with: mesh.call_service('ee_monitor_test', 'log_message', {'message': 'Hello'})")
    log_message("")
    log_message("Press Ctrl+C to stop")
    log_message("")

    try:
        # Keep running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("")
        log_message("=" * 60)
        log_message("EE Monitor TEST stopped")
        log_message("=" * 60)
        server.shutdown()


if __name__ == "__main__":
    main()
