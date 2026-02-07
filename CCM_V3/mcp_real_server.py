#!/usr/bin/env python3
"""
Real MCP Server - Background thread in CCM

Listens on Unix socket for messages from MCP Stdio Access Proxy.
Processes log_message requests and notifies CCM GUI via callback.

This is the REAL MCP server - it does the actual work.
The Access Proxy is just a thin stdio bridge.
"""

import socket
import json
import logging
import threading
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class RealMCPServer(threading.Thread):
    """
    Real MCP Server - runs in background thread of CCM

    Listens on Unix socket for messages from Access Proxy.
    Optimized communication since both are our code.
    """

    def __init__(self, socket_path: Path, on_message: Callable[[str], None]):
        """
        Initialize Real MCP Server

        Args:
            socket_path: Unix socket path to listen on
            on_message: Callback when message received (called from this thread)
        """
        super().__init__(daemon=True)
        self.socket_path = socket_path
        self.on_message = on_message
        self.running = False
        self.server_socket = None

        logger.info(f"[Real MCP Server] Initialized on {socket_path}")

    def run(self):
        """Main server loop - runs in background thread"""
        self.running = True

        # Remove old socket if exists
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Create Unix socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(str(self.socket_path))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)  # Timeout for clean shutdown

        logger.info(f"[Real MCP Server] Listening on {self.socket_path}")

        while self.running:
            try:
                # Accept connection from Access Proxy
                conn, _ = self.server_socket.accept()

                # Handle request
                self._handle_connection(conn)

            except socket.timeout:
                continue  # Check running flag
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    logger.error(f"[Real MCP Server] Error: {e}", exc_info=True)

        # Cleanup
        if self.server_socket:
            self.server_socket.close()
        if self.socket_path.exists():
            self.socket_path.unlink()

        logger.info("[Real MCP Server] Stopped")

    def _handle_connection(self, conn: socket.socket):
        """
        Handle connection from Access Proxy

        Simple protocol:
        - Access Proxy sends JSON: {"method": "log_message", "message": "..."}
        - We process and send back: {"success": true}
        """
        try:
            # Read request (max 64KB)
            data = conn.recv(65536)
            if not data:
                return

            request = json.loads(data.decode('utf-8'))
            method = request.get("method")

            if method == "log_message":
                message = request.get("message", "")
                logger.info(f"[Real MCP Server] Received: {message}")

                # Call CCM callback (we're in background thread)
                if self.on_message:
                    self.on_message(message)

                # Send success response
                response = {"success": True, "message": "logged"}
                conn.sendall(json.dumps(response).encode('utf-8'))

            else:
                # Unknown method
                response = {"success": False, "error": f"Unknown method: {method}"}
                conn.sendall(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"[Real MCP Server] Connection error: {e}", exc_info=True)
            try:
                error_response = {"success": False, "error": str(e)}
                conn.sendall(json.dumps(error_response).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def stop(self):
        """Stop the server"""
        logger.info("[Real MCP Server] Stopping...")
        self.running = False
