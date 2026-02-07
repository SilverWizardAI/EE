#!/usr/bin/env python3
"""
MCP Server STDIO Wrapper Template

JSON-RPC 2.0 / MCP Protocol stdio transport wrapper for MCP servers.
Exposes MCP server commands via Model Context Protocol over stdio.

EXTRACTED FROM: C3 project (services/c3_mcp_server_stdio.py)
PROTOCOL: Model Context Protocol (MCP) v2025-06-18
TRANSPORT: stdio (newline-delimited JSON-RPC 2.0)

Usage:
    from mcp_server_template import ExampleMCPServer
    from mcp_server_stdio_wrapper import MCPStdioWrapper

    server = ExampleMCPServer(project_dir=Path.cwd())
    wrapper = MCPStdioWrapper(
        mcp_server=server,
        tool_name="example_command",
        server_name="example-server"
    )
    wrapper.run()

MCP Configuration (.mcp.json):
    {
      "mcpServers": {
        "example-server": {
          "command": "python3",
          "args": ["/path/to/mcp_server_stdio_wrapper.py"],
          "env": {
            "PROJECT_DIR": "/path/to/project"
          }
        }
      }
    }

References:
- https://modelcontextprotocol.io/docs/learn/architecture
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import the MCP server template
# Adjust this import based on your project structure
try:
    from library.mcp_server_template import MCPServerTemplate, StatusCode
except ImportError:
    # Fallback for when running as standalone
    from mcp_server_template import MCPServerTemplate, StatusCode


# Configure logging (to stderr, stdout is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class MCPStdioWrapper:
    """
    MCP stdio transport wrapper for MCP servers

    Implements:
    - JSON-RPC 2.0 message handling
    - MCP protocol lifecycle (initialize, initialized)
    - Tool discovery (tools/list)
    - Tool execution (tools/call)
    - Newline-delimited stdio transport
    """

    def __init__(
        self,
        mcp_server: MCPServerTemplate,
        tool_name: str = "command",
        server_name: str = "mcp-server",
        server_version: str = "1.0.0"
    ):
        """
        Initialize MCP stdio wrapper

        Args:
            mcp_server: MCP server instance to wrap
            tool_name: Name of the MCP tool (e.g., "c3_command", "my_command")
            server_name: Server name for MCP registration
            server_version: Server version
        """
        self.mcp_server = mcp_server
        self.tool_name = tool_name
        self.server_name = server_name
        self.server_version = server_version
        self.initialized = False
        self.protocol_version = "2025-06-18"

        logger.info(f"MCP STDIO Wrapper starting")
        logger.info(f"  Server: {self.server_name} v{self.server_version}")
        logger.info(f"  Tool: {self.tool_name}")
        logger.info(f"  Project: {self.mcp_server.project_dir}")

    def send_response(self, response: Dict[str, Any]):
        """
        Send JSON-RPC response to stdout

        Args:
            response: JSON-RPC response dict
        """
        message = json.dumps(response)
        sys.stdout.write(message + "\n")
        sys.stdout.flush()
        logger.debug(f"Sent: {message[:100]}...")

    def send_error(self, request_id: Optional[int], code: int, message: str, data: Any = None):
        """
        Send JSON-RPC error response

        Args:
            request_id: Request ID (None for parse errors)
            code: Error code
            message: Error message
            data: Additional error data
        """
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

        if data is not None:
            error_response["error"]["data"] = data

        self.send_response(error_response)

    def handle_initialize(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP initialize request

        Returns server capabilities and info
        """
        client_name = params.get('clientInfo', {}).get('name', 'unknown')
        logger.info(f"Received initialize request from {client_name}")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": self.protocol_version,
                "capabilities": {
                    "tools": {
                        "listChanged": False  # Our tools are static
                    }
                },
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version
                }
            }
        }

    def handle_initialized(self, params: Dict[str, Any]):
        """
        Handle MCP initialized notification

        Marks server as ready to receive requests
        """
        self.initialized = True
        logger.info("MCP server initialized and ready")

    def handle_tools_list(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/list request

        Returns available tools (single tool with command_code interface)
        """
        logger.debug("Handling tools/list request")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": self.tool_name,
                        "description": f"Execute {self.server_name} command with hex command code and parameters",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command_code": {
                                    "type": "integer",
                                    "description": "Hex command code (0x00-0xFF). Core commands: 0x00=PING, 0x01=GET_STATUS, 0x02=GET_AVAILABLE_COMMANDS, 0x03=LOG_MESSAGE",
                                    "minimum": 0,
                                    "maximum": 255
                                },
                                "params": {
                                    "type": "object",
                                    "description": "Command-specific parameters (varies by command_code)",
                                    "additionalProperties": True
                                }
                            },
                            "required": ["command_code"]
                        }
                    }
                ]
            }
        }

    def handle_tools_call(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/call request

        Routes to MCP server command execution
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        logger.info(f"Tool call: {tool_name} with args: {arguments}")

        if tool_name != self.tool_name:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

        # Extract command_code and params
        command_code = arguments.get("command_code")
        command_params = arguments.get("params", {})

        if command_code is None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: command_code"
                }
            }

        # Execute via MCP server
        try:
            response = self.mcp_server.execute_command(command_code, command_params)

            # Convert server response to MCP tool result
            if response["status"] == StatusCode.SUCCESS:
                result_text = json.dumps({
                    "status": response["status"],
                    "message": response["message"],
                    "data": response.get("data"),
                    "timestamp": response["timestamp"]
                }, indent=2)
            else:
                result_text = json.dumps({
                    "status": response["status"],
                    "message": response["message"],
                    "error_code": response["status"],
                    "timestamp": response["timestamp"]
                }, indent=2)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    def handle_request(self, request: Dict[str, Any]):
        """
        Route JSON-RPC request to appropriate handler

        Args:
            request: Parsed JSON-RPC request
        """
        jsonrpc_version = request.get("jsonrpc")
        if jsonrpc_version != "2.0":
            self.send_error(
                request.get("id"),
                -32600,
                "Invalid Request: jsonrpc must be '2.0'"
            )
            return

        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        logger.debug(f"Request: method={method}, id={request_id}")

        # Route to handler
        if method == "initialize":
            response = self.handle_initialize(request_id, params)
            self.send_response(response)

        elif method == "notifications/initialized":
            self.handle_initialized(params)
            # No response for notifications

        elif method == "tools/list":
            if not self.initialized:
                self.send_error(request_id, -32002, "Server not initialized")
                return
            response = self.handle_tools_list(request_id, params)
            self.send_response(response)

        elif method == "tools/call":
            if not self.initialized:
                self.send_error(request_id, -32002, "Server not initialized")
                return
            response = self.handle_tools_call(request_id, params)
            self.send_response(response)

        else:
            self.send_error(request_id, -32601, f"Method not found: {method}")

    def run(self):
        """
        Main stdio loop

        Reads newline-delimited JSON-RPC messages from stdin
        Writes responses to stdout
        """
        logger.info("Starting MCP stdio loop (reading from stdin)")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    self.handle_request(request)

                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    self.send_error(None, -32700, f"Parse error: {str(e)}")

                except Exception as e:
                    logger.error(f"Request handling error: {e}", exc_info=True)
                    self.send_error(None, -32603, f"Internal error: {str(e)}")

        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down")

        except Exception as e:
            logger.error(f"Fatal error in stdio loop: {e}", exc_info=True)

        finally:
            logger.info("MCP stdio server stopped")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """
    Main entry point for standalone execution

    Usage:
        python3 mcp_server_stdio_wrapper.py [project_dir]

    Or via MCP configuration:
        {
          "mcpServers": {
            "example-server": {
              "command": "python3",
              "args": ["/path/to/mcp_server_stdio_wrapper.py", "/path/to/project"]
            }
          }
        }
    """
    import os

    # Get project directory from args or environment
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    elif "PROJECT_DIR" in os.environ:
        project_dir = Path(os.environ["PROJECT_DIR"])
    else:
        project_dir = Path.cwd()

    logger.info(f"Starting MCP server with project_dir: {project_dir}")

    # Import and create server
    # Customize this for your server class
    from mcp_server_template import ExampleMCPServer

    server = ExampleMCPServer(project_dir)

    # Create wrapper and run
    wrapper = MCPStdioWrapper(
        mcp_server=server,
        tool_name="example_command",
        server_name="example-server",
        server_version="1.0.0"
    )

    wrapper.run()


if __name__ == "__main__":
    main()
