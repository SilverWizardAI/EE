"""
App Registry Management

Track and manage all applications under Parent CC control.

Module Size Target: <400 lines (Current: ~250 lines)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class AppRegistry:
    """
    Central registry for all managed applications.

    Tracks:
    - App metadata (name, created, template, etc.)
    - App status (running, stopped, healthy, etc.)
    - Health check history
    - Assistance request history
    """

    def __init__(self, registry_path: Path):
        """
        Initialize app registry.

        Args:
            registry_path: Path to app_registry.json
        """
        self.registry_path = Path(registry_path)
        self.data = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")

        with open(self.registry_path, 'r') as f:
            return json.load(f)

    def _save_registry(self):
        """Save registry to disk."""
        with open(self.registry_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        logger.info(f"Registry saved: {self.registry_path}")

    def add_app(
        self,
        name: str,
        template: str,
        folder: str,
        mesh_service: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add new app to registry.

        Args:
            name: App name
            template: Template type used
            folder: App folder path (relative to PCC folder)
            mesh_service: MM mesh service name
            metadata: Optional additional metadata

        Returns:
            App entry
        """
        if name in self.data['apps']:
            raise ValueError(f"App already exists: {name}")

        app_entry = {
            "name": name,
            "created": datetime.now().isoformat(),
            "template": template,
            "status": "created",
            "mesh_service": mesh_service,
            "folder": folder,
            "claude_instance_id": None,
            "health": {
                "last_check": None,
                "status": "unknown",
                "uptime": 0,
                "error_count": 0
            },
            "metadata": metadata or {}
        }

        self.data['apps'][name] = app_entry
        self.data['statistics']['total_apps'] += 1
        self._save_registry()

        logger.info(f"App added to registry: {name}")
        return app_entry

    def update_app(self, name: str, updates: Dict[str, Any]):
        """
        Update app entry.

        Args:
            name: App name
            updates: Fields to update
        """
        if name not in self.data['apps']:
            raise ValueError(f"App not found: {name}")

        self.data['apps'][name].update(updates)
        self._save_registry()

        logger.info(f"App updated: {name}")

    def update_health(
        self,
        name: str,
        status: str,
        uptime: int = 0,
        error_count: int = 0
    ):
        """
        Update app health status.

        Args:
            name: App name
            status: Health status (healthy, degraded, unhealthy)
            uptime: Uptime in seconds
            error_count: Number of errors
        """
        if name not in self.data['apps']:
            raise ValueError(f"App not found: {name}")

        self.data['apps'][name]['health'] = {
            "last_check": datetime.now().isoformat(),
            "status": status,
            "uptime": uptime,
            "error_count": error_count
        }

        self._save_registry()
        self.data['statistics']['total_health_checks'] += 1

    def set_claude_instance(self, name: str, instance_id: str):
        """
        Set Claude instance ID for app.

        Args:
            name: App name
            instance_id: Claude instance ID
        """
        self.update_app(name, {"claude_instance_id": instance_id})

    def set_status(self, name: str, status: str):
        """
        Update app status.

        Args:
            name: App name
            status: New status (created, running, stopped, error)
        """
        self.update_app(name, {"status": status})

        # Update statistics
        if status == "running":
            self.data['statistics']['running_apps'] = sum(
                1 for app in self.data['apps'].values()
                if app['status'] == 'running'
            )
        elif status == "stopped":
            self.data['statistics']['stopped_apps'] = sum(
                1 for app in self.data['apps'].values()
                if app['status'] == 'stopped'
            )

        self._save_registry()

    def get_app(self, name: str) -> Dict[str, Any]:
        """Get app entry by name."""
        if name not in self.data['apps']:
            raise ValueError(f"App not found: {name}")
        return self.data['apps'][name]

    def get_all_apps(self) -> Dict[str, Dict[str, Any]]:
        """Get all apps."""
        return self.data['apps']

    def get_running_apps(self) -> List[str]:
        """Get list of running app names."""
        return [
            name for name, app in self.data['apps'].items()
            if app['status'] == 'running'
        ]

    def get_unhealthy_apps(self) -> List[str]:
        """Get list of unhealthy app names."""
        return [
            name for name, app in self.data['apps'].items()
            if app['health']['status'] in ('degraded', 'unhealthy')
        ]

    def record_assistance_request(self, app_name: str):
        """Record that an assistance request was made."""
        self.data['statistics']['total_assistance_requests'] += 1
        self._save_registry()

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return self.data['statistics']

    def remove_app(self, name: str):
        """
        Remove app from registry.

        Args:
            name: App name
        """
        if name not in self.data['apps']:
            raise ValueError(f"App not found: {name}")

        del self.data['apps'][name]
        self.data['statistics']['total_apps'] -= 1
        self._save_registry()

        logger.info(f"App removed from registry: {name}")

    def list_apps(self, format: str = "table") -> str:
        """
        List all apps in formatted output.

        Args:
            format: Output format (table, json, simple)

        Returns:
            Formatted app list
        """
        if format == "json":
            return json.dumps(self.data['apps'], indent=2)

        if format == "simple":
            return "\n".join(self.data['apps'].keys())

        # Table format
        lines = []
        lines.append("=" * 80)
        lines.append(f"{'Name':<20} {'Status':<12} {'Health':<12} {'Template':<15}")
        lines.append("=" * 80)

        for name, app in sorted(self.data['apps'].items()):
            lines.append(
                f"{name:<20} {app['status']:<12} "
                f"{app['health']['status']:<12} {app['template']:<15}"
            )

        lines.append("=" * 80)
        lines.append(f"Total: {self.data['statistics']['total_apps']} apps")
        lines.append(f"Running: {self.data['statistics']['running_apps']}")
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Command-line interface for registry management."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Manage app registry")
    parser.add_argument(
        "--registry",
        default="app_registry.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all apps"
    )
    parser.add_argument(
        "--check-health",
        metavar="APP",
        help="Check health of specific app"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics"
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "simple"],
        default="table",
        help="Output format"
    )

    args = parser.parse_args()

    try:
        registry = AppRegistry(args.registry)

        if args.list:
            print(registry.list_apps(format=args.format))

        elif args.check_health:
            app = registry.get_app(args.check_health)
            print(json.dumps(app['health'], indent=2))

        elif args.stats:
            print(json.dumps(registry.get_statistics(), indent=2))

        else:
            parser.print_help()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
