"""
Spawn Claude Instance

Spawn Claude Code instances for managed applications.

Module Size Target: <400 lines (Current: ~200 lines)
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


def spawn_claude_instance(
    app_folder: Path,
    app_name: str,
    initial_prompt: Optional[str] = None,
    background: bool = True
) -> Dict[str, Any]:
    """
    Spawn Claude Code instance for an application.

    Args:
        app_folder: Path to app folder
        app_name: Name of the app
        initial_prompt: Optional initial prompt to send
        background: Run in background (default: True)

    Returns:
        Dict with instance_id and status

    Example:
        result = spawn_claude_instance(
            app_folder=Path("/A_Coding/Test_App_PCC/apps/TestApp1"),
            app_name="TestApp1",
            initial_prompt="Run the application and monitor for issues"
        )
    """
    logger.info(f"Spawning Claude instance for: {app_name}")

    if not app_folder.exists():
        raise FileNotFoundError(f"App folder not found: {app_folder}")

    # Build claude command
    cmd = ["claude", "code"]

    # Add working directory
    cmd.extend(["--cwd", str(app_folder)])

    # Add initial prompt if provided
    if initial_prompt:
        cmd.extend(["--prompt", initial_prompt])

    # Spawn the process
    try:
        if background:
            # Start in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(app_folder)
            )

            instance_id = f"{app_name}_{process.pid}"

            logger.info(f"✓ Claude instance spawned: {instance_id} (PID: {process.pid})")

            return {
                "instance_id": instance_id,
                "pid": process.pid,
                "status": "running",
                "app_name": app_name,
                "app_folder": str(app_folder)
            }
        else:
            # Run in foreground (blocking)
            result = subprocess.run(
                cmd,
                cwd=str(app_folder),
                capture_output=True,
                text=True
            )

            logger.info(f"✓ Claude instance completed: {app_name}")

            return {
                "instance_id": f"{app_name}_completed",
                "status": "completed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "app_name": app_name
            }

    except Exception as e:
        logger.error(f"Failed to spawn Claude instance: {e}")
        raise


def check_instance_status(instance_id: str, pid: int) -> str:
    """
    Check if Claude instance is still running.

    Args:
        instance_id: Instance ID
        pid: Process ID

    Returns:
        Status (running, stopped)
    """
    try:
        # Check if process exists
        subprocess.run(
            ["ps", "-p", str(pid)],
            capture_output=True,
            check=True
        )
        return "running"
    except subprocess.CalledProcessError:
        return "stopped"


def stop_instance(instance_id: str, pid: int):
    """
    Stop Claude instance gracefully.

    Args:
        instance_id: Instance ID
        pid: Process ID
    """
    logger.info(f"Stopping Claude instance: {instance_id}")

    try:
        # Send SIGTERM for graceful shutdown
        subprocess.run(["kill", "-TERM", str(pid)], check=True)
        logger.info(f"✓ Instance stopped: {instance_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop instance: {e}")
        raise


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Spawn Claude instance for app")
    parser.add_argument("--app-folder", required=True, help="App folder path")
    parser.add_argument("--app-name", required=True, help="App name")
    parser.add_argument("--prompt", help="Initial prompt")
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="Run in foreground (default: background)"
    )

    args = parser.parse_args()

    try:
        result = spawn_claude_instance(
            app_folder=Path(args.app_folder),
            app_name=args.app_name,
            initial_prompt=args.prompt,
            background=not args.foreground
        )

        print(json.dumps(result, indent=2))
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
