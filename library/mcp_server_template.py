"""
MCP Server Template

Extensible MCP (Model Context Protocol) server with command handler registry pattern.
Add your own commands by registering handlers for specific command codes.

EXTRACTED FROM: C3 project (services/c3_mcp_server.py)
PATTERN: Telecom protocol design (hex command codes, handler registry)

Architecture:
- Single tool interface: your_command(command_code, params)
- Hex command codes organized by category (0x00-0xFF)
- Handler registry for extensibility
- Structured command/response with status codes
- Comprehensive logging

Usage:
    1. Subclass MCPServerTemplate
    2. Override _register_custom_handlers()
    3. Add your command handlers
    4. Use the STDIO wrapper to expose via MCP

Example:
    class MyMCPServer(MCPServerTemplate):
        def _register_custom_handlers(self):
            self.register_handler(0x10, self._handle_do_something)

        def _handle_do_something(self, params):
            return CommandResponse(
                status=StatusCode.SUCCESS,
                message="Did something!",
                data={"result": "..."}
            )

    # Start stdio server
    server = MyMCPServer(project_dir=Path.cwd())
    wrapper = MCPStdioWrapper(server, tool_name="my_command")
    wrapper.run()
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict


# ============================================================================
# STATUS CODES
# ============================================================================

class StatusCode:
    """Response status codes"""
    SUCCESS = 0x00
    INVALID_COMMAND = 0x01
    INVALID_PARAMS = 0x02
    FILE_NOT_FOUND = 0x03
    PARSE_ERROR = 0x04
    INTERNAL_ERROR = 0x05
    NOT_IMPLEMENTED = 0x06
    PERMISSION_DENIED = 0x07


# ============================================================================
# COMMAND CODE RANGES
# ============================================================================

class CommandRange:
    """
    Command code ranges organized by category

    Define your command ranges here. Each range should span 16 codes (0x00-0x0F).
    This organization makes it easy to understand command categories at a glance.
    """

    # Core/Meta Commands (0x00-0x0F)
    CORE_START = 0x00
    CORE_END = 0x0F

    # Custom Category 1 (0x10-0x1F)
    CATEGORY1_START = 0x10
    CATEGORY1_END = 0x1F

    # Custom Category 2 (0x20-0x2F)
    CATEGORY2_START = 0x20
    CATEGORY2_END = 0x2F

    # Custom Category 3 (0x30-0x3F)
    CATEGORY3_START = 0x30
    CATEGORY3_END = 0x3F

    # Add more as needed...


# ============================================================================
# CORE COMMAND CODES
# ============================================================================

class CoreCommand:
    """Core/meta command codes (0x00-0x0F)"""
    PING = 0x00                      # Health check
    GET_STATUS = 0x01                # Server status
    GET_AVAILABLE_COMMANDS = 0x02    # List registered commands
    LOG_MESSAGE = 0x03               # Log from client

    # Add more core commands as needed...


# ============================================================================
# REQUEST/RESPONSE STRUCTURES
# ============================================================================

@dataclass
class CommandRequest:
    """MCP command request structure"""
    command_code: int
    params: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class CommandResponse:
    """MCP command response structure"""
    status: int
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        result = {
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp
        }
        if self.data is not None:
            result["data"] = self.data
        return result


# Command handler type
CommandHandler = Callable[[Dict[str, Any]], CommandResponse]


# ============================================================================
# MCP SERVER TEMPLATE
# ============================================================================

class MCPServerTemplate:
    """
    Base MCP Server with command handler registry

    Subclass this and override _register_custom_handlers() to add your commands.
    """

    def __init__(self, project_dir: Path, server_name: str = "MCPServer"):
        """
        Initialize MCP server

        Args:
            project_dir: Project root directory
            server_name: Name for logging
        """
        self.project_dir = Path(project_dir)
        self.server_name = server_name
        self.output_dir = self.project_dir / ".mcp_server"

        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Handler registry: command_code -> handler function
        self._handlers: Dict[int, CommandHandler] = {}

        # Setup logging
        self._setup_logging()

        # Register core handlers
        self._register_core_handlers()

        # Register custom handlers (override this in subclass)
        self._register_custom_handlers()

        self.logger.info(f"{self.server_name} initialized")
        self.logger.info(f"Project: {self.project_dir}")
        self.logger.info(f"Output dir: {self.output_dir}")
        self.logger.info(f"Registered commands: {len(self._handlers)}")

    def _setup_logging(self):
        """Setup logging for MCP server"""
        log_file = self.output_dir / f"{self.server_name.lower()}.log"

        # Create logger
        self.logger = logging.getLogger(self.server_name)
        self.logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers
        if self.logger.handlers:
            return

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        # Console handler (stderr)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def register_handler(self, command_code: int, handler: CommandHandler):
        """
        Register a command handler

        Args:
            command_code: Command code (0x00-0xFF)
            handler: Handler function that takes params dict and returns CommandResponse

        Example:
            server.register_handler(0x10, self._handle_my_command)
        """
        if command_code in self._handlers:
            self.logger.warning(f"Overwriting handler for command 0x{command_code:02X}")

        self._handlers[command_code] = handler
        self.logger.debug(f"Registered handler for command 0x{command_code:02X}")

    def _register_core_handlers(self):
        """Register core/meta command handlers (0x00-0x0F)"""
        self.register_handler(CoreCommand.PING, self._handle_ping)
        self.register_handler(CoreCommand.GET_STATUS, self._handle_get_status)
        self.register_handler(CoreCommand.GET_AVAILABLE_COMMANDS, self._handle_get_available_commands)
        self.register_handler(CoreCommand.LOG_MESSAGE, self._handle_log_message)

    def _register_custom_handlers(self):
        """
        Override this method to register your custom command handlers

        Example:
            def _register_custom_handlers(self):
                self.register_handler(0x10, self._handle_my_command1)
                self.register_handler(0x11, self._handle_my_command2)
                self.register_handler(0x12, self._handle_my_command3)
        """
        pass  # Override in subclass

    def execute_command(self, command_code: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command via MCP interface

        This is the main entry point called by the MCP tool.

        Args:
            command_code: Command code (0x00-0xFF)
            params: Command parameters

        Returns:
            Response dictionary
        """
        # Create request object
        request = CommandRequest(command_code=command_code, params=params)

        self.logger.info(f"Executing command 0x{command_code:02X} with params: {params}")

        # Validate command code
        if command_code < 0 or command_code > 0xFF:
            response = CommandResponse(
                status=StatusCode.INVALID_COMMAND,
                message=f"Invalid command code: 0x{command_code:02X}"
            )
            self.logger.error(response.message)
            return response.to_dict()

        # Check if handler exists
        if command_code not in self._handlers:
            response = CommandResponse(
                status=StatusCode.NOT_IMPLEMENTED,
                message=f"Command 0x{command_code:02X} not implemented"
            )
            self.logger.warning(response.message)
            return response.to_dict()

        # Execute handler
        try:
            handler = self._handlers[command_code]
            response = handler(params)

            self.logger.info(f"Command 0x{command_code:02X} completed: {response.message}")
            return response.to_dict()

        except Exception as e:
            response = CommandResponse(
                status=StatusCode.INTERNAL_ERROR,
                message=f"Internal error: {str(e)}"
            )
            self.logger.error(f"Command 0x{command_code:02X} failed: {e}", exc_info=True)
            return response.to_dict()

    # ========================================================================
    # CORE COMMAND HANDLERS (0x00-0x0F)
    # ========================================================================

    def _handle_ping(self, params: Dict[str, Any]) -> CommandResponse:
        """Handle PING command (0x00)"""
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="pong",
            data={
                "server": self.server_name,
                "version": "1.0.0"
            }
        )

    def _handle_get_status(self, params: Dict[str, Any]) -> CommandResponse:
        """Handle GET_STATUS command (0x01)"""
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Server status retrieved",
            data={
                "project_dir": str(self.project_dir),
                "output_dir": str(self.output_dir),
                "registered_commands": len(self._handlers),
                "server_name": self.server_name
            }
        )

    def _handle_get_available_commands(self, params: Dict[str, Any]) -> CommandResponse:
        """Handle GET_AVAILABLE_COMMANDS command (0x02)"""
        # Group commands by range
        commands_by_range = {
            "core": [],
            "category1": [],
            "category2": [],
            "category3": [],
            "other": []
        }

        for code in sorted(self._handlers.keys()):
            hex_code = f"0x{code:02X}"

            if CommandRange.CORE_START <= code <= CommandRange.CORE_END:
                commands_by_range["core"].append(hex_code)
            elif CommandRange.CATEGORY1_START <= code <= CommandRange.CATEGORY1_END:
                commands_by_range["category1"].append(hex_code)
            elif CommandRange.CATEGORY2_START <= code <= CommandRange.CATEGORY2_END:
                commands_by_range["category2"].append(hex_code)
            elif CommandRange.CATEGORY3_START <= code <= CommandRange.CATEGORY3_END:
                commands_by_range["category3"].append(hex_code)
            else:
                commands_by_range["other"].append(hex_code)

        return CommandResponse(
            status=StatusCode.SUCCESS,
            message=f"Found {len(self._handlers)} registered commands",
            data={
                "total_commands": len(self._handlers),
                "commands_by_range": commands_by_range
            }
        )

    def _handle_log_message(self, params: Dict[str, Any]) -> CommandResponse:
        """Handle LOG_MESSAGE command (0x03)"""
        if "message" not in params:
            return CommandResponse(
                status=StatusCode.INVALID_PARAMS,
                message="Missing required parameter: message"
            )

        level = params.get("level", "info").upper()
        message = params["message"]

        # Log the message (to log file)
        if level == "DEBUG":
            self.logger.debug(f"[CLIENT] {message}")
        elif level == "INFO":
            self.logger.info(f"[CLIENT] {message}")
        elif level == "WARNING":
            self.logger.warning(f"[CLIENT] {message}")
        elif level == "ERROR":
            self.logger.error(f"[CLIENT] {message}")
        else:
            self.logger.info(f"[CLIENT] {message}")

        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Message logged"
        )


# ============================================================================
# EXAMPLE IMPLEMENTATION
# ============================================================================

class ExampleMCPServer(MCPServerTemplate):
    """
    Example MCP server implementation

    Shows how to subclass MCPServerTemplate and add custom commands.
    """

    def __init__(self, project_dir: Path):
        super().__init__(project_dir, server_name="ExampleMCPServer")

    def _register_custom_handlers(self):
        """Register example custom commands"""
        # Category 1 commands (0x10-0x1F)
        self.register_handler(0x10, self._handle_greet)
        self.register_handler(0x11, self._handle_calculate)

        # Category 2 commands (0x20-0x2F)
        self.register_handler(0x20, self._handle_list_files)

    def _handle_greet(self, params: Dict[str, Any]) -> CommandResponse:
        """
        Handle GREET command (0x10)

        Params:
            name: str - Name to greet

        Returns:
            Greeting message
        """
        if "name" not in params:
            return CommandResponse(
                status=StatusCode.INVALID_PARAMS,
                message="Missing required parameter: name"
            )

        name = params["name"]

        return CommandResponse(
            status=StatusCode.SUCCESS,
            message=f"Hello, {name}!",
            data={"name": name}
        )

    def _handle_calculate(self, params: Dict[str, Any]) -> CommandResponse:
        """
        Handle CALCULATE command (0x11)

        Params:
            a: float - First number
            b: float - Second number
            operation: str - Operation (add, subtract, multiply, divide)

        Returns:
            Calculation result
        """
        required = ["a", "b", "operation"]
        missing = [p for p in required if p not in params]

        if missing:
            return CommandResponse(
                status=StatusCode.INVALID_PARAMS,
                message=f"Missing required parameters: {', '.join(missing)}"
            )

        a = params["a"]
        b = params["b"]
        operation = params["operation"]

        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return CommandResponse(
                        status=StatusCode.INVALID_PARAMS,
                        message="Cannot divide by zero"
                    )
                result = a / b
            else:
                return CommandResponse(
                    status=StatusCode.INVALID_PARAMS,
                    message=f"Invalid operation: {operation}"
                )

            return CommandResponse(
                status=StatusCode.SUCCESS,
                message=f"Result: {result}",
                data={
                    "a": a,
                    "b": b,
                    "operation": operation,
                    "result": result
                }
            )

        except Exception as e:
            return CommandResponse(
                status=StatusCode.INTERNAL_ERROR,
                message=f"Calculation error: {str(e)}"
            )

    def _handle_list_files(self, params: Dict[str, Any]) -> CommandResponse:
        """
        Handle LIST_FILES command (0x20)

        Params:
            directory: str - Directory to list (optional, defaults to project_dir)
            pattern: str - Glob pattern (optional, defaults to "*")

        Returns:
            List of matching files
        """
        directory = Path(params.get("directory", self.project_dir))
        pattern = params.get("pattern", "*")

        # Make directory absolute if relative
        if not directory.is_absolute():
            directory = self.project_dir / directory

        # Check if directory exists
        if not directory.exists():
            return CommandResponse(
                status=StatusCode.FILE_NOT_FOUND,
                message=f"Directory not found: {directory}"
            )

        if not directory.is_dir():
            return CommandResponse(
                status=StatusCode.INVALID_PARAMS,
                message=f"Not a directory: {directory}"
            )

        try:
            # List matching files
            files = list(directory.glob(pattern))
            file_list = [
                {
                    "name": f.name,
                    "path": str(f),
                    "is_file": f.is_file(),
                    "is_dir": f.is_dir(),
                    "size": f.stat().st_size if f.is_file() else 0
                }
                for f in files
            ]

            return CommandResponse(
                status=StatusCode.SUCCESS,
                message=f"Found {len(file_list)} files",
                data={
                    "directory": str(directory),
                    "pattern": pattern,
                    "files": file_list,
                    "count": len(file_list)
                }
            )

        except Exception as e:
            return CommandResponse(
                status=StatusCode.INTERNAL_ERROR,
                message=f"Error listing files: {str(e)}"
            )


# ============================================================================
# SINGLETON PATTERN (OPTIONAL)
# ============================================================================

_mcp_server_instance: Optional[MCPServerTemplate] = None


def get_mcp_server(project_dir: Optional[Path] = None, server_class=None) -> MCPServerTemplate:
    """
    Get singleton MCP server instance

    Args:
        project_dir: Project directory (required on first call)
        server_class: Server class to instantiate (defaults to ExampleMCPServer)

    Returns:
        MCP server instance
    """
    global _mcp_server_instance

    if _mcp_server_instance is None:
        if project_dir is None:
            raise ValueError("project_dir required for first call to get_mcp_server()")

        if server_class is None:
            server_class = ExampleMCPServer

        _mcp_server_instance = server_class(project_dir)

    return _mcp_server_instance


def reset_mcp_server():
    """Reset singleton instance (for testing)"""
    global _mcp_server_instance
    _mcp_server_instance = None


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test the MCP server directly (without MCP protocol)
    """
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get project path from args or use current directory
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    else:
        project_dir = Path.cwd()

    print(f"Project directory: {project_dir}\n")

    # Create server
    server = ExampleMCPServer(project_dir)

    print("=" * 60)
    print("Testing MCP Server Commands")
    print("=" * 60)

    # Test PING (0x00)
    print("\n1. Testing PING (0x00):")
    response = server.execute_command(0x00, {})
    print(json.dumps(response, indent=2))

    # Test GET_STATUS (0x01)
    print("\n2. Testing GET_STATUS (0x01):")
    response = server.execute_command(0x01, {})
    print(json.dumps(response, indent=2))

    # Test GET_AVAILABLE_COMMANDS (0x02)
    print("\n3. Testing GET_AVAILABLE_COMMANDS (0x02):")
    response = server.execute_command(0x02, {})
    print(json.dumps(response, indent=2))

    # Test GREET (0x10)
    print("\n4. Testing GREET (0x10):")
    response = server.execute_command(0x10, {"name": "Alice"})
    print(json.dumps(response, indent=2))

    # Test CALCULATE (0x11)
    print("\n5. Testing CALCULATE (0x11):")
    response = server.execute_command(0x11, {
        "a": 15,
        "b": 3,
        "operation": "multiply"
    })
    print(json.dumps(response, indent=2))

    # Test LIST_FILES (0x20)
    print("\n6. Testing LIST_FILES (0x20):")
    response = server.execute_command(0x20, {
        "directory": ".",
        "pattern": "*.py"
    })
    print(json.dumps(response, indent=2))

    # Test invalid command
    print("\n7. Testing INVALID COMMAND (0xFF):")
    response = server.execute_command(0xFF, {})
    print(json.dumps(response, indent=2))

    # Test missing params
    print("\n8. Testing GREET with missing params:")
    response = server.execute_command(0x10, {})
    print(json.dumps(response, indent=2))

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
