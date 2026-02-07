"""
MCP Project Setup Utility

Instruments Claude Code projects with MCP (Model Context Protocol) configuration
and permissions. Safely backs up existing configurations and provides cleanup.

EXTRACTED FROM: C3 project (services/instrumentation_service.py + services/terminal_manager.py)
VALIDATION: Proven in C3's multi-terminal orchestration

Key Features:
- ✅ Creates/updates .mcp.json with MCP server configuration
- ✅ Configures settings.local.json with tool permissions
- ✅ Backs up existing files (reversible)
- ✅ Adds C3 patterns to .gitignore
- ✅ Validates configuration after setup
- ✅ Provides cleanup/restoration

Usage:
    from library.mcp_project_setup import setup_mcp_for_project, cleanup_mcp_from_project

    # Setup MCP in target project
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
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys

logger = logging.getLogger(__name__)


@dataclass
class MCPSetupResult:
    """Result of MCP setup operation"""
    success: bool
    modified_files: List[str]
    backed_up_files: List[str]
    error: Optional[str] = None


@dataclass
class MCPCleanupResult:
    """Result of MCP cleanup operation"""
    success: bool
    removed_files: List[str]
    restored_files: List[str]
    error: Optional[str] = None


def setup_mcp_for_project(
    project_path: Path,
    mcp_server_script: Path,
    server_name: str,
    tool_name: Optional[str] = None,
    python_executable: Optional[str] = None,
    backup_suffix: str = ".mcp_backup",
    add_to_gitignore: bool = True
) -> MCPSetupResult:
    """
    Setup MCP server configuration in target Claude Code project.

    This function instruments a Claude Code project with:
    1. .mcp.json - MCP server configuration
    2. settings.local.json - Tool permissions
    3. .gitignore - Ignore MCP artifacts (optional)

    All modifications are backed up and reversible via cleanup_mcp_from_project().

    Args:
        project_path: Path to target Claude Code project
        mcp_server_script: Path to MCP server stdio script (e.g., my_mcp_server_stdio.py)
        server_name: MCP server name (e.g., "my-server", will appear as mcp__my-server__...)
        tool_name: Tool name (e.g., "my_command", if None defaults to "command")
        python_executable: Python to use (defaults to sys.executable)
        backup_suffix: Suffix for backup files (default: ".mcp_backup")
        add_to_gitignore: Whether to add MCP artifacts to .gitignore

    Returns:
        MCPSetupResult with success status and details

    Example:
        result = setup_mcp_for_project(
            project_path=Path("/Users/me/myproject"),
            mcp_server_script=Path("/Users/me/EE/my_mcp_server_stdio.py"),
            server_name="my-server",
            tool_name="my_command"
        )

        if result.success:
            print(f"✅ Setup complete!")
            print(f"Modified: {result.modified_files}")
            print(f"Backed up: {result.backed_up_files}")
        else:
            print(f"❌ Setup failed: {result.error}")
    """
    modified = []
    backed_up = []

    try:
        # Validate inputs
        if not project_path.exists():
            return MCPSetupResult(
                success=False,
                modified_files=[],
                backed_up_files=[],
                error=f"Project path does not exist: {project_path}"
            )

        if not mcp_server_script.exists():
            return MCPSetupResult(
                success=False,
                modified_files=[],
                backed_up_files=[],
                error=f"MCP server script not found: {mcp_server_script}"
            )

        # Default values
        if tool_name is None:
            tool_name = "command"

        if python_executable is None:
            python_executable = sys.executable

        # Ensure .claude directory exists
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)

        # 1. Setup .mcp.json
        mcp_result = _setup_mcp_json(
            project_path=project_path,
            mcp_server_script=mcp_server_script,
            server_name=server_name,
            python_executable=python_executable,
            backup_suffix=backup_suffix
        )
        modified.extend(mcp_result['modified'])
        backed_up.extend(mcp_result['backed_up'])

        # 2. Configure permissions in settings.local.json
        perm_result = _setup_permissions(
            project_path=project_path,
            server_name=server_name,
            tool_name=tool_name,
            backup_suffix=backup_suffix
        )
        modified.extend(perm_result['modified'])
        backed_up.extend(perm_result['backed_up'])

        # 3. Add to .gitignore (optional)
        if add_to_gitignore:
            gitignore_result = _add_to_gitignore(
                project_path=project_path,
                backup_suffix=backup_suffix
            )
            modified.extend(gitignore_result['modified'])
            backed_up.extend(gitignore_result['backed_up'])

        # 4. Validate setup
        if not _validate_mcp_setup(project_path, server_name):
            # Rollback on validation failure
            logger.error(f"MCP setup validation failed for {project_path}")
            _rollback_setup(project_path, modified, backed_up, backup_suffix)
            return MCPSetupResult(
                success=False,
                modified_files=modified,
                backed_up_files=backed_up,
                error="Validation failed: MCP configuration not accessible"
            )

        logger.info(f"MCP setup completed successfully for {project_path}")
        logger.info(f"  Server: {server_name}")
        logger.info(f"  Tool: mcp__{server_name}__{tool_name}")
        logger.info(f"  Modified: {len(modified)} files")
        logger.info(f"  Backed up: {len(backed_up)} files")

        return MCPSetupResult(
            success=True,
            modified_files=modified,
            backed_up_files=backed_up
        )

    except Exception as e:
        logger.error(f"MCP setup failed: {e}")
        # Rollback on error
        _rollback_setup(project_path, modified, backed_up, backup_suffix)
        return MCPSetupResult(
            success=False,
            modified_files=modified,
            backed_up_files=backed_up,
            error=str(e)
        )


def cleanup_mcp_from_project(
    project_path: Path,
    backup_suffix: str = ".mcp_backup"
) -> MCPCleanupResult:
    """
    Remove MCP instrumentation from project and restore original files.

    Reverses changes made by setup_mcp_for_project():
    1. Removes or restores .mcp.json
    2. Removes or restores settings.local.json
    3. Removes or restores .gitignore

    Args:
        project_path: Path to target project
        backup_suffix: Backup suffix used during setup (default: ".mcp_backup")

    Returns:
        MCPCleanupResult with success status and details

    Example:
        result = cleanup_mcp_from_project(
            project_path=Path("/Users/me/myproject")
        )

        if result.success:
            print(f"✅ Cleanup complete!")
            print(f"Removed: {result.removed_files}")
            print(f"Restored: {result.restored_files}")
        else:
            print(f"❌ Cleanup failed: {result.error}")
    """
    removed = []
    restored = []

    try:
        if not project_path.exists():
            return MCPCleanupResult(
                success=False,
                removed_files=[],
                restored_files=[],
                error=f"Project path does not exist: {project_path}"
            )

        # 1. Restore or remove .mcp.json
        mcp_config = project_path / ".mcp.json"
        mcp_backup = project_path / f".mcp.json{backup_suffix}"

        if mcp_backup.exists():
            # Restore from backup
            shutil.copy(mcp_backup, mcp_config)
            mcp_backup.unlink()
            restored.append(".mcp.json")
            removed.append(f".mcp.json{backup_suffix}")
        elif mcp_config.exists():
            # No backup, just remove (was created by setup)
            mcp_config.unlink()
            removed.append(".mcp.json")

        # 2. Restore or remove settings.local.json
        settings_path = project_path / ".claude" / "settings.local.json"
        settings_backup = project_path / ".claude" / f"settings.local.json{backup_suffix}"

        if settings_backup.exists():
            # Restore from backup
            shutil.copy(settings_backup, settings_path)
            settings_backup.unlink()
            restored.append(".claude/settings.local.json")
            removed.append(f".claude/settings.local.json{backup_suffix}")
        # Note: We don't remove settings.local.json if no backup exists
        # as it may contain other user settings

        # 3. Restore or clean .gitignore
        gitignore_path = project_path / ".claude" / ".gitignore"
        gitignore_backup = project_path / ".claude" / f".gitignore{backup_suffix}"

        if gitignore_backup.exists():
            # Restore from backup
            shutil.copy(gitignore_backup, gitignore_path)
            gitignore_backup.unlink()
            restored.append(".claude/.gitignore")
            removed.append(f".claude/.gitignore{backup_suffix}")
        elif gitignore_path.exists():
            # Remove MCP patterns from .gitignore
            _remove_mcp_from_gitignore(gitignore_path)
            restored.append(".claude/.gitignore (cleaned)")

        logger.info(f"MCP cleanup completed successfully for {project_path}")
        logger.info(f"  Removed: {len(removed)} items")
        logger.info(f"  Restored: {len(restored)} items")

        return MCPCleanupResult(
            success=True,
            removed_files=removed,
            restored_files=restored
        )

    except Exception as e:
        logger.error(f"MCP cleanup failed: {e}")
        return MCPCleanupResult(
            success=False,
            removed_files=removed,
            restored_files=restored,
            error=str(e)
        )


# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================

def _setup_mcp_json(
    project_path: Path,
    mcp_server_script: Path,
    server_name: str,
    python_executable: str,
    backup_suffix: str
) -> dict:
    """Setup .mcp.json configuration"""
    modified = []
    backed_up = []

    mcp_config_path = project_path / ".mcp.json"
    mcp_backup_path = project_path / f".mcp.json{backup_suffix}"

    # Backup existing .mcp.json if it exists and no backup exists yet
    if mcp_config_path.exists() and not mcp_backup_path.exists():
        shutil.copy(mcp_config_path, mcp_backup_path)
        backed_up.append(f".mcp.json{backup_suffix}")
        logger.info(f"Backed up existing .mcp.json")

    # Create MCP config
    mcp_config = {
        "mcpServers": {
            server_name: {
                "command": python_executable,
                "args": [str(mcp_server_script.resolve())]
            }
        }
    }

    # Write config
    mcp_config_path.write_text(json.dumps(mcp_config, indent=2) + "\n")
    modified.append(".mcp.json")
    logger.info(f"Created .mcp.json for server '{server_name}'")

    return {"modified": modified, "backed_up": backed_up}


def _setup_permissions(
    project_path: Path,
    server_name: str,
    tool_name: str,
    backup_suffix: str
) -> dict:
    """Setup permissions in settings.local.json"""
    modified = []
    backed_up = []

    settings_path = project_path / ".claude" / "settings.local.json"
    settings_backup_path = project_path / ".claude" / f"settings.local.json{backup_suffix}"

    # Load existing settings or create new
    if settings_path.exists():
        # Backup existing settings if no backup exists yet
        if not settings_backup_path.exists():
            shutil.copy(settings_path, settings_backup_path)
            backed_up.append(f".claude/settings.local.json{backup_suffix}")
            logger.info(f"Backed up existing settings.local.json")

        try:
            settings = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read settings.local.json: {e}, creating new")
            settings = {}
    else:
        settings = {}

    # Ensure permissions structure exists
    if 'permissions' not in settings:
        settings['permissions'] = {}
    if 'allow' not in settings['permissions']:
        settings['permissions']['allow'] = []

    # Add MCP tool permission if not present
    mcp_tool_permission = f"mcp__{server_name}__{tool_name}"
    if mcp_tool_permission not in settings['permissions']['allow']:
        settings['permissions']['allow'].append(mcp_tool_permission)
        logger.info(f"Added MCP tool permission: {mcp_tool_permission}")

    # Ensure enabledMcpjsonServers exists
    if 'enabledMcpjsonServers' not in settings:
        settings['enabledMcpjsonServers'] = []

    # Add server if not present
    if server_name not in settings['enabledMcpjsonServers']:
        settings['enabledMcpjsonServers'].append(server_name)
        logger.info(f"Enabled MCP server: {server_name}")

    # Write updated settings
    settings_path.parent.mkdir(exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    modified.append(".claude/settings.local.json")

    return {"modified": modified, "backed_up": backed_up}


def _add_to_gitignore(
    project_path: Path,
    backup_suffix: str
) -> dict:
    """Add MCP artifacts to .gitignore"""
    modified = []
    backed_up = []

    gitignore_path = project_path / ".claude" / ".gitignore"
    gitignore_backup_path = project_path / ".claude" / f".gitignore{backup_suffix}"

    mcp_patterns = [
        "# MCP artifacts - auto-generated",
        "*.mcp_backup",
        "mcp_temp/",
        "",  # Blank line
    ]

    if gitignore_path.exists():
        # Read existing .gitignore
        existing = gitignore_path.read_text()

        # Check if MCP section already exists
        if "# MCP artifacts" in existing:
            return {"modified": [], "backed_up": []}  # Already configured

        # Backup if no backup exists yet
        if not gitignore_backup_path.exists():
            shutil.copy(gitignore_path, gitignore_backup_path)
            backed_up.append(f".claude/.gitignore{backup_suffix}")
            logger.info(f"Backed up existing .gitignore")

        # Append MCP patterns
        updated = existing.rstrip() + "\n\n" + "\n".join(mcp_patterns)
        gitignore_path.write_text(updated)
        modified.append(".claude/.gitignore")
    else:
        # Create new .gitignore with MCP patterns
        gitignore_path.parent.mkdir(exist_ok=True)
        gitignore_path.write_text("\n".join(mcp_patterns))
        modified.append(".claude/.gitignore")

    logger.info(f"Added MCP patterns to .gitignore")

    return {"modified": modified, "backed_up": backed_up}


def _validate_mcp_setup(project_path: Path, server_name: str) -> bool:
    """Validate that MCP setup is correct"""
    # Check .mcp.json exists and contains server
    mcp_config_path = project_path / ".mcp.json"
    if not mcp_config_path.exists():
        logger.error("Validation failed: .mcp.json not found")
        return False

    try:
        config = json.loads(mcp_config_path.read_text())
        if "mcpServers" not in config or server_name not in config["mcpServers"]:
            logger.error(f"Validation failed: server '{server_name}' not in .mcp.json")
            return False
    except Exception as e:
        logger.error(f"Validation failed: cannot parse .mcp.json: {e}")
        return False

    # Check settings.local.json exists and has permissions
    settings_path = project_path / ".claude" / "settings.local.json"
    if not settings_path.exists():
        logger.error("Validation failed: settings.local.json not found")
        return False

    try:
        settings = json.loads(settings_path.read_text())
        if server_name not in settings.get("enabledMcpjsonServers", []):
            logger.error(f"Validation failed: server '{server_name}' not enabled in settings")
            return False
    except Exception as e:
        logger.error(f"Validation failed: cannot parse settings.local.json: {e}")
        return False

    logger.info("Validation passed")
    return True


def _rollback_setup(
    project_path: Path,
    modified: List[str],
    backed_up: List[str],
    backup_suffix: str
):
    """Rollback changes on setup failure"""
    logger.info("Rolling back MCP setup changes...")

    # Restore backed-up files
    for backup_rel_path in backed_up:
        backup_path = project_path / backup_rel_path
        # Remove backup_suffix to get original path
        original_rel_path = backup_rel_path.replace(backup_suffix, "")
        original_path = project_path / original_rel_path

        if backup_path.exists():
            shutil.copy(backup_path, original_path)
            backup_path.unlink()
            logger.info(f"  Restored {original_rel_path}")

    # Remove modified files that have no backup (newly created)
    for modified_rel_path in modified:
        if modified_rel_path not in [b.replace(backup_suffix, "") for b in backed_up]:
            modified_path = project_path / modified_rel_path
            if modified_path.exists():
                modified_path.unlink()
                logger.info(f"  Removed {modified_rel_path}")


def _remove_mcp_from_gitignore(gitignore_path: Path):
    """Remove MCP artifact patterns from .gitignore"""
    if not gitignore_path.exists():
        return

    try:
        content = gitignore_path.read_text()
        lines = content.split('\n')

        # Find and remove MCP section
        cleaned_lines = []
        in_mcp_section = False

        for line in lines:
            # Detect start of MCP section
            if "# MCP artifacts" in line:
                in_mcp_section = True
                continue

            # Skip lines in MCP section
            if in_mcp_section:
                # MCP patterns: *.mcp_backup, mcp_temp/
                if any(pattern in line for pattern in ["*.mcp_backup", "mcp_temp/"]):
                    continue
                # End of MCP section (blank line)
                if not line.strip():
                    in_mcp_section = False
                    continue

            cleaned_lines.append(line)

        # Write cleaned content
        cleaned_content = '\n'.join(cleaned_lines).strip() + '\n'
        gitignore_path.write_text(cleaned_content)
        logger.info("Removed MCP patterns from .gitignore")

    except Exception as e:
        logger.warning(f"Could not clean .gitignore: {e}")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test MCP project setup
    """
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("MCP Project Setup Test")
    print("=" * 70)

    # Get test project path
    if len(sys.argv) > 1:
        test_project = Path(sys.argv[1])
    else:
        test_project = Path.cwd() / "test_project"
        test_project.mkdir(exist_ok=True)

    print(f"\nTest project: {test_project}")

    # Create dummy MCP server script for testing
    dummy_server = test_project.parent / "dummy_mcp_server.py"
    dummy_server.write_text("#!/usr/bin/env python3\nprint('Dummy MCP server')\n")

    print(f"Dummy server: {dummy_server}")

    # Test setup
    print("\n" + "=" * 70)
    print("Testing MCP Setup")
    print("=" * 70)

    result = setup_mcp_for_project(
        project_path=test_project,
        mcp_server_script=dummy_server,
        server_name="test-server",
        tool_name="test_command"
    )

    print(f"\nSetup result:")
    print(f"  Success: {result.success}")
    print(f"  Modified: {result.modified_files}")
    print(f"  Backed up: {result.backed_up_files}")
    if result.error:
        print(f"  Error: {result.error}")

    # Test cleanup
    input("\nPress ENTER to test cleanup...")

    print("\n" + "=" * 70)
    print("Testing MCP Cleanup")
    print("=" * 70)

    cleanup_result = cleanup_mcp_from_project(project_path=test_project)

    print(f"\nCleanup result:")
    print(f"  Success: {cleanup_result.success}")
    print(f"  Removed: {cleanup_result.removed_files}")
    print(f"  Restored: {cleanup_result.restored_files}")
    if cleanup_result.error:
        print(f"  Error: {cleanup_result.error}")

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)
