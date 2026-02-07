# EE Library

Reusable components extracted from Silver Wizard Software projects. Each library module is battle-tested and ready for cross-project use.

## Available Libraries

### 1. Claude Terminal Spawner

**File:** `claude_terminal_spawner.py`
**Source:** C3 project (`services/terminal_manager.py`)
**Documentation:** [README_claude_terminal_spawner.md](README_claude_terminal_spawner.md)

Complete protocol for spawning macOS Terminal windows running Claude Code with:
- ✅ NEW window creation (not tabs)
- ✅ Text injection for auto-starting sessions
- ✅ **Foolproof termination using SIGKILL (no approval dialogs)**
- ✅ PID tracking and window management
- ✅ Trust prompt bypass with `--permission-mode dontAsk`

**Key Use Cases:**
- Automated Claude session spawning
- Handoff automation between EE cycles
- Multi-terminal orchestration (SW Factory pattern)
- Development assistance terminals

**Quick Example:**
```python
from library.claude_terminal_spawner import ClaudeTerminalSpawner

spawner = ClaudeTerminalSpawner()
info = spawner.spawn_terminal(
    project_path=Path("/path/to/project"),
    terminal_id="task_1",
    label="Task 1"
)

spawner.inject_text(info['window_id'], "Help me with...", submit=True)
spawner.close_terminal(info['pid'], info['window_id'], "task_1")
```

---

### 2. MCP Server Template

**Files:**
- `mcp_server_template.py` - Core server with handler registry
- `mcp_server_stdio_wrapper.py` - MCP protocol stdio transport

**Source:** C3 project (`services/c3_mcp_server.py` + `services/c3_mcp_server_stdio.py`)
**Documentation:** [README_mcp_server_template.md](README_mcp_server_template.md)

Extensible MCP (Model Context Protocol) server template with command handler registry pattern:
- ✅ **Handler registry pattern** (hex command codes 0x00-0xFF)
- ✅ **Structured protocol** with status codes and typed requests/responses
- ✅ **MCP integration** (JSON-RPC 2.0 over stdio)
- ✅ **Phase-based organization** (inspired by 30 years telecom experience)
- ✅ **Production-ready** with comprehensive logging

**Key Use Cases:**
- Building custom MCP servers for Claude Code integration
- Multi-command tools with single MCP tool interface (85% context savings)
- Claude-to-parent communication (SW Factory pattern)
- Structured command routing and handling

**Quick Example:**
```python
from library.mcp_server_template import MCPServerTemplate, CommandResponse, StatusCode

class MyMCPServer(MCPServerTemplate):
    def _register_custom_handlers(self):
        self.register_handler(0x10, self._handle_my_command)

    def _handle_my_command(self, params):
        return CommandResponse(
            status=StatusCode.SUCCESS,
            message="Did something!",
            data={"result": "..."}
        )

# Expose via MCP
from library.mcp_server_stdio_wrapper import MCPStdioWrapper
server = MyMCPServer(project_dir=Path.cwd())
wrapper = MCPStdioWrapper(server, tool_name="my_command")
wrapper.run()
```

---

### 3. MCP Project Setup Utility

**File:** `mcp_project_setup.py`
**Source:** C3 project (`services/instrumentation_service.py` + `services/terminal_manager.py`)
**Documentation:** Used by MCP server template and terminal spawner

Utility for instrumenting Claude Code projects with MCP configuration:
- ✅ **Creates .mcp.json** with server configuration
- ✅ **Configures settings.local.json** with tool permissions
- ✅ **Backs up existing files** (fully reversible)
- ✅ **Adds to .gitignore** to prevent git pollution
- ✅ **Validates setup** after configuration
- ✅ **Provides cleanup** to restore original state

**Key Use Cases:**
- Setting up MCP servers in Claude Code projects
- Terminal spawning with MCP integration
- Automated project instrumentation
- Clean teardown after testing

**Quick Example:**
```python
from library.mcp_project_setup import setup_mcp_for_project, cleanup_mcp_from_project

# Setup MCP
result = setup_mcp_for_project(
    project_path=Path("/path/to/project"),
    mcp_server_script=Path("/path/to/my_mcp_server_stdio.py"),
    server_name="my-server",
    tool_name="my_command"
)

# Later, cleanup
cleanup_result = cleanup_mcp_from_project(
    project_path=Path("/path/to/project")
)
```

---

## Library Standards

All EE library modules follow these standards:

1. **Battle-Tested**: Extracted from working Silver Wizard projects
2. **Documented**: Complete README with examples and API reference
3. **Source Attribution**: Clear citation of origin project
4. **Validation History**: Evidence of successful usage
5. **Standalone**: Minimal dependencies, works independently
6. **Educational**: Includes insights and technical details

## Using Library Modules

### Installation

Library modules are Python files that can be imported directly:

```python
# From within EE project
from library.claude_terminal_spawner import ClaudeTerminalSpawner

# From sister projects (add EE to path)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "EE"))
from library.claude_terminal_spawner import ClaudeTerminalSpawner
```

### Dependencies

Most library modules have minimal dependencies:
- Standard library (os, subprocess, pathlib, etc.)
- Python 3.13+ (Silver Wizard standard)

Project-specific dependencies are noted in each module's README.

## Contributing New Libraries

When extracting code from other Silver Wizard projects:

1. **Identify proven patterns** - Only extract code that's been validated in real use
2. **Remove project-specific coupling** - Make it generic and reusable
3. **Keep core logic intact** - Don't refactor during extraction
4. **Document thoroughly** - README with examples and technical details
5. **Cite source** - Always attribute the origin project
6. **Add to this index** - Update this README with new entry

### Extraction Checklist

- [ ] Code proven in source project (not experimental)
- [ ] Project-specific imports removed or made optional
- [ ] Configuration exposed as parameters (not hardcoded)
- [ ] Complete docstrings on all public methods
- [ ] README created with:
  - [ ] Overview and key features
  - [ ] Basic and advanced usage examples
  - [ ] Complete API reference
  - [ ] Technical details and design rationale
  - [ ] Source attribution
  - [ ] Validation history
- [ ] Example code in `if __name__ == "__main__"`
- [ ] Entry added to this index

## Library Philosophy

### Why Extract?

Silver Wizard Software builds multiple interconnected projects. Rather than duplicate code, we:
1. **Extract proven patterns** into reusable libraries
2. **Maintain single source of truth** for each pattern
3. **Share knowledge** across all projects
4. **Accelerate development** by building on validated components

### Quality Bar

Library code must meet a higher standard than project code:
- **Thoroughly tested** in real projects
- **Clearly documented** with examples
- **Designed for reuse** (generic, configurable)
- **Minimal coupling** to specific projects
- **Educational** (explains why, not just what)

### Anti-Patterns to Avoid

❌ Don't extract code that's only been used once
❌ Don't refactor during extraction (test first, then refactor)
❌ Don't create abstractions for hypothetical future use
❌ Don't hide important details behind "simple" APIs
❌ Don't skip documentation ("code is self-documenting")

## Library Naming Conventions

- **Descriptive names**: `claude_terminal_spawner.py` not `terminal.py`
- **Snake case**: `multi_word_names.py` not `multiWordNames.py`
- **Action-oriented**: `spawner`, `manager`, `handler` suffixes
- **No abbreviations**: `claude_terminal_spawner` not `cts`

## Future Libraries (Planned)

These patterns are candidates for extraction:

- [ ] **MM Mesh Client** - MCP mesh registration and communication
- [ ] **Version Info** - Structured version reporting (from PIW)
- [ ] **Module Monitor** - LOC tracking and bloat detection (from CMC)
- [ ] **PyQt Template Patterns** - Reusable PyQt6 components
- [ ] **Telco Logger** - Structured logging with severity levels (from C3)
- [ ] **Parent CC Protocol** - Handoff and continuation (from EE)

## Questions?

For questions about library modules, see:
- Individual README files for each module
- Source project for reference implementation
- `.claude/CLAUDE.md` in EE project for architecture guidance

---

**Silver Wizard Software - Enterprise Edition**
*Building the infrastructure that powers the ecosystem*
