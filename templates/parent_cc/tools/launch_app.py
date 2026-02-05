"""
Launch Managed App

Launch applications and spawn Claude instances for them.

Module Size Target: <400 lines (Current: ~250 lines)
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from .registry import AppRegistry
from .spawn_claude import spawn_claude_instance


logger = logging.getLogger(__name__)


def launch_app(
    app_name: str,
    pcc_folder: Path,
    registry_path: Path,
    initial_prompt: Optional[str] = None,
    generate_version: bool = True
) -> dict:
    """
    Launch application and spawn Claude instance.

    Args:
        app_name: Name of app to launch
        pcc_folder: Parent CC folder path
        registry_path: Path to app registry
        initial_prompt: Optional initial prompt for Claude instance
        generate_version: Generate version data before launch

    Returns:
        Launch result with instance info

    Example:
        result = launch_app(
            app_name="TestApp1",
            pcc_folder=Path("/A_Coding/Test_App_PCC"),
            registry_path=Path("/A_Coding/Test_App_PCC/app_registry.json"),
            initial_prompt="Run the application"
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

    # Generate version data if requested
    if generate_version:
        _generate_version_data(app_folder, app_name)

    # Build initial prompt if not provided
    if not initial_prompt:
        initial_prompt = _build_initial_prompt(app_name, app_entry)

    # Spawn Claude instance
    instance_info = spawn_claude_instance(
        app_folder=app_folder,
        app_name=app_name,
        initial_prompt=initial_prompt,
        background=True
    )

    # Update registry
    registry.set_claude_instance(app_name, instance_info['instance_id'])
    registry.set_status(app_name, "running")

    logger.info(f"✓ App launched: {app_name} ({instance_info['instance_id']})")

    return {
        "app_name": app_name,
        "instance_id": instance_info['instance_id'],
        "pid": instance_info['pid'],
        "status": "launched",
        "app_folder": str(app_folder)
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


def _build_initial_prompt(app_name: str, app_entry: dict) -> str:
    """
    Build initial prompt for Claude instance.

    Args:
        app_name: App name
        app_entry: App registry entry

    Returns:
        Initial prompt
    """
    template = app_entry.get('template', 'unknown')
    features = app_entry.get('metadata', {}).get('features', [])

    prompt = f"""You are managing the {app_name} application.

App Details:
- Name: {app_name}
- Template: {template}
- Features: {', '.join(features) if features else 'standard'}

Your tasks:
1. Review the application code and structure
2. Run the application (execute main.py if it exists)
3. Monitor for errors or issues
4. Respond to any assistance requests from Parent CC
5. Keep the app running and healthy

Remember:
- You are an autonomous app instance
- Report issues to Parent CC via MM mesh
- Request help when you encounter complex situations
- Keep modules under 400 lines

Start the application now.
"""

    return prompt


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

    instance_id = app_entry.get('claude_instance_id')
    if not instance_id:
        logger.warning(f"No Claude instance ID for {app_name}")
        return

    # Extract PID from instance_id (format: appname_pid)
    try:
        pid = int(instance_id.split('_')[-1])

        from .spawn_claude import stop_instance
        stop_instance(instance_id, pid)

        # Update registry
        registry.set_status(app_name, "stopped")

        logger.info(f"✓ App stopped: {app_name}")

    except Exception as e:
        logger.error(f"Failed to stop app: {e}")
        raise


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Launch or stop managed app")
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
        "--prompt",
        help="Initial prompt for launch"
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
                initial_prompt=args.prompt
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
