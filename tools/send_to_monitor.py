#!/usr/bin/env python3
"""
Send status update to EE Monitor by writing to its log file.

The monitor displays this log file in real-time in its communications panel.

Usage:
    python tools/send_to_monitor.py "Message to send"
    python tools/send_to_monitor.py --step 8 "registry.py extracted"
"""

import sys
from pathlib import Path
from datetime import datetime


def send_to_monitor(message: str, prefix: str = "EE:") -> bool:
    """
    Send message to EE Monitor by appending to its log file.

    Args:
        message: Status message to send
        prefix: Log prefix (default: "EE:")

    Returns:
        True if successful
    """
    try:
        # Get log directory
        ee_root = Path(__file__).parent.parent
        log_dir = ee_root / "logs"
        log_dir.mkdir(exist_ok=True)

        # Get today's log file
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"ee_monitor_{today}.log"

        # Append message
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{prefix} {message}\n")

        print(f"✓ Sent to monitor: {message}")
        return True

    except Exception as e:
        print(f"✗ Error writing to monitor log: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/send_to_monitor.py [--step N] <message>")
        print("Examples:")
        print("  python tools/send_to_monitor.py 'Cycle 1 started'")
        print("  python tools/send_to_monitor.py --step 8 'registry.py extracted'")
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    prefix = "EE:"

    if args[0] == "--step" and len(args) >= 3:
        step_num = args[1]
        message = f"✅ Step {step_num}: {' '.join(args[2:])}"
    else:
        message = " ".join(args)

    success = send_to_monitor(message, prefix)
    sys.exit(0 if success else 1)
