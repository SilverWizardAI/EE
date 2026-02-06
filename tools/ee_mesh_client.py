#!/usr/bin/env python3
"""
EE Mesh Client - Register EE instances with MM mesh and handle status polling
"""

import httpx
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EEMeshClient:
    """Client for EE instance to register with MM mesh and handle status requests"""

    def __init__(self, cycle_number: int, mesh_url: str = "http://localhost:6001"):
        self.cycle_number = cycle_number
        self.instance_name = f"ee_cycle_{cycle_number}"
        self.mesh_url = mesh_url
        self.registered = False

        # Status tracking
        self.current_step = 0
        self.current_task = "Initializing"
        self.cycle_status = "running"
        self.progress = "0%"
        self.tokens_used = 0

    def register(self) -> bool:
        """Register this EE instance with MM mesh"""
        tools = [{
            "name": "get_status",
            "description": f"Get current status of EE Cycle {self.cycle_number}",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }]

        try:
            response = httpx.post(
                f"{self.mesh_url}/register",
                json={
                    "instance_name": self.instance_name,
                    "port": 9999,  # Placeholder - EE doesn't expose real MCP server
                    "tools": tools
                },
                timeout=5.0
            )

            if response.status_code == 200:
                self.registered = True
                logger.info(f"✅ Registered {self.instance_name} with MM mesh")
                return True
            else:
                logger.error(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to register with MM mesh: {e}")
            return False

    def update_status(
        self,
        step: Optional[int] = None,
        task: Optional[str] = None,
        cycle_status: Optional[str] = None,
        progress: Optional[str] = None,
        tokens_used: Optional[int] = None
    ):
        """Update current status (will be returned by get_status tool)"""
        if step is not None:
            self.current_step = step
        if task is not None:
            self.current_task = task
        if cycle_status is not None:
            self.cycle_status = cycle_status
        if progress is not None:
            self.progress = progress
        if tokens_used is not None:
            self.tokens_used = tokens_used

    def get_status(self) -> Dict[str, Any]:
        """Get current status (called by MM mesh when EEM polls)"""
        return {
            "step": self.current_step,
            "task": self.current_task,
            "cycle_status": self.cycle_status,
            "progress": self.progress,
            "tokens_used": self.tokens_used,
            "instance": self.instance_name
        }

    def notify_monitor(self, message: str, step: Optional[int] = None) -> bool:
        """Send notification to EE monitor via MM mesh"""
        try:
            # Send to ee_monitor via mesh
            response = httpx.post(
                f"{self.mesh_url}/call",
                json={
                    "target": "ee_monitor",
                    "tool": "log_event",
                    "arguments": {
                        "event": message,
                        "step": step,
                        "source": self.instance_name
                    }
                },
                timeout=5.0
            )

            if response.status_code == 200:
                logger.debug(f"📡 Notified monitor: {message}")
                return True
            else:
                logger.warning(f"⚠️ Monitor notification failed: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"⚠️ Failed to notify monitor: {e}")
            return False

    def unregister(self) -> bool:
        """Unregister from MM mesh on shutdown"""
        if not self.registered:
            return True

        try:
            response = httpx.post(
                f"{self.mesh_url}/unregister",
                json={"instance_name": self.instance_name},
                timeout=5.0
            )

            if response.status_code == 200:
                self.registered = False
                logger.info(f"✅ Unregistered {self.instance_name} from MM mesh")
                return True
            else:
                logger.warning(f"⚠️ Unregister failed: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"⚠️ Failed to unregister: {e}")
            return False


# Singleton instance for current EE cycle
_mesh_client: Optional[EEMeshClient] = None


def init_mesh_client(cycle_number: int) -> EEMeshClient:
    """Initialize mesh client for this EE instance"""
    global _mesh_client
    _mesh_client = EEMeshClient(cycle_number)
    return _mesh_client


def get_mesh_client() -> Optional[EEMeshClient]:
    """Get current mesh client instance"""
    return _mesh_client


if __name__ == "__main__":
    # Test registration
    logging.basicConfig(level=logging.INFO)

    client = EEMeshClient(cycle_number=1)

    # Register
    if client.register():
        print(f"✅ Registered as {client.instance_name}")

        # Update status
        client.update_status(
            step=13,
            task="Testing mesh registration",
            progress="100%",
            tokens_used=15000
        )

        # Get status
        status = client.get_status()
        print(f"📊 Status: {json.dumps(status, indent=2)}")

        # Notify monitor
        client.notify_monitor("Test notification from EE instance", step=13)

        # Unregister
        client.unregister()
        print(f"✅ Unregistered from mesh")
    else:
        print(f"❌ Registration failed")
