#!/usr/bin/env python3
"""
EE Start Server - Quick startup script for EE HTTP server

This is a convenience script that EE can call to quickly start the HTTP server
and register with MM mesh.

Usage in EE:
    from tools.ee_start_server import start_ee_server
    start_ee_server(cycle_number=4)
"""

import sys
import re
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from ee_http_server import init_server, update_status, get_server


def get_current_cycle_number() -> int:
    """
    Auto-detect cycle number from git branch or status files

    Returns:
        Cycle number (defaults to 1 if not found)
    """
    try:
        # Try to get from status file
        status_file = Path(__file__).parent.parent / "status" / "cycle_status.json"
        if status_file.exists():
            import json
            with open(status_file) as f:
                data = json.load(f)
                return data.get("cycle_number", 1)
    except Exception:
        pass

    # Default to 1
    return 1


def start_ee_server(cycle_number: int = None):
    """
    Start EE HTTP server

    Args:
        cycle_number: Cycle number (auto-detected if not provided)

    Returns:
        Server instance
    """
    if cycle_number is None:
        cycle_number = get_current_cycle_number()

    print(f"🚀 Starting EE HTTP Server for Cycle {cycle_number}")
    server = init_server(cycle_number=cycle_number)

    print(f"✅ Server started: ee_cycle_{cycle_number}")
    print(f"📡 Registered with MM mesh")
    print(f"💡 Update status with: update_status(step=N, task='...', progress='X%')")
    print(f"🏁 Mark complete with: update_status(cycle_status='complete', progress='100%')")

    return server


# Auto-start if run as script
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start EE HTTP Server")
    parser.add_argument("--cycle", type=int, help="Cycle number (auto-detected if not provided)")

    args = parser.parse_args()

    server = start_ee_server(cycle_number=args.cycle)

    print("\n" + "="*60)
    print("EE HTTP Server Running")
    print("="*60)
    print(f"Instance: {server.instance_name}")
    print(f"Port: {server.port}")
    print(f"Status: {server.cycle_status}")
    print("="*60)

    # Keep alive
    try:
        import time
        while server.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
