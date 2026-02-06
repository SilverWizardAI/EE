#!/usr/bin/env python3
"""
EE Instance Status Writer - File-Based Status Reporting

EE instances (Claude Code sessions) CANNOT run MCP servers.
Instead, they write status to a JSON file that EEM polls.

This is simpler, more reliable, and actually works!
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class EEStatusWriter:
    """Write EE instance status to file for EEM to poll."""

    def __init__(self, cycle_number: int, ee_root: Optional[Path] = None):
        """Initialize status writer for this cycle."""
        self.cycle_number = cycle_number
        self.ee_root = ee_root or Path(__file__).parent.parent
        self.status_dir = self.ee_root / "status"
        self.status_dir.mkdir(exist_ok=True)

        self.status_file = self.status_dir / f"ee_cycle_{cycle_number}_status.json"

        # Initialize with starting status
        self.write_status(
            step=0,
            task="Initializing",
            cycle_status="starting",
            progress="0%",
            tokens_used=0
        )

    def write_status(
        self,
        step: int,
        task: str,
        cycle_status: str = "running",
        progress: str = "",
        tokens_used: int = 0
    ) -> bool:
        """
        Write current status to file.

        Args:
            step: Current step number
            task: Description of current task
            cycle_status: Status (starting/running/complete/error)
            progress: Optional progress indicator
            tokens_used: Current token count

        Returns:
            True if successful
        """
        try:
            status = {
                "cycle": self.cycle_number,
                "step": step,
                "task": task,
                "cycle_status": cycle_status,
                "progress": progress,
                "tokens_used": tokens_used,
                "last_updated": datetime.now().isoformat()
            }

            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)

            return True

        except Exception as e:
            print(f"⚠️ Failed to write status: {e}")
            return False

    def mark_complete(self, final_step: int, final_message: str) -> bool:
        """Mark cycle as complete."""
        return self.write_status(
            step=final_step,
            task=final_message,
            cycle_status="complete",
            progress="100%"
        )

    def mark_error(self, error_message: str) -> bool:
        """Mark cycle as errored."""
        return self.write_status(
            step=-1,
            task=f"ERROR: {error_message}",
            cycle_status="error",
            progress="N/A"
        )


# Global instance for easy access
_status_writer: Optional[EEStatusWriter] = None


def init_status_writer(cycle_number: int) -> EEStatusWriter:
    """Initialize status writer for this cycle."""
    global _status_writer
    _status_writer = EEStatusWriter(cycle_number)
    return _status_writer


def get_status_writer() -> Optional[EEStatusWriter]:
    """Get current status writer."""
    return _status_writer


def write_status(step: int, task: str, **kwargs) -> bool:
    """Convenience function to write status."""
    if _status_writer:
        return _status_writer.write_status(step, task, **kwargs)
    return False


if __name__ == "__main__":
    # Test
    writer = EEStatusWriter(cycle_number=1)

    # Test updates
    writer.write_status(1, "Starting Cycle 1", progress="10%", tokens_used=5000)
    print(f"✅ Wrote status to: {writer.status_file}")

    # Read it back
    with open(writer.status_file) as f:
        status = json.load(f)
        print(f"📊 Status: {json.dumps(status, indent=2)}")

    # Mark complete
    writer.mark_complete(13, "Step 13 complete!")
    print("✅ Marked complete")
