#!/usr/bin/env python3
"""
EE Instance Server - MCP Server for Enterprise Architect

Exposes EE's status and control tools via MM mesh so EEM can monitor progress.

Architecture:
- Uses InstanceServer from MM mesh
- Registers with MM proxy on port 6001
- Exposes tools: get_status, get_progress, get_cycle_info
- Runs in background, handles calls from EEM

Usage:
    # Start server for cycle 4
    python3 tools/ee_instance_server.py --cycle 4

    # Or import and use:
    from tools.ee_instance_server import EEInstanceServer
    server = EEInstanceServer(cycle_number=4)
    server.start()  # Runs in background thread
"""

import sys
import logging
import threading
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add MM to path
mm_path = Path.home() / "Library/CloudStorage/Dropbox/A_Coding/MM"
if mm_path.exists():
    sys.path.insert(0, str(mm_path))

from mcp_mesh.instance import InstanceServer

logger = logging.getLogger(__name__)


class EEInstanceServer:
    """
    MCP Instance Server for EE cycles

    Provides real-time status updates to EEM via MM mesh.
    """

    def __init__(self, cycle_number: int):
        """
        Initialize EE instance server

        Args:
            cycle_number: Current cycle number (e.g., 4 for "ee_cycle_4")
        """
        self.cycle_number = cycle_number
        self.instance_name = f"ee_cycle_{cycle_number}"

        # Status tracking
        self.current_step = 0
        self.current_task = "Initializing"
        self.cycle_status = "running"  # running, complete, error
        self.progress = "0%"
        self.tokens_used = 0
        self.start_time = datetime.now()
        self.completed_steps = []
        self.next_action = "Starting up"

        # Create instance server
        self.server = InstanceServer(
            instance_name=self.instance_name,
            version="1.0.0"
        )

        # Register tools
        self._register_tools()

        # Server thread
        self.server_thread: Optional[threading.Thread] = None
        self.running = False

        logger.info(f"EE Instance Server initialized: {self.instance_name}")

    def _register_tools(self):
        """Register MCP tools that EEM can call"""

        @self.server.tool()
        def get_status() -> dict:
            """
            Get current EE cycle status (called by EEM heartbeat)

            Returns:
                Status dict with step, task, cycle_status, progress, tokens
            """
            uptime = (datetime.now() - self.start_time).total_seconds()

            return {
                "step": self.current_step,
                "task": self.current_task,
                "cycle_status": self.cycle_status,
                "progress": self.progress,
                "tokens_used": self.tokens_used,
                "instance": self.instance_name,
                "uptime_seconds": uptime,
                "completed_steps": self.completed_steps,
                "next_action": self.next_action
            }

        @self.server.tool()
        def get_progress() -> dict:
            """
            Get detailed progress information

            Returns:
                Detailed progress including step history
            """
            return {
                "cycle_number": self.cycle_number,
                "instance_name": self.instance_name,
                "current_step": self.current_step,
                "current_task": self.current_task,
                "status": self.cycle_status,
                "progress_percent": self.progress,
                "tokens_used": self.tokens_used,
                "steps_completed": len(self.completed_steps),
                "completed_steps": self.completed_steps,
                "next_action": self.next_action,
                "start_time": self.start_time.isoformat(),
                "uptime": (datetime.now() - self.start_time).total_seconds()
            }

        @self.server.tool()
        def get_cycle_info() -> dict:
            """
            Get cycle metadata

            Returns:
                Cycle information
            """
            return {
                "cycle_number": self.cycle_number,
                "instance_name": self.instance_name,
                "version": "1.0.0",
                "start_time": self.start_time.isoformat()
            }

    def update_status(
        self,
        step: Optional[int] = None,
        task: Optional[str] = None,
        cycle_status: Optional[str] = None,
        progress: Optional[str] = None,
        tokens_used: Optional[int] = None,
        next_action: Optional[str] = None
    ):
        """
        Update current status (called by EE as work progresses)

        Args:
            step: Current step number
            task: Current task description
            cycle_status: Cycle status (running, complete, error)
            progress: Progress percentage string
            tokens_used: Token count
            next_action: What comes next
        """
        if step is not None and step != self.current_step:
            # Step changed - record completion
            if self.current_step > 0:
                self.completed_steps.append({
                    "step": self.current_step,
                    "task": self.current_task,
                    "completed_at": datetime.now().isoformat()
                })
            self.current_step = step

        if task is not None:
            self.current_task = task
        if cycle_status is not None:
            self.cycle_status = cycle_status
        if progress is not None:
            self.progress = progress
        if tokens_used is not None:
            self.tokens_used = tokens_used
        if next_action is not None:
            self.next_action = next_action

        logger.debug(
            f"Status updated: step={self.current_step}, "
            f"task={self.current_task}, status={self.cycle_status}"
        )

    def start(self):
        """Start instance server in background thread"""
        if self.running:
            logger.warning("Server already running")
            return

        self.running = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name=f"EEInstanceServer-{self.cycle_number}"
        )
        self.server_thread.start()
        logger.info(f"Instance server started in background: {self.instance_name}")

    def _run_server(self):
        """Run server (called in background thread)"""
        try:
            logger.info(f"Starting MCP server for {self.instance_name}")
            self.server.run()
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.running = False

    def stop(self):
        """Stop instance server"""
        self.running = False
        # Update status to indicate shutdown
        self.cycle_status = "stopped"
        logger.info(f"Instance server stopped: {self.instance_name}")


# Global instance for current cycle
_current_server: Optional[EEInstanceServer] = None


def init_server(cycle_number: int) -> EEInstanceServer:
    """
    Initialize and start instance server for current cycle

    Args:
        cycle_number: Cycle number

    Returns:
        EEInstanceServer instance
    """
    global _current_server

    if _current_server:
        logger.warning("Stopping previous server")
        _current_server.stop()

    _current_server = EEInstanceServer(cycle_number)
    _current_server.start()

    return _current_server


def get_server() -> Optional[EEInstanceServer]:
    """Get current instance server"""
    return _current_server


def update_status(**kwargs):
    """Update status on current server"""
    if _current_server:
        _current_server.update_status(**kwargs)
    else:
        logger.warning("No server initialized - status update ignored")


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="EE Instance Server")
    parser.add_argument("--cycle", type=int, required=True, help="Cycle number")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Create and start server
    server = EEInstanceServer(args.cycle)
    server.start()

    print(f"✓ EE Instance Server running: {server.instance_name}")
    print(f"  Registered with MM mesh")
    print(f"  Tools: get_status, get_progress, get_cycle_info")
    print(f"  Press Ctrl+C to stop")

    # Handle shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Keep alive
    try:
        while server.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()


if __name__ == "__main__":
    main()
