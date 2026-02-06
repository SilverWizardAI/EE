#!/usr/bin/env python3
"""
EE Startup Script

Run this on every EE startup to:
- Check cycle status
- Detect handoffs from previous instance
- Report what to do next
- Provide context for current work

Module Size Target: <400 lines (Current: ~200 lines)
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from ee_manager import EEManager


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to readable string."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_timestamp


def print_banner(text: str, width: int = 70):
    """Print a banner."""
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70)


def get_token_status_indicator(tokens: int, budget: int = 200000) -> str:
    """Get visual indicator for token status."""
    percentage = (tokens / budget) * 100

    if percentage < 50:
        return "✅ HEALTHY"
    elif percentage < 70:
        return "🟡 MODERATE"
    elif percentage < 85:
        return "🟠 PREPARE HANDOFF"
    else:
        return "🔴 HANDOFF NEEDED"


def main():
    """Run EE startup sequence."""
    manager = EEManager()

    print_banner("🏛️  SILVER WIZARD SOFTWARE - ENTERPRISE EDITION")
    print_banner("EE STARTUP SEQUENCE")

    # Get startup info
    startup_info = manager.get_startup_info()
    cycle_status = startup_info.get("cycle_status")
    handoff_signal = startup_info.get("handoff_signal")
    is_handoff = startup_info.get("is_handoff", False)

    # HANDOFF DETECTION
    if is_handoff:
        print_section("🔄 HANDOFF DETECTED")
        print(f"  Previous Cycle: {handoff_signal.get('cycle', 'Unknown')}")
        print(f"  This Cycle: {handoff_signal.get('next_cycle', 'Unknown')}")
        print(f"  Previous Tokens: {handoff_signal.get('tokens', 'Unknown')}")
        print(f"  Handoff Time: {handoff_signal.get('timestamp', 'Unknown')}")
        print(f"\n  📋 Next Task: {handoff_signal.get('next_task', 'Unknown')}")

        # Start new cycle from handoff
        if handoff_signal.get('next_task'):
            prev_cycle = handoff_signal.get('cycle')
            if prev_cycle:
                try:
                    prev_cycle_num = int(prev_cycle.split('→')[0].strip())
                    new_status = manager.start_new_cycle(
                        task=handoff_signal['next_task'],
                        previous_cycle=prev_cycle_num
                    )
                    cycle_status = new_status.__dict__
                except:
                    pass

        # Clear handoff signal
        manager.clear_handoff_signal()
        print("\n  ✅ Handoff signal processed and cleared")

    # CYCLE STATUS
    print_section("📊 CYCLE STATUS")

    if cycle_status:
        print(f"  Cycle Number: {cycle_status['cycle_number']}")
        print(f"  Started: {format_timestamp(cycle_status['started_at'])}")
        print(f"  Last Updated: {format_timestamp(cycle_status['last_updated'])}")
        print(f"\n  Current Task: {cycle_status['current_task']}")

        # Tasks completed
        if cycle_status['tasks_completed']:
            print(f"\n  Completed Tasks:")
            for task in cycle_status['tasks_completed']:
                print(f"    ✅ {task}")
        else:
            print(f"\n  Completed Tasks: None yet")

        print(f"\n  Next Action: {cycle_status['next_action']}")

    else:
        print("  ⚠️  No active cycle found")
        print("  This appears to be a fresh start")

    # TOKEN BUDGET
    print_section("🎫 TOKEN BUDGET")

    token_budget = cycle_status['token_budget'] if cycle_status else 200000
    token_threshold = cycle_status['token_threshold'] if cycle_status else 170000

    print(f"  Budget: {token_budget:,} tokens")
    print(f"  Handoff Threshold: {token_threshold:,} tokens (85%)")
    print(f"\n  Current Usage: [Check your actual usage]")
    print(f"  Status: Monitor as you work")

    # WHAT TO DO NEXT
    print_section("🎯 WHAT TO DO NEXT")

    if is_handoff and handoff_signal:
        print(f"  📋 Resume: {handoff_signal.get('next_task', 'Check IMMEDIATE_NEXT.md')}")
        print(f"\n  You are continuing work from Cycle {handoff_signal.get('cycle', '?')}")
        print(f"  Continue where the previous instance left off.")

    elif cycle_status and cycle_status.get('next_action'):
        print(f"  📋 Current: {cycle_status['next_action']}")

    else:
        print(f"  📋 Check: plans/IMMEDIATE_NEXT.md for current priorities")
        print(f"  📋 Review: status/COMPLETED.md for recent work")

    # REMINDERS
    print_section("⚠️  REMINDERS")
    print(f"  • Monitor token usage throughout work")
    print(f"  • At ~85% (170K tokens): Run handoff protocol")
    print(f"  • Update progress: python3 tools/ee_manager.py update")
    print(f"  • Check status: python3 tools/ee_manager.py status")

    # HANDOFF COMMAND REFERENCE
    print_section("🔄 HANDOFF PROTOCOL (When needed)")
    print(f"  When you reach 85% tokens (~170K), run:")
    print(f"")
    print(f"  python3 tools/ee_manager.py handoff \\")
    print(f"    --tokens <your_current_tokens> \\")
    print(f"    --next \"Description of what comes next\"")
    print(f"")
    print(f"  This will:")
    print(f"    1. Update cycle status")
    print(f"    2. Commit all changes")
    print(f"    3. Create handoff signal")
    print(f"    4. Spawn fresh EE instance")

    print("\n" + "=" * 70)
    print("  ✅ STARTUP COMPLETE - Ready to work!")
    print("=" * 70 + "\n")

    # Return status info as JSON for programmatic use
    return {
        "is_handoff": is_handoff,
        "cycle_status": cycle_status,
        "handoff_signal": handoff_signal
    }


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Startup error: {e}", file=sys.stderr)
        sys.exit(1)
