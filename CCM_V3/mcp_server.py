#!/usr/bin/env python3
"""
MCP Server - Iteration 1 (KISS)

Simple MCP server with ONE tool: log_message
TCC sends messages, CCM logs them and resets watchdog.

Module Size Target: <150 lines
"""

import asyncio
import logging
from typing import Optional, Callable
from aiohttp import web

logger = logging.getLogger(__name__)


class MCPServer:
    """
    Simple MCP server for CCM ↔ TCC communication.

    Iteration 1: Monitor only (no control).
    Single tool: log_message
    """

    def __init__(
        self,
        port: int = 50001,
        on_message: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize MCP server.

        Args:
            port: HTTP server port
            on_message: Callback when message received (for GUI update)
        """
        self.port = port
        self.on_message = on_message
        self.server_loop = None
        self.server_runner = None
        logger.info(f"MCPServer initialized on port {port}")

    def start(self):
        """Start MCP server in background thread."""
        import threading

        def run_server():
            self.server_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.server_loop)

            app = web.Application()
            app.router.add_post('/mcp', self._handle_mcp)
            app.router.add_get('/health', self._handle_health)

            runner = web.AppRunner(app)
            self.server_loop.run_until_complete(runner.setup())
            self.server_runner = runner

            site = web.TCPSite(runner, 'localhost', self.port)
            self.server_loop.run_until_complete(site.start())

            logger.info(f"MCP server started on http://localhost:{self.port}/mcp")
            self.server_loop.run_forever()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info("MCP server thread started")

    async def _handle_health(self, request):
        """Health check endpoint."""
        return web.json_response({"status": "ok", "service": "ccm_mcp"})

    async def _handle_mcp(self, request):
        """
        Handle MCP JSON-RPC 2.0 requests.

        Supports:
        - tools/list: Return available tools
        - tools/call: Execute a tool
        """
        try:
            data = await request.json()
            method = data.get("method")

            if method == "tools/list":
                return await self._handle_tools_list(data)
            elif method == "tools/call":
                return await self._handle_tools_call(data)
            else:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })

        except Exception as e:
            logger.error(f"MCP request failed: {e}", exc_info=True)
            return web.json_response({
                "jsonrpc": "2.0",
                "id": data.get("id", None),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })

    async def _handle_tools_list(self, data):
        """Return list of available MCP tools."""
        return web.json_response({
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "log_message",
                        "description": "TCC sends a message to CCM for logging and monitoring",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Message from TCC"
                                }
                            },
                            "required": ["message"]
                        }
                    }
                ]
            }
        })

    async def _handle_tools_call(self, data):
        """Execute a tool."""
        params = data.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "log_message":
            result = await self._tool_log_message(tool_args)
        else:
            return web.json_response({
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            })

        return web.json_response({
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": result
        })

    async def _tool_log_message(self, args: dict):
        """
        Tool: log_message

        TCC sends a message to CCM.
        CCM logs it and resets watchdog timer.
        """
        message = args.get("message", "")

        logger.info(f"[MCP] TCC message: {message}")

        # Callback to GUI (thread-safe via Qt signal)
        if self.on_message:
            self.on_message(message)

        return {
            "success": True,
            "logged": message,
            "timestamp": asyncio.get_event_loop().time()
        }

    def stop(self):
        """Stop MCP server."""
        if self.server_loop and self.server_runner:
            async def shutdown():
                await self.server_runner.cleanup()

            asyncio.run_coroutine_threadsafe(shutdown(), self.server_loop)
            self.server_loop.call_soon_threadsafe(self.server_loop.stop)
            logger.info("MCP server stopped")
