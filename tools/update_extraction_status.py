#!/usr/bin/env python3
"""
Update Library Extraction Status

Helper for EE to update status after completing tasks.
"""

from pathlib import Path
from datetime import datetime
import sys


def mark_task_complete(task_name: str, phase: str = "1A"):
    """
    Mark a task as complete in status file.

    Args:
        task_name: Task description (e.g., "Extracted base_application.py")
        phase: Phase identifier (e.g., "1A", "1B")
    """
    status_file = Path(__file__).parent.parent / "status" / "LIBRARY_EXTRACTION_STATUS.md"

    if not status_file.exists():
        print(f"✗ Status file not found: {status_file}")
        return

    content = status_file.read_text()

    # Find and replace task
    task_line = f"- [ ] {task_name}"
    completed_line = f"- [x] {task_name}"

    if task_line in content:
        content = content.replace(task_line, completed_line)
        status_file.write_text(content)
        print(f"✓ Marked complete: {task_name}")
    else:
        print(f"⚠️ Task not found: {task_name}")
        print(f"   Searched for: {task_line}")


def update_cycle_info(instance_id: str, tokens_used: int):
    """
    Update current cycle information.

    Args:
        instance_id: Current EE instance ID
        tokens_used: Current token usage
    """
    status_file = Path(__file__).parent.parent / "status" / "LIBRARY_EXTRACTION_STATUS.md"

    if not status_file.exists():
        print(f"✗ Status file not found: {status_file}")
        return

    content = status_file.read_text()

    # Update instance ID and tokens
    # Find current instance ID line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith("**Instance ID:**"):
            lines[i] = f"**Instance ID:** {instance_id}"
        elif line.startswith("**Tokens Used:**"):
            lines[i] = f"**Tokens Used:** {tokens_used:,} / 200,000"

    content = '\n'.join(lines)
    status_file.write_text(content)
    print(f"✓ Updated cycle info: {instance_id}, {tokens_used:,} tokens")


def add_cycle_entry(cycle_num: int, status: str, tasks_completed: int, handoff_reason: str = "N/A"):
    """
    Add cycle history entry.

    Args:
        cycle_num: Cycle number
        status: Status (In Progress, Completed, Failed)
        tasks_completed: Number of tasks completed in this cycle
        handoff_reason: Reason for handoff
    """
    status_file = Path(__file__).parent.parent / "status" / "LIBRARY_EXTRACTION_STATUS.md"

    if not status_file.exists():
        print(f"✗ Status file not found: {status_file}")
        return

    content = status_file.read_text()

    # Create cycle entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cycle_entry = f"""
### Cycle {cycle_num}
- **Started:** {timestamp}
- **Status:** {status}
- **Tasks Completed:** {tasks_completed}
- **Handoff Reason:** {handoff_reason}
"""

    # Find Cycle History section and append
    if "## Cycle History" in content:
        parts = content.split("## Cycle History")
        if len(parts) == 2:
            # Insert after existing cycles
            parts[1] = parts[1] + "\n" + cycle_entry
            content = "## Cycle History".join(parts)
            status_file.write_text(content)
            print(f"✓ Added cycle {cycle_num} entry")
        else:
            print("⚠️ Could not locate Cycle History section")
    else:
        print("⚠️ Cycle History section not found")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python update_extraction_status.py <task_name>")
        print("  python update_extraction_status.py --cycle-info <instance_id> <tokens>")
        print("  python update_extraction_status.py --add-cycle <num> <status> <tasks> [reason]")
        print()
        print("Examples:")
        print("  python update_extraction_status.py 'Extracted spawn_claude.py'")
        print("  python update_extraction_status.py --cycle-info ee_12345 45000")
        print("  python update_extraction_status.py --add-cycle 2 Completed 3 'Token limit'")
        sys.exit(1)

    if sys.argv[1] == "--cycle-info":
        if len(sys.argv) < 4:
            print("✗ Error: --cycle-info requires <instance_id> and <tokens>")
            sys.exit(1)
        instance_id = sys.argv[2]
        tokens_used = int(sys.argv[3])
        update_cycle_info(instance_id, tokens_used)

    elif sys.argv[1] == "--add-cycle":
        if len(sys.argv) < 5:
            print("✗ Error: --add-cycle requires <num> <status> <tasks> [reason]")
            sys.exit(1)
        cycle_num = int(sys.argv[2])
        status = sys.argv[3]
        tasks_completed = int(sys.argv[4])
        handoff_reason = sys.argv[5] if len(sys.argv) > 5 else "N/A"
        add_cycle_entry(cycle_num, status, tasks_completed, handoff_reason)

    else:
        # Mark task complete
        task_name = " ".join(sys.argv[1:])
        mark_task_complete(task_name)
