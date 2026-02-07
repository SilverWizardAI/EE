#!/usr/bin/env python3
"""
MCP Stdio Access Proxy

Thin bridge between TCC (stdio) and Real MCP Server (Unix socket).
Spawned by TCC, forwards requests to Real MCP Server in CCM.

This is NOT an MCP server - it's an ACCESS PROXY to the real server.

Usage:
    python3 mcp_access_proxy.py <socket_path>

Where socket_path is the Unix socket of the Real MCP Server.
"""

import sys
import json
import socket
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Logging to stderr (stdout is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ACCESS PROXY] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class MCPAccessProxy:
    """
    MCP Stdio Access Proxy

    Bridges TCC's stdio communication to Real MCP Server's Unix socket.
    Implements standard MCP protocol on stdio side.
    """

    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.initialized = False
        self.protocol_version = "2025-06-18"

        logger.info(f"Access Proxy starting")
        logger.info(f"  Real MCP Server socket: {socket_path}")

    def send_response(self, response: Dict[str, Any]):
        """Send JSON-RPC response to TCC via stdout"""
        message = json.dumps(response)
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def send_error(self, request_id: Optional[int], code: int, message: str):
        """Send JSON-RPC error response"""
        self.send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        })

    def forward_to_real_server(self, method: str, message: str) -> Dict[str, Any]:
        """
        Forward request to Real MCP Server via Unix socket

        Args:
            method: MCP method (e.g., "log_message")
            message: Message parameter

        Returns:
            Response from Real MCP Server
        """
        try:
            # Connect to Real MCP Server
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(str(self.socket_path))

            # Send request (simplified protocol)
            request = {"method": method, "message": message}
            sock.sendall(json.dumps(request).encode('utf-8'))

            # Receive response
            data = sock.recv(65536)
            response = json.loads(data.decode('utf-8'))

            sock.close()
            return response

        except Exception as e:
            logger.error(f"Failed to forward to Real MCP Server: {e}")
            return {"success": False, "error": str(e)}

    def handle_initialize(self, request_id: int, params: Dict[str, Any]):
        """Handle MCP initialize request"""
        self.send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": self.protocol_version,
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "ccm-mcp-server",
                    "version": "1.0.0"
                }
            }
        })

    def handle_initialized(self, params: Dict[str, Any]):
        """Handle MCP initialized notification"""
        self.initialized = True
        logger.info("Initialized and ready")

    def handle_tools_list(self, request_id: int, params: Dict[str, Any]):
        """Return available tools"""
        self.send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [{
                    "name": "log_message",
                    "description": "Send message to CCM for logging and monitoring. Resets watchdog timer.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to log (e.g., 'Step 1 complete')"
                            }
                        },
                        "required": ["message"]
                    }
                }]
            }
        })

    def handle_tools_call(self, request_id: int, params: Dict[str, Any]):
        """Handle tool execution - forward to Real MCP Server"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name != "log_message":
            self.send_error(request_id, -32601, f"Unknown tool: {tool_name}")
            return

        message = arguments.get("message")
        if not message:
            self.send_error(request_id, -32602, "Missing parameter: message")
            return

        # Forward to Real MCP Server
        result = self.forward_to_real_server("log_message", message)

        if result.get("success"):
            self.send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"✅ Message logged: '{message}'"
                    }]
                }
            })
        else:
            error_msg = result.get("error", "Unknown error")
            self.send_error(request_id, -32603, f"Real MCP Server error: {error_msg}")

    def handle_request(self, request: Dict[str, Any]):
        """Route JSON-RPC request"""
        if request.get("jsonrpc") != "2.0":
            self.send_error(request.get("id"), -32600, "Invalid Request")
            return

        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            self.handle_initialize(request_id, params)
        elif method == "notifications/initialized":
            self.handle_initialized(params)
        elif method == "tools/list":
            if not self.initialized:
                self.send_error(request_id, -32002, "Not initialized")
                return
            self.handle_tools_list(request_id, params)
        elif method == "tools/call":
            if not self.initialized:
                self.send_error(request_id, -32002, "Not initialized")
                return
            self.handle_tools_call(request_id, params)
        else:
            self.send_error(request_id, -32601, f"Unknown method: {method}")

    def run(self):
        """Main stdio loop"""
        logger.info("Starting stdio loop")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON error: {e}")
                    self.send_error(None, -32700, str(e))
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
                    self.send_error(None, -32603, str(e))

        except KeyboardInterrupt:
            logger.info("Shutting down")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            logger.info("Access Proxy stopped")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mcp_access_proxy.py <socket_path>", file=sys.stderr)
        sys.exit(1)

    socket_path = Path(sys.argv[1])
    proxy = MCPAccessProxy(socket_path)
    proxy.run()


if __name__ == "__main__":
    main()
