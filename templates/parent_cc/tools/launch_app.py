"""
Launch Managed App

Launch applications as Python processes (simplified architecture).

Apps run directly with python3 main.py, no Claude instance needed.
Parent CC monitors apps via MM mesh health checks.

Module Size Target: <400 lines (Current: ~180 lines)
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

# Handle both package and script execution
try:
    from .registry import AppRegistry
except ImportError:
    from registry import AppRegistry


logger = logging.getLogger(__name__)


def launch_app(
    app_name: str,
    pcc_folder: Path,
    registry_path: Path,
    headless: bool = False,
    generate_version: bool = True
) -> dict:
    """
    Launch application as Python process.

    Args:
        app_name: Name of app to launch
        pcc_folder: Parent CC folder path
        registry_path: Path to app registry
        headless: Run in headless mode (no GUI)
        generate_version: Generate version data before launch

    Returns:
        Launch result with process info

    Example:
        result = launch_app(
            app_name="TestApp1",
            pcc_folder=Path("/A_Coding/Test_App_PCC"),
            registry_path=Path("/A_Coding/Test_App_PCC/app_registry.json")
        )
    """
    logger.info(f"Launching app: {app_name}")

    # Load registry
    registry = AppRegistry(registry_path)

    try:
        app_entry = registry.get_app(app_name)
    except ValueError:
        raise ValueError(f"App not found in registry: {app_name}")

    # Get app folder
    app_folder = pcc_folder / app_entry['folder']

    if not app_folder.exists():
        raise FileNotFoundError(f"App folder not found: {app_folder}")

    # Check if main.py exists
    main_py = app_folder / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"main.py not found in {app_folder}")

    # Generate version data if requested
    if generate_version:
        _generate_version_data(app_folder, app_name)

    # Create logs directory
    log_dir = pcc_folder / "logs"
    log_dir.mkdir(exist_ok=True)

    # Create log file for this app
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{app_name}_{timestamp}.log"

    # Build command
    cmd = ["python3", "main.py"]
    if headless:
        cmd.append("--headless")

    # Launch Python process
    with open(log_file, 'w') as log:
        process = subprocess.Popen(
            cmd,
            cwd=str(app_folder),
            stdout=log,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            start_new_session=True  # Detach from parent (proper daemon)
        )

    # Wait a moment to ensure it started
    time.sleep(0.5)

    # Check if still running
    if process.poll() is not None:
        # Process already exited
        with open(log_file) as f:
            error_output = f.read()
        raise RuntimeError(
            f"App {app_name} failed to start. Exit code: {process.returncode}\n"
            f"Log: {log_file}\n{error_output}"
        )

    # Update registry
    instance_id = f"{app_name}_{process.pid}"
    registry.update_app(app_name, {
        "process_id": process.pid,
        "instance_id": instance_id,
        "log_file": str(log_file),
        "launched_at": datetime.now().isoformat()
    })
    registry.set_status(app_name, "running")

    logger.info(f"✓ App launched: {app_name} (PID: {process.pid}, Log: {log_file})")

    return {
        "app_name": app_name,
        "instance_id": instance_id,
        "pid": process.pid,
        "status": "launched",
        "app_folder": str(app_folder),
        "log_file": str(log_file)
    }


def _generate_version_data(app_folder: Path, app_name: str):
    """
    Generate version data for app before launch.

    Args:
        app_folder: App folder path
        app_name: App name
    """
    logger.info(f"Generating version data for {app_name}")

    version_json = app_folder / "version.json"

    if not version_json.exists():
        logger.warning(f"version.json not found for {app_name}, skipping generation")
        return

    try:
        # Import version_info generator
        import sys
        version_info_path = app_folder / "version_info"
        if version_info_path.exists():
            sys.path.insert(0, str(app_folder))

            from version_info.generator import generate_version_module

            generate_version_module(
                version_json_path=str(version_json),
                update_build=True,
                auto_increment=True
            )

            logger.info(f"✓ Version data generated for {app_name}")

    except Exception as e:
        logger.warning(f"Failed to generate version data: {e}")


def stop_app(
    app_name: str,
    registry_path: Path,
    reason: str = "Manual stop"
):
    """
    Stop running application.

    Args:
        app_name: Name of app to stop
        registry_path: Path to app registry
        reason: Reason for stopping
    """
    logger.info(f"Stopping app: {app_name} (reason: {reason})")

    # Load registry
    registry = AppRegistry(registry_path)

    try:
        app_entry = registry.get_app(app_name)
    except ValueError:
        raise ValueError(f"App not found in registry: {app_name}")

    if app_entry['status'] != 'running':
        logger.warning(f"App not running: {app_name}")
        return

    # Get process ID
    pid = app_entry.get('process_id')
    if not pid:
        logger.warning(f"No process ID for {app_name}")
        return

    # Kill the Python process
    try:
        import signal
        import os

        # Try graceful shutdown first (SIGTERM)
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)

        # Check if still running
        try:
            os.kill(pid, 0)  # Check if process exists
            # Still running, force kill
            os.kill(pid, signal.SIGKILL)
            logger.warning(f"Force killed {app_name} (PID: {pid})")
        except ProcessLookupError:
            # Already exited
            pass

        # Update registry
        registry.set_status(app_name, "stopped")

        logger.info(f"✓ App stopped: {app_name} (reason: {reason})")

    except ProcessLookupError:
        logger.warning(f"Process {pid} not found (already exited)")
        registry.set_status(app_name, "stopped")

    except Exception as e:
        logger.error(f"Failed to stop app: {e}")
        raise


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Launch or stop managed app (simplified - no Claude instances)"
    )
    parser.add_argument("--app", required=True, help="App name")
    parser.add_argument(
        "--pcc-folder",
        required=True,
        help="Parent CC folder path"
    )
    parser.add_argument(
        "--registry",
        default="app_registry.json",
        help="Path to app registry"
    )
    parser.add_argument(
        "--action",
        choices=["launch", "stop"],
        default="launch",
        help="Action to perform"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run app in headless mode (no GUI)"
    )

    args = parser.parse_args()

    try:
        pcc_folder = Path(args.pcc_folder)
        registry_path = pcc_folder / args.registry

        if args.action == "launch":
            result = launch_app(
                app_name=args.app,
                pcc_folder=pcc_folder,
                registry_path=registry_path,
                headless=args.headless
            )
            print(json.dumps(result, indent=2))

        elif args.action == "stop":
            stop_app(
                app_name=args.app,
                registry_path=registry_path
            )
            print(f"✓ App stopped: {args.app}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
