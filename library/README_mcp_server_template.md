

# MCP Server Template

**Source:** Extracted from C3 project (`services/c3_mcp_server.py` + `services/c3_mcp_server_stdio.py`)
**Validation:** Proven in C3's Software Factory multi-terminal orchestration
**Files:**
- `library/mcp_server_template.py` - Core server with handler registry
- `library/mcp_server_stdio_wrapper.py` - MCP protocol stdio transport

## Overview

Complete template for building extensible MCP (Model Context Protocol) servers with command handler registry pattern. Based on 30 years telecom protocol design experience - hex command codes, structured request/response, and phase-based organization.

## Key Features

### 1. Handler Registry Pattern
- ✅ Map command codes (0x00-0xFF) to handler functions
- ✅ Easy extensibility - just register new handlers
- ✅ Organized by hex ranges (phases/categories)
- ✅ Automatic command validation and routing

### 2. Structured Protocol
- ✅ Status codes (SUCCESS, INVALID_COMMAND, INVALID_PARAMS, etc.)
- ✅ Typed request/response structures (dataclasses)
- ✅ Timestamped messages
- ✅ Comprehensive error handling

### 3. MCP Protocol Integration
- ✅ JSON-RPC 2.0 over stdio (newline-delimited)
- ✅ MCP lifecycle handling (initialize, initialized)
- ✅ Tool discovery (tools/list)
- ✅ Tool execution (tools/call)
- ✅ Single-tool interface (command_code pattern)

### 4. Production-Ready Features
- ✅ Comprehensive logging (file + console)
- ✅ Singleton pattern (optional)
- ✅ Exception handling at all levels
- ✅ Built-in core commands (PING, GET_STATUS, etc.)

## Quick Start

### 1. Create Your MCP Server

```python
from pathlib import Path
from library.mcp_server_template import (
    MCPServerTemplate,
    CommandResponse,
    StatusCode,
    CoreCommand
)

class MyMCPServer(MCPServerTemplate):
    """My custom MCP server"""

    def __init__(self, project_dir: Path):
        super().__init__(project_dir, server_name="MyMCPServer")

    def _register_custom_handlers(self):
        """Register your custom command handlers"""
        # Category 1 commands (0x10-0x1F)
        self.register_handler(0x10, self._handle_do_something)
        self.register_handler(0x11, self._handle_do_something_else)

        # Category 2 commands (0x20-0x2F)
        self.register_handler(0x20, self._handle_query)

    def _handle_do_something(self, params):
        """Handle DO_SOMETHING command (0x10)"""
        # Validate params
        if "name" not in params:
            return CommandResponse(
                status=StatusCode.INVALID_PARAMS,
                message="Missing required parameter: name"
            )

        # Do the work
        result = f"Did something with {params['name']}!"

        # Return success
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Completed successfully",
            data={"result": result}
        )

    def _handle_do_something_else(self, params):
        """Handle DO_SOMETHING_ELSE command (0x11)"""
        # Your implementation here
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Did something else!"
        )

    def _handle_query(self, params):
        """Handle QUERY command (0x20)"""
        # Your implementation here
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Query completed",
            data={"results": [...]}
        )
```

### 2. Create STDIO Wrapper Script

Create a script `my_mcp_server_stdio.py`:

```python
#!/usr/bin/env python3
"""My MCP Server - STDIO Entry Point"""

import sys
from pathlib import Path

# Add library to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from my_mcp_server import MyMCPServer
from library.mcp_server_stdio_wrapper import MCPStdioWrapper

def main():
    """Main entry point"""
    # Get project directory from args or env
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    else:
        project_dir = Path.cwd()

    # Create server
    server = MyMCPServer(project_dir)

    # Create wrapper and run
    wrapper = MCPStdioWrapper(
        mcp_server=server,
        tool_name="my_command",  # Claude will call mcp__my-server__my_command
        server_name="my-server",
        server_version="1.0.0"
    )

    wrapper.run()

if __name__ == "__main__":
    main()
```

Make it executable:

```bash
chmod +x my_mcp_server_stdio.py
```

### 3. Configure MCP in Project

Create or update `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python3",
      "args": ["/absolute/path/to/my_mcp_server_stdio.py"],
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    }
  }
}
```

### 4. Enable in Claude Settings

Update `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__my-server__my_command"
    ]
  },
  "enabledMcpjsonServers": [
    "my-server"
  ]
}
```

### 5. Test from Claude Code

```python
# Claude Code will call:
mcp__my-server__my_command(
    command_code=0x10,
    params={"name": "Alice"}
)

# Returns:
{
  "status": 0,
  "message": "Completed successfully",
  "data": {
    "result": "Did something with Alice!"
  },
  "timestamp": "2026-02-07T12:34:56.789Z"
}
```

## Command Code Organization

Organize commands by hex ranges (16 codes per category):

```python
class CommandRange:
    """Command code ranges by category"""

    # Core/Meta Commands (0x00-0x0F)
    CORE_START = 0x00
    CORE_END = 0x0F

    # Data Operations (0x10-0x1F)
    DATA_START = 0x10
    DATA_END = 0x1F

    # Analysis Operations (0x20-0x2F)
    ANALYSIS_START = 0x20
    ANALYSIS_END = 0x2F

    # File Operations (0x30-0x3F)
    FILE_START = 0x30
    FILE_END = 0x3F

    # Add more as needed...
```

Define command codes:

```python
class DataCommand:
    """Data operation command codes (0x10-0x1F)"""
    CREATE = 0x10
    READ = 0x11
    UPDATE = 0x12
    DELETE = 0x13
    LIST = 0x14
```

## Built-in Core Commands

All MCP servers include these core commands:

| Code | Name | Description |
|------|------|-------------|
| 0x00 | PING | Health check - returns "pong" |
| 0x01 | GET_STATUS | Server status (project dir, command count) |
| 0x02 | GET_AVAILABLE_COMMANDS | List all registered commands |
| 0x03 | LOG_MESSAGE | Log message from client |

Test core commands:

```python
# PING
server.execute_command(0x00, {})
# Returns: {"status": 0, "message": "pong", "data": {"server": "...", "version": "..."}}

# GET_STATUS
server.execute_command(0x01, {})
# Returns: {"status": 0, "message": "Server status retrieved", "data": {...}}

# GET_AVAILABLE_COMMANDS
server.execute_command(0x02, {})
# Returns: {"status": 0, "message": "Found N commands", "data": {"commands_by_range": {...}}}

# LOG_MESSAGE
server.execute_command(0x03, {"message": "Hello from client", "level": "info"})
# Returns: {"status": 0, "message": "Message logged"}
```

## Status Codes

Use structured status codes for proper error handling:

```python
class StatusCode:
    SUCCESS = 0x00          # Command succeeded
    INVALID_COMMAND = 0x01  # Unknown command code
    INVALID_PARAMS = 0x02   # Missing or invalid parameters
    FILE_NOT_FOUND = 0x03   # File/resource not found
    PARSE_ERROR = 0x04      # Failed to parse input
    INTERNAL_ERROR = 0x05   # Internal server error
    NOT_IMPLEMENTED = 0x06  # Command not implemented yet
    PERMISSION_DENIED = 0x07 # Permission denied
```

Return proper status codes:

```python
def _handle_my_command(self, params):
    # Parameter validation
    if "required_field" not in params:
        return CommandResponse(
            status=StatusCode.INVALID_PARAMS,
            message="Missing required parameter: required_field"
        )

    # File operations
    file_path = Path(params["file_path"])
    if not file_path.exists():
        return CommandResponse(
            status=StatusCode.FILE_NOT_FOUND,
            message=f"File not found: {file_path}"
        )

    # Business logic
    try:
        result = do_something()
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Operation completed",
            data={"result": result}
        )
    except Exception as e:
        return CommandResponse(
            status=StatusCode.INTERNAL_ERROR,
            message=f"Error: {str(e)}"
        )
```

## Handler Function Signature

All command handlers must follow this signature:

```python
def _handle_command_name(self, params: Dict[str, Any]) -> CommandResponse:
    """
    Handle COMMAND_NAME command (0xNN)

    Params:
        param1: type - Description
        param2: type - Description (optional)

    Returns:
        CommandResponse with status, message, and data
    """
    # Implementation
    return CommandResponse(
        status=StatusCode.SUCCESS,
        message="Success message",
        data={"key": "value"}
    )
```

## Testing

### Direct Testing (Without MCP Protocol)

Test your server directly without MCP:

```python
from pathlib import Path
from my_mcp_server import MyMCPServer

# Create server
server = MyMCPServer(project_dir=Path.cwd())

# Test commands directly
response = server.execute_command(0x10, {"name": "Alice"})
print(response)
# {'status': 0, 'message': '...', 'data': {...}, 'timestamp': '...'}
```

### Testing with MCP Protocol

Use the built-in test script in `mcp_server_template.py`:

```bash
python3 library/mcp_server_template.py /path/to/project
```

This will test all example commands and show output.

### Integration Testing

Test via Claude Code:

1. Configure `.mcp.json` and `settings.local.json`
2. Start Claude Code session
3. Call your MCP tool:

```python
# In Claude Code
result = mcp__my_server__my_command(
    command_code=0x10,
    params={"name": "Test"}
)
```

## Advanced Patterns

### Command Aliases

Create friendly wrappers:

```python
class MyMCPServer(MCPServerTemplate):
    def ping(self):
        """Convenience method for PING"""
        return self.execute_command(0x00, {})

    def get_status(self):
        """Convenience method for GET_STATUS"""
        return self.execute_command(0x01, {})

    def do_something(self, name: str):
        """Convenience method for DO_SOMETHING"""
        return self.execute_command(0x10, {"name": name})
```

### File-Based Communication

Store results in files for large responses:

```python
def _handle_generate_report(self, params):
    """Generate large report and save to file"""
    report_file = self.output_dir / "report.json"

    # Generate report
    report_data = generate_large_report()

    # Save to file
    report_file.write_text(json.dumps(report_data, indent=2))

    # Return file path
    return CommandResponse(
        status=StatusCode.SUCCESS,
        message="Report generated",
        data={
            "report_file": str(report_file),
            "size_bytes": report_file.stat().st_size
        }
    )
```

### Activity Tracking

Track client activity for monitoring:

```python
def _handle_log_message(self, params):
    """Override core LOG_MESSAGE to add activity tracking"""
    # Call parent implementation
    response = super()._handle_log_message(params)

    # Also persist to activity file
    activity_file = self.output_dir / "activity.json"

    # Load existing activity
    if activity_file.exists():
        activity_data = json.loads(activity_file.read_text())
    else:
        activity_data = {"messages": []}

    # Append new message
    activity_data["messages"].append({
        "timestamp": datetime.now().isoformat(),
        "level": params.get("level", "info"),
        "message": params["message"]
    })

    # Keep last 100 messages
    if len(activity_data["messages"]) > 100:
        activity_data["messages"] = activity_data["messages"][-100:]

    # Save
    activity_file.write_text(json.dumps(activity_data, indent=2))

    return response
```

### Batch Operations

Support batch commands for efficiency:

```python
class BatchCommand:
    """Batch operation commands"""
    BATCH_EXECUTE = 0x50

def _handle_batch_execute(self, params):
    """Execute multiple commands in sequence"""
    if "commands" not in params:
        return CommandResponse(
            status=StatusCode.INVALID_PARAMS,
            message="Missing required parameter: commands"
        )

    commands = params["commands"]
    results = []

    for cmd in commands:
        code = cmd.get("command_code")
        cmd_params = cmd.get("params", {})

        # Execute each command
        result = self.execute_command(code, cmd_params)
        results.append(result)

        # Stop on first error if requested
        if params.get("stop_on_error", False) and result["status"] != StatusCode.SUCCESS:
            break

    return CommandResponse(
        status=StatusCode.SUCCESS,
        message=f"Executed {len(results)} commands",
        data={"results": results}
    )
```

## Integration with C3 Patterns

### SW Factory Monitored Sessions

Combine with C3's terminal spawning for orchestration:

```python
from library.claude_terminal_spawner import ClaudeTerminalSpawner

# Spawn Claude terminal
spawner = ClaudeTerminalSpawner()
terminal = spawner.spawn_terminal(
    project_path=Path("/path/to/project"),
    terminal_id="worker_1",
    label="Worker 1"
)

# Configure MCP in that project (terminal_manager.py pattern)
# Terminal will auto-connect to your MCP server

# Inject initial command
spawner.inject_text(
    window_id=terminal['window_id'],
    text="Use mcp__my-server__my_command with code 0x10 to start",
    submit=True
)
```

### Multi-Terminal Coordination

Each terminal can communicate with central MCP server:

```python
# Terminal 1 reports progress
mcp__my-server__my_command(0x10, {"status": "started", "terminal": "T1"})

# Terminal 2 queries Terminal 1's status
mcp__my-server__my_command(0x20, {"query": "status", "terminal": "T1"})

# Central orchestrator decides next steps
```

## Debugging

### Enable Debug Logging

```python
import logging

# Set debug level before creating server
logging.basicConfig(level=logging.DEBUG)

server = MyMCPServer(project_dir=Path.cwd())
```

### Check Log Files

Server logs are written to:
- `{output_dir}/{server_name}.log`

Default: `{project_dir}/.mcp_server/mymcpserver.log`

### STDIO Transport Logs

STDIO wrapper logs to **stderr** (stdout is for protocol):

```bash
# Run wrapper and see logs
python3 my_mcp_server_stdio.py 2>&1 | tee mcp_debug.log
```

### Test Without Claude

```python
# Direct testing
python3 -c "
from my_mcp_server import MyMCPServer
from pathlib import Path
import json

server = MyMCPServer(Path.cwd())
result = server.execute_command(0x10, {'name': 'Test'})
print(json.dumps(result, indent=2))
"
```

## Best Practices

### 1. Command Organization
- **Group by phase/category** (0x10-0x1F for one category, 0x20-0x2F for another)
- **Reserve 0x00-0x0F** for core/meta commands
- **Document command codes** in docstrings and README

### 2. Parameter Validation
- **Always validate required params** before processing
- **Return INVALID_PARAMS** with clear message for missing/invalid params
- **Use type hints** in docstrings for clarity

### 3. Error Handling
- **Catch exceptions** and return INTERNAL_ERROR with details
- **Use appropriate status codes** (not just SUCCESS/ERROR)
- **Log errors** with full context for debugging

### 4. Response Data
- **Keep responses focused** - include only necessary data
- **Use consistent data structures** across commands
- **Document response structure** in handler docstrings

### 5. Performance
- **For large data, use file-based communication** (return file path, not data)
- **Support batch operations** for efficiency
- **Add timeouts** for long-running operations

### 6. Security
- **Validate file paths** (prevent directory traversal)
- **Sanitize inputs** (prevent injection attacks)
- **Check permissions** before sensitive operations
- **Log all commands** for audit trail

## Comparison: Single Tool vs Multi-Tool

### Single Tool Pattern (This Template)
```python
# One tool, multiple commands via code
mcp__my_server__my_command(command_code=0x10, params={...})
mcp__my_server__my_command(command_code=0x11, params={...})
```

**Pros:**
- ✅ **85% context savings** (proven in C3)
- ✅ Easy to add commands (just register handler)
- ✅ Consistent interface
- ✅ Easy versioning (command codes)

**Cons:**
- ❌ Less discoverable (need to query available commands)
- ❌ Extra layer of indirection

### Multi-Tool Pattern (Traditional MCP)
```python
# Multiple tools
mcp__my_server__do_something(params={...})
mcp__my_server__do_something_else(params={...})
```

**Pros:**
- ✅ Better tool discovery
- ✅ Direct invocation
- ✅ Familiar pattern

**Cons:**
- ❌ Uses more context (each tool definition)
- ❌ Harder to add new commands (new tool definition)
- ❌ Versioning complexity

**Recommendation:** Use single-tool pattern for applications with many commands (10+). The context savings become significant.

## FAQ

**Q: Can I have multiple tools per server?**
A: Yes! The template uses a single tool pattern, but you can modify `MCPStdioWrapper.handle_tools_list()` to return multiple tools if needed.

**Q: How do I version my command codes?**
A: Add version to response data, or use different command code ranges for different versions (v1: 0x10-0x1F, v2: 0x20-0x2F).

**Q: Can I use async handlers?**
A: Not directly in this template (uses sync), but you can run async code inside handlers with `asyncio.run()`.

**Q: How do I share state between commands?**
A: Store state as instance variables in your server class (e.g., `self._state = {}`).

**Q: Can I have multiple MCP servers per project?**
A: Yes! Just use different server names and tool names in `.mcp.json`.

**Q: How do I test MCP servers in CI/CD?**
A: Use direct testing (without MCP protocol) in your test suite. See "Testing" section.

## Example Projects

See complete example implementations:

- **C3** (`/A_Coding/C3/services/c3_mcp_server.py`) - Full-featured server with 30+ commands
- **EE** (`library/mcp_server_template.py`) - Minimal template with examples

## References

- [Model Context Protocol Docs](https://modelcontextprotocol.io/docs/learn/architecture)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- C3 MCP Design Doc (30 years telecom protocol experience)

---

**Silver Wizard Software - Enterprise Edition**
*Building the infrastructure that powers the ecosystem*
