#!/usr/bin/env python3
"""
Terminate Cycle - Allow TCC to unilaterally end cycle

Provides a simple way for TCC (or automation) to terminate the current
cycle without user intervention. Reports to monitor and updates status.

Module Size Target: <150 lines (Current: ~120 lines)
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))


def terminate_cycle(
    reason: str,
    cycle_number: int = None,
    tokens_used: int = None,
    send_to_monitor: bool = True,
    exit_after: bool = True
) -> dict:
    """
    Terminate the current cycle unilaterally.

    This function:
    1. Updates cycle status with termination reason
    2. Reports to monitor (if enabled)
    3. Optionally exits process (for automation)

    Args:
        reason: Reason for termination (e.g., "Token threshold exceeded")
        cycle_number: Optional cycle number (auto-detected if not provided)
        tokens_used: Optional current token count
        send_to_monitor: Whether to send notification to monitor (default: True)
        exit_after: Whether to exit process after termination (default: True)

    Returns:
        Dict with termination details
    """
    # Get current cycle number if not provided
    if cycle_number is None:
        try:
            result = subprocess.run(
                ["python3", "tools/ee_manager.py", "status"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            if result.returncode == 0:
                import json
                status = json.loads(result.stdout)
                cycle_number = status.get('cycle_number', 'unknown')
        except Exception:
            cycle_number = 'unknown'

    # Build termination message
    timestamp = datetime.now().isoformat()
    message = f"Cycle {cycle_number} closed: {reason}"

    if tokens_used:
        token_percent = (tokens_used / 200000) * 100
        message += f" (tokens: {token_percent:.1f}%)"

    # Update cycle status
    try:
        subprocess.run(
            ["python3", "tools/ee_manager.py", "update", "--cycle-end", message],
            cwd=Path(__file__).parent.parent,
            check=True
        )
        print(f"✅ Cycle status updated: {message}")
    except Exception as e:
        print(f"⚠️  Failed to update cycle status: {e}")

    # Send to monitor if enabled
    if send_to_monitor:
        try:
            subprocess.run(
                ["python3", "tools/send_to_monitor.py", f"🔴 {message}"],
                cwd=Path(__file__).parent.parent,
                check=True
            )
            print(f"✅ Monitor notified: {message}")
        except Exception as e:
            print(f"⚠️  Failed to notify monitor: {e}")

    result = {
        'status': 'terminated',
        'cycle': cycle_number,
        'reason': reason,
        'timestamp': timestamp,
        'message': message
    }

    if tokens_used:
        result['tokens_used'] = tokens_used
        result['token_percent'] = round((tokens_used / 200000) * 100, 1)

    # Exit if requested (for automation)
    if exit_after:
        print(f"\n🔴 Cycle terminated: {reason}")
        print(f"Exiting with code 0 (clean termination)")
        sys.exit(0)

    return result


def main():
    """CLI interface for cycle termination."""
    parser = argparse.ArgumentParser(
        description="Terminate Cycle - Allow TCC to unilaterally end cycle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic termination
  python3 terminate_cycle.py "Work completed"

  # With token count
  python3 terminate_cycle.py "Token threshold exceeded" --tokens 75000

  # No exit (for testing)
  python3 terminate_cycle.py "Test termination" --no-exit

  # No monitor notification (silent)
  python3 terminate_cycle.py "Silent termination" --no-monitor
        """
    )

    parser.add_argument(
        "reason",
        help="Reason for cycle termination"
    )
    parser.add_argument(
        "--tokens",
        type=int,
        help="Current token count (optional)"
    )
    parser.add_argument(
        "--cycle",
        type=int,
        help="Cycle number (auto-detected if not provided)"
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="Don't send notification to monitor"
    )
    parser.add_argument(
        "--no-exit",
        action="store_true",
        help="Don't exit process after termination (for testing)"
    )

    args = parser.parse_args()

    result = terminate_cycle(
        reason=args.reason,
        cycle_number=args.cycle,
        tokens_used=args.tokens,
        send_to_monitor=not args.no_monitor,
        exit_after=not args.no_exit
    )

    # Only reached if --no-exit was used
    import json
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
