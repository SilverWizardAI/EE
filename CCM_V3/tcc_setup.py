#!/usr/bin/env python3
"""
TCC Setup - Iteration 2 (C3 Integration)

Instruments a project directory for TCC monitoring.
Creates MCP settings, SessionStart hook, and C3 (Claude Code Controller) tools.

Module Size Target: <600 lines (Current: ~550 with C3 support)
"""

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# C3 Version - increment when updating tools
C3_VERSION = "1.0.0"


class TCCSetup:
    """
    Instruments a project for TCC (Target CC) monitoring.

    Iteration 1: Simple MCP setup + SessionStart hook.
    """

    @staticmethod
    def instrument_project(
        project_path: Path,
        mcp_socket_path: Path,
        plan_file: str = "Plan_2.md",
        c3_version: str = C3_VERSION
    ) -> dict:
        """
        Instrument a project for TCC monitoring with C3 tools.

        Creates:
        1. .C3/ - Claude Code Controller tools package (versioned)
        2. .claude/mcp_settings.json - Points to MCP Access Proxy
        3. .claude/settings.json - SessionStart hook sends "TCC started"
        4. .claude/CLAUDE.md - Monitoring instructions
        5. Plan.md - Copy of selected plan from plans directory
        6. Next_Steps.md - State persistence file
        7. cycle_state.json - Initial cycle state

        Args:
            project_path: Path to project directory
            mcp_socket_path: Unix socket path of Real MCP Server
            plan_file: Name of plan file to use (e.g., "Plan_2.md")
            c3_version: C3 version to install (default: current version)

        Returns:
            dict with status, C3 version, and files created

        Raises:
            RuntimeError: If project path invalid or instrumentation fails
        """
        if not project_path.exists():
            raise RuntimeError(f"Project path does not exist: {project_path}")

        logger.info(f"Instrumenting project: {project_path}")

        # Check and install/upgrade C3
        c3_status = TCCSetup._check_c3_version(project_path, c3_version)

        if c3_status["action"] == "install":
            logger.info("Installing C3 instrumentation (not present)")
            TCCSetup._install_c3(project_path, c3_version)
        elif c3_status["action"] == "upgrade":
            logger.info(f"Upgrading C3 from {c3_status['current']} to {c3_version}")
            TCCSetup._upgrade_c3(project_path, c3_version)
        elif c3_status["action"] == "skip":
            logger.info(f"C3 {c3_status['current']} already installed, skipping")

        # Initialize cycle state if needed
        TCCSetup._initialize_state(project_path)

        # Create .claude directory
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # Write to GLOBAL Claude Code config (where Claude CLI reads from)
        global_config_dir = Path.home() / "Library" / "Application Support" / "Claude"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "claude_desktop_config.json"
        TCCSetup._write_mcp_settings(global_config_file, mcp_socket_path)

        # Create/update settings.json with SessionStart hook
        settings_file = claude_dir / "settings.json"
        TCCSetup._write_session_start_hook(settings_file, mcp_socket_path)

        # Create CLAUDE.md explaining CCM monitoring
        claude_md_file = claude_dir / "CLAUDE.md"
        TCCSetup._write_monitoring_instructions(claude_md_file, mcp_socket_path)

        # Copy selected plan to project root
        plan_target = project_path / "Plan.md"
        TCCSetup._copy_plan_to_project(plan_target, plan_file)

        # Create Next_Steps.md if doesn't exist
        next_steps_file = project_path / "Next_Steps.md"
        if not next_steps_file.exists():
            next_steps_file.write_text("Next: Step 1\n")
            logger.info(f"✅ Created Next_Steps.md")

        logger.info(f"✅ Project instrumented successfully with C3 v{c3_version}")

        return {
            "success": True,
            "project": str(project_path),
            "c3_version": c3_version,
            "c3_action": c3_status["action"],
            "files_created": [
                str(project_path / ".C3"),
                str(global_config_file),
                str(settings_file),
                str(claude_md_file),
                str(plan_target),
                str(next_steps_file)
            ]
        }

    @staticmethod
    def _check_c3_version(project_path: Path, required_version: str) -> dict:
        """
        Check if C3 is installed and at correct version.

        Returns:
            {
                "action": "install" | "upgrade" | "skip",
                "current": version string or None,
                "required": required_version
            }
        """
        c3_dir = project_path / ".C3"
        readme_file = c3_dir / "README.md"

        if not c3_dir.exists():
            return {"action": "install", "current": None, "required": required_version}

        if not readme_file.exists():
            logger.warning("C3 directory exists but no README.md, reinstalling")
            return {"action": "install", "current": None, "required": required_version}

        # Parse version from README.md
        try:
            readme_content = readme_file.read_text()
            version_match = re.search(r'\*\*Version:\*\*\s+([\d.]+)', readme_content)
            if version_match:
                current_version = version_match.group(1)

                # Simple version comparison (assumes semver)
                if current_version == required_version:
                    return {"action": "skip", "current": current_version, "required": required_version}
                else:
                    return {"action": "upgrade", "current": current_version, "required": required_version}
            else:
                logger.warning("Version not found in README.md, reinstalling")
                return {"action": "install", "current": None, "required": required_version}
        except Exception as e:
            logger.error(f"Error reading C3 README: {e}")
            return {"action": "install", "current": None, "required": required_version}

    @staticmethod
    def _install_c3(project_path: Path, version: str):
        """
        Install C3 (Claude Code Controller) instrumentation package.

        Creates .C3/ directory with:
        - send_to_monitor.py
        - ee_manager.py
        - token_checker.py
        - terminate_cycle.py
        - README.md (with version info)
        """
        c3_dir = project_path / ".C3"
        c3_dir.mkdir(exist_ok=True)

        # Get EE tools directory
        ee_tools_dir = Path(__file__).parent.parent / "tools"

        # Tools to copy (TCC's essential list + token_checker for defensive checking)
        tools = [
            "send_to_monitor.py",
            "ee_manager.py",
            "token_checker.py",
            "terminate_cycle.py"
        ]

        # Copy each tool
        for tool in tools:
            source = ee_tools_dir / tool
            target = c3_dir / tool

            if source.exists():
                shutil.copy2(source, target)
                target.chmod(0o755)
                logger.info(f"✅ Installed {tool}")
            else:
                logger.warning(f"⚠️  Tool not found: {source}")

        # Create README.md with version and documentation
        readme_content = f"""# Claude Code Controller (C3) - Instrumentation Package

**Version:** {version}
**Installed:** {datetime.now().isoformat()}
**Installed By:** CCM v3

---

## What is C3?

This directory contains instrumentation tools that enable Claude Code (CC) instances
to operate under CCM (CC Monitor) orchestration. These tools provide:

- Communication with CCM
- Cycle state management
- Token budget tracking
- Graceful cycle termination

---

## Tools Included

### `send_to_monitor.py`
**Purpose:** Send status messages to CCM via Unix socket
**Usage:** `python3 .C3/send_to_monitor.py "Your message here"`
**When:** After completing each step, on errors, on cycle end

### `ee_manager.py`
**Purpose:** Manage cycle state (steps, cycles, history)
**Usage:**
- Complete step: `python3 .C3/ee_manager.py update --step-complete 1 --task "Description"`
- End cycle: `python3 .C3/ee_manager.py update --cycle-end "Reason"`
- Show status: `python3 .C3/ee_manager.py show`

### `token_checker.py`
**Purpose:** Check if token usage exceeds threshold before starting step
**Usage:** `python3 .C3/token_checker.py <current_tokens> --threshold <percent>`
**Returns:** Exit code 0 (OK to proceed) or 1 (threshold exceeded)

### `terminate_cycle.py` (Optional)
**Purpose:** Unilateral cycle termination with cleanup
**Usage:** `python3 .C3/terminate_cycle.py "Reason" --tokens <count>`
**When:** Emergency termination, automation scripts

---

## Standard Step Completion Protocol

After **EVERY** successful step:

```bash
# 1. Update state
python3 .C3/ee_manager.py update --step-complete {{STEP}} --task "{{DESCRIPTION}}"

# 2. Commit
git add -A
git commit -m "Step {{STEP}}: {{DESCRIPTION}}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 3. Report (with your actual token %)
python3 .C3/send_to_monitor.py "Step {{STEP}} completed: Tokens: {{X.X}}%; Status: OK"
```

---

## Version History

### {version} ({datetime.now().strftime('%Y-%m-%d')})
- Initial release
- Core tools: send_to_monitor, ee_manager, token_checker, terminate_cycle
- Standard Step Completion Protocol

---

## Upgrade Instructions

CCM automatically manages C3 versions. If an upgrade is needed:
1. CCM detects version mismatch
2. Backs up current .C3/ to .C3.backup/
3. Installs new version
4. Updates this README with new version number

---

**DO NOT modify files in this directory.** They are managed by CCM.
"""

        readme_file = c3_dir / "README.md"
        readme_file.write_text(readme_content)
        logger.info(f"✅ Created C3 README.md v{version}")

    @staticmethod
    def _upgrade_c3(project_path: Path, new_version: str):
        """
        Upgrade C3 to new version.

        Backs up existing .C3/ to .C3.backup/ then installs new version.
        """
        c3_dir = project_path / ".C3"
        backup_dir = project_path / ".C3.backup"

        # Backup current C3
        if c3_dir.exists():
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(c3_dir, backup_dir)
            logger.info(f"✅ Backed up C3 to {backup_dir}")

        # Install new version
        TCCSetup._install_c3(project_path, new_version)
        logger.info(f"✅ Upgraded C3 to v{new_version}")

    @staticmethod
    def _initialize_state(project_path: Path):
        """
        Create initial cycle_state.json if doesn't exist.

        Uses the schema that matches what ee_manager.py expects.
        """
        state_file = project_path / "cycle_state.json"

        if not state_file.exists():
            initial_state = {
                "cycle": 1,
                "next_step": 1,
                "history": [],
                "created_at": datetime.now().isoformat()
            }
            state_file.write_text(json.dumps(initial_state, indent=2))
            logger.info(f"✅ Created cycle_state.json")

    @staticmethod
    def _write_mcp_settings(file_path: Path, mcp_socket_path: Path):
        """
        Write MCP settings pointing to MCP Access Proxy.

        TCC spawns the Access Proxy which connects to Real MCP Server.
        Merges with existing MCP servers if file exists.
        """
        # Load existing settings if present
        if file_path.exists():
            try:
                mcp_settings = json.loads(file_path.read_text())
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {file_path}, creating new")
                mcp_settings = {}
        else:
            mcp_settings = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in mcp_settings:
            mcp_settings["mcpServers"] = {}

        # Get path to mcp_access_proxy.py
        access_proxy_script = Path(__file__).parent / "mcp_access_proxy.py"

        # Add/update ccm server
        mcp_settings["mcpServers"]["ccm"] = {
            "command": "python3",
            "args": [str(access_proxy_script), str(mcp_socket_path)]
        }

        file_path.write_text(json.dumps(mcp_settings, indent=2))
        logger.info(f"✅ MCP settings written: {file_path}")

    @staticmethod
    def _write_session_start_hook(file_path: Path, mcp_socket_path: Path):
        """
        Write/update settings.json with SessionStart hook.

        Hook shows that monitoring is active. TCC will send messages via log_message tool.
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

        # Simple hook that shows monitoring is active
        hook_command = (
            f'echo "\\n🎯 CCM Monitoring Active\\n'
            f'   MCP Server: {mcp_socket_path.name}\\n'
            f'   Tool: log_message (send progress updates)\\n"'
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
    def _write_monitoring_instructions(file_path: Path, mcp_socket_path: Path):
        """
        Write CLAUDE.md explaining CCM monitoring to TCC.

        This helps TCC understand it's being monitored and how to interact with CCM.
        """
        content = f"""# 🎯 CCM Monitoring Active

**This project is being monitored by CCM (Claude Code Monitor).**

---

## 🛠️ C3 Tools Available

Your workspace is instrumented with **C3 (Claude Code Controller)**.

All tools are in the `.C3/` directory. **Read `.C3/README.md` for full documentation.**

**Quick reference:**
- `python3 .C3/send_to_monitor.py "message"` - Send status to CCM
- `python3 .C3/ee_manager.py update --step-complete N --task "desc"` - Mark step done
- `python3 .C3/token_checker.py $TOKENS --threshold 35` - Check token budget
- `python3 .C3/ee_manager.py show` - Show current cycle state

**Standard Step Completion Protocol:**
```bash
# After EVERY step:
python3 .C3/ee_manager.py update --step-complete {{STEP}} --task "{{DESCRIPTION}}"
git add -A && git commit -m "Step {{STEP}}: {{DESCRIPTION}}"
python3 .C3/send_to_monitor.py "Step {{STEP}} completed: Tokens: {{X.X}}%; Status: OK"
```

---

## What is CCM?

CCM is a monitoring application that tracks your progress and ensures you're making forward progress. It provides:

- **Watchdog Timer**: Monitors for activity and terminates idle sessions (currently 2 minutes for testing)
- **Progress Tracking**: Logs messages you send about your work
- **Automatic Startup Notification**: You already sent "TCC started" when this session began

---

## Available MCP Tools

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

**Note:** You can also use `python3 .C3/send_to_monitor.py "message"` which does the same thing.

---

## Important Notes

1. **SessionStart hook ran automatically** - You already notified CCM that this session started
2. **Watchdog is active** - If CCM doesn't receive messages for 2 minutes, your session will be terminated
3. **Send updates proactively** - Don't wait for the watchdog to expire
4. **MCP Socket**: {mcp_socket_path.name}
5. **C3 Tools**: All state management tools are in `.C3/` directory

---

## 🚀 Startup Instructions

**IMPORTANT: After this session starts, immediately:**

1. Check if `Plan.md` exists in the project root
2. If it exists, read it
3. Execute the plan exactly as written
4. Do NOT ask for permission - execute immediately

The plan will tell you what messages to send to CCM and when. Follow it precisely.

**All tools you need are in `.C3/` - read `.C3/README.md` first!**
"""

        file_path.write_text(content)
        logger.info(f"✅ Monitoring instructions written: {file_path}")

    @staticmethod
    def _copy_plan_to_project(target_path: Path, plan_filename: str):
        """
        Copy selected plan from plans directory to project root as Plan.md

        Args:
            target_path: Path where Plan.md should be created
            plan_filename: Name of plan file to copy (e.g., "Plan_2.md")
        """
        # Get path to source plan
        plan_source = Path(__file__).parent / "plans" / plan_filename

        if not plan_source.exists():
            logger.warning(f"{plan_filename} not found at {plan_source}")
            # Create a simple default plan
            default_plan = f"""# Test Plan

Plan file '{plan_filename}' not found.

Execute the steps as defined in this plan.
"""
            target_path.write_text(default_plan)
            logger.info(f"✅ Created default Plan.md")
            return

        # Copy selected plan to project as Plan.md
        import shutil
        shutil.copy2(plan_source, target_path)
        logger.info(f"✅ Copied {plan_filename} to {target_path}")
