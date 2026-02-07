#!/usr/bin/env python3
"""
TCC Setup - Iteration 1 (KISS)

Instruments a project directory for TCC monitoring.
Creates MCP settings and SessionStart hook.

Module Size Target: <100 lines
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TCCSetup:
    """
    Instruments a project for TCC (Target CC) monitoring.

    Iteration 1: Simple MCP setup + SessionStart hook.
    """

    @staticmethod
    def instrument_project(
        project_path: Path,
        ccm_port: int = 50001
    ) -> dict:
        """
        Instrument a project for TCC monitoring.

        Creates:
        1. .claude/mcp_settings.json - Points to CCM MCP server
        2. .claude/settings.json - SessionStart hook sends "TCC started"

        Args:
            project_path: Path to project directory
            ccm_port: CCM MCP server port

        Returns:
            dict with status and files created

        Raises:
            RuntimeError: If project path invalid or instrumentation fails
        """
        if not project_path.exists():
            raise RuntimeError(f"Project path does not exist: {project_path}")

        logger.info(f"Instrumenting project: {project_path}")

        # Create .claude directory
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # Create MCP settings
        mcp_settings_file = claude_dir / "mcp_settings.json"
        TCCSetup._write_mcp_settings(mcp_settings_file, ccm_port)

        # Create/update settings.json with SessionStart hook
        settings_file = claude_dir / "settings.json"
        TCCSetup._write_session_start_hook(settings_file, ccm_port)

        # Create CLAUDE.md explaining CCM monitoring
        claude_md_file = claude_dir / "CLAUDE.md"
        TCCSetup._write_monitoring_instructions(claude_md_file, ccm_port)

        logger.info(f"✅ Project instrumented successfully")

        return {
            "success": True,
            "project": str(project_path),
            "files_created": [
                str(mcp_settings_file),
                str(settings_file),
                str(claude_md_file)
            ]
        }

    @staticmethod
    def _write_mcp_settings(file_path: Path, ccm_port: int):
        """Write MCP settings pointing to CCM."""
        mcp_settings = {
            "mcpServers": {
                "ccm": {
                    "url": f"http://localhost:{ccm_port}/mcp"
                }
            }
        }

        file_path.write_text(json.dumps(mcp_settings, indent=2))
        logger.info(f"✅ MCP settings written: {file_path}")

    @staticmethod
    def _write_session_start_hook(file_path: Path, ccm_port: int):
        """
        Write/update settings.json with SessionStart hook.

        Hook sends "TCC started" message to CCM via MCP.
        """
        # Load existing settings if present
        if file_path.exists():
            try:
                settings = json.loads(file_path.read_text())
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {file_path}, creating new")
                settings = {}
        else:
            settings = {}

        # Create SessionStart hook using NEW format (matcher-based)
        # Uses MCP to call log_message tool
        # Added visibility: echo statements show instrumentation status
        hook_command = (
            f'echo "\\n🎯 CCM Monitoring Active (port {ccm_port})" && '
            f'echo "📤 Sending startup notification to CCM..." && '
            f'curl -X POST http://localhost:{ccm_port}/mcp '
            f'-H "Content-Type: application/json" '
            f'-d \'{{"jsonrpc": "2.0", "id": 1, "method": "tools/call", '
            f'"params": {{"name": "log_message", "arguments": {{"message": "TCC started"}}}}}}\' '
            f'&& echo "✅ CCM notified: TCC started\\n" || echo "⚠️  CCM notification failed (CCM may not be running)\\n"'
        )

        # Add hooks section with NEW format (array containing object with hooks)
        if "hooks" not in settings:
            settings["hooks"] = {}

        # NEW format: array containing object with "hooks" array
        # Format: "SessionStart": [{"hooks": [{"type": "command", "command": "..."}]}]
        settings["hooks"]["SessionStart"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": hook_command
                    }
                ]
            }
        ]

        # Write settings
        file_path.write_text(json.dumps(settings, indent=2))
        logger.info(f"✅ SessionStart hook written: {file_path}")

    @staticmethod
    def _write_monitoring_instructions(file_path: Path, ccm_port: int):
        """
        Write CLAUDE.md explaining CCM monitoring to TCC.

        This helps TCC understand it's being monitored and how to interact with CCM.
        """
        content = f"""# 🎯 CCM Monitoring Active

**This project is being monitored by CCM (Claude Code Monitor).**

## What is CCM?

CCM is a monitoring application that tracks your progress and ensures you're making forward progress. It provides:

- **Watchdog Timer**: Monitors for activity and terminates idle sessions (currently 2 minutes for testing)
- **Progress Tracking**: Logs messages you send about your work
- **Automatic Startup Notification**: You already sent "TCC started" when this session began

## Available Tools

You have access to the **ccm** MCP server with these tools:

### `log_message`
Send status updates to CCM to reset the watchdog timer and log your progress.

**Example usage:**
```
Use the log_message tool from the ccm MCP server:
- message: "Completed step 1: Read project files"
```

**When to use:**
- Major milestone completed
- Starting a new phase of work
- Regular heartbeat to prevent timeout
- Error or blocker encountered

## Important Notes

1. **SessionStart hook ran automatically** - You already notified CCM that this session started
2. **Watchdog is active** - If CCM doesn't receive messages for 2 minutes, your session will be terminated
3. **Send updates proactively** - Don't wait for the watchdog to expire
4. **CCM port**: {ccm_port}

## MCP Server Configuration

The CCM MCP server is configured in `.claude/mcp_settings.json`:
- Server name: `ccm`
- URL: `http://localhost:{ccm_port}/mcp`

---

**Bottom line:** You're being monitored for progress. Send regular updates using the `log_message` tool to show you're making forward progress and reset the watchdog timer.

## 🚀 Startup Instructions

**IMPORTANT: After this session starts, immediately:**

1. Check if `Plan.md` exists in the project root
2. If it exists, read it
3. Execute the plan exactly as written
4. Do NOT ask for permission - execute immediately

The plan will tell you what messages to send to CCM and when. Follow it precisely.
"""

        file_path.write_text(content)
        logger.info(f"✅ Monitoring instructions written: {file_path}")
