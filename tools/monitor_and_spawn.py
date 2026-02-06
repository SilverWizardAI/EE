#!/usr/bin/env python3
"""
EE Instance Monitor & Auto-Spawn

Simple monitoring script that:
1. Watches for handoff signals from EE instance
2. Spawns fresh EE instance when needed
3. Runs overnight while user sleeps

Usage:
    python tools/monitor_and_spawn.py
"""

import time
import subprocess
from pathlib import Path
from datetime import datetime


EE_FOLDER = Path("/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE")
HANDOFF_SIGNAL = EE_FOLDER / "status" / "HANDOFF_SIGNAL.txt"
STATUS_FILE = EE_FOLDER / "status" / "LIBRARY_EXTRACTION_STATUS.md"
POLL_INTERVAL = 60  # Check every 60 seconds


def log(message: str):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def check_for_handoff() -> bool:
    """Check if EE instance needs handoff."""
    if HANDOFF_SIGNAL.exists():
        log("🔄 HANDOFF SIGNAL DETECTED!")
        content = HANDOFF_SIGNAL.read_text()
        log(f"Signal content:\n{content}")
        return True
    return False


def get_next_task() -> str:
    """Read next task from status file."""
    if not STATUS_FILE.exists():
        return "Start library extraction from plans/LIBRARY_FACTORY_PLAN.md"

    content = STATUS_FILE.read_text()

    # Find Next Steps section
    if "### Next Steps:" in content:
        next_section = content.split("### Next Steps:")[1]
        # Find first uncompleted task
        for line in next_section.split("\n"):
            if line.strip().startswith("- [ ]"):
                task = line.strip()[6:].strip()
                return f"Continue library extraction: {task}"

    return "Continue library extraction from status file"


def spawn_fresh_ee():
    """Spawn fresh EE instance."""
    log("=" * 60)
    log("SPAWNING FRESH EE INSTANCE")
    log("=" * 60)

    # Get next task
    next_task = get_next_task()
    log(f"Next task: {next_task}")

    # Build command
    cmd = [
        "claude",
        "code",
        "--cwd", str(EE_FOLDER),
        "--prompt", next_task
    ]

    log(f"Command: {' '.join(cmd)}")

    # Spawn in background
    log("Spawning...")
    try:
        # Remove handoff signal
        if HANDOFF_SIGNAL.exists():
            HANDOFF_SIGNAL.unlink()
            log("✓ Removed handoff signal")

        # Spawn new instance
        subprocess.Popen(
            cmd,
            cwd=EE_FOLDER,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        log("✓ Fresh EE instance spawned!")
        log("=" * 60)

    except Exception as e:
        log(f"✗ Error spawning EE: {e}")


def main():
    """Main monitoring loop."""
    log("=" * 60)
    log("EE INSTANCE MONITOR STARTED")
    log("=" * 60)
    log(f"Monitoring: {HANDOFF_SIGNAL}")
    log(f"Poll interval: {POLL_INTERVAL}s")
    log("Press Ctrl+C to stop")
    log("=" * 60)

    try:
        cycle = 0
        while True:
            cycle += 1

            # Check for handoff
            if check_for_handoff():
                spawn_fresh_ee()
                # Reset cycle counter after spawn
                cycle = 0
            else:
                if cycle % 10 == 0:  # Log every 10 minutes
                    log(f"Monitoring... (checked {cycle} times)")

            # Wait
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log("\n" + "=" * 60)
        log("MONITOR STOPPED")
        log("=" * 60)


if __name__ == "__main__":
    main()
