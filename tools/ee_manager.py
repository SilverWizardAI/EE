#!/usr/bin/env python3
"""
EE Manager - Enterprise Edition Self-Management

Manages EE's own lifecycle for autonomous overnight operation:
- Monitors token usage of current EE instance
- Triggers handoff at 85% token threshold
- Spawns fresh EE instances to continue work
- Tracks cycle progression and work status

Module Size Target: <400 lines (Current: ~350 lines)
"""

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from sw_core import get_terminal_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CycleStatus:
    """Tracks EE work cycle status."""
    cycle_number: int
    started_at: str
    token_budget: int = 200000
    token_threshold: int = 170000  # 85%
    current_task: str = ""
    tasks_completed: list = None
    next_action: str = ""
    last_updated: str = ""

    def __post_init__(self):
        if self.tasks_completed is None:
            self.tasks_completed = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


class EEManager:
    """
    Manages EE instance lifecycle for autonomous operation.

    Features:
    - Token usage monitoring
    - Cycle status tracking
    - Automatic handoff at 85% tokens
    - Fresh instance spawning
    - Work continuation across cycles

    Usage:
        manager = EEManager()

        # Check if handoff needed
        if manager.should_handoff(current_tokens=170000):
            manager.trigger_handoff(next_task="Continue Phase 1A extraction")

        # Start new cycle
        status = manager.start_new_cycle(task="Extract sw_core libraries")

        # Update progress
        manager.update_progress(
            tasks_completed=["spawn_claude.py extracted"],
            next_action="Extract settings_manager.py"
        )
    """

    def __init__(self, ee_root: Optional[Path] = None):
        """
        Initialize EE Manager.

        Args:
            ee_root: Path to EE project root (auto-detected if not provided)
        """
        # Auto-detect EE root
        if ee_root is None:
            ee_root = Path(__file__).parent.parent

        self.ee_root = Path(ee_root)
        self.status_dir = self.ee_root / "status"
        self.cycle_status_file = self.status_dir / "EE_CYCLE_STATUS.json"
        self.handoff_signal_file = self.status_dir / "HANDOFF_SIGNAL.txt"
        self.cycle_reports_file = self.status_dir / "cycle_reports.log"
        self.config_file = self.status_dir / "ee_config.json"

        # Ensure status directory exists
        self.status_dir.mkdir(exist_ok=True)

        logger.info(f"EE Manager initialized: {self.ee_root}")

    # Configuration Management

    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Config dictionary with handoff_threshold_percent and token_budget
        """
        default_config = {
            'handoff_threshold_percent': 20,  # Default 20% for testing
            'token_budget': 200000
        }

        if not self.config_file.exists():
            return default_config

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return {**default_config, **config}  # Merge with defaults
        except Exception as e:
            logger.error(f"Failed to read config: {e}")
            return default_config

    def get_threshold_tokens(self) -> int:
        """
        Get handoff threshold in tokens based on current config.

        Returns:
            Threshold in tokens
        """
        config = self.get_config()
        percent = config.get('handoff_threshold_percent', 20)
        budget = config.get('token_budget', 200000)
        threshold = int((percent / 100) * budget)
        logger.debug(f"Threshold: {percent}% = {threshold:,} tokens")
        return threshold

    # Cycle Management

    def get_current_cycle(self) -> Optional[CycleStatus]:
        """
        Get current cycle status.

        Returns:
            CycleStatus object or None if no active cycle
        """
        if not self.cycle_status_file.exists():
            logger.debug("No cycle status file found")
            return None

        try:
            with open(self.cycle_status_file, 'r') as f:
                data = json.load(f)

            status = CycleStatus(**data)
            logger.debug(f"Current cycle: {status.cycle_number}")
            return status

        except Exception as e:
            logger.error(f"Failed to read cycle status: {e}")
            return None

    def start_new_cycle(self, task: str, previous_cycle: Optional[int] = None, report: Optional[str] = None) -> CycleStatus:
        """
        Start a new work cycle.

        Args:
            task: Description of current task
            previous_cycle: Previous cycle number (auto-detected if not provided)
            report: Optional cycle report (auto-generated if not provided)

        Returns:
            New CycleStatus object
        """
        # Determine cycle number
        if previous_cycle is not None:
            cycle_num = previous_cycle + 1
        else:
            current = self.get_current_cycle()
            cycle_num = (current.cycle_number + 1) if current else 1

        # Get current threshold from config
        threshold = self.get_threshold_tokens()
        config = self.get_config()

        status = CycleStatus(
            cycle_number=cycle_num,
            started_at=datetime.now().isoformat(),
            current_task=task,
            next_action=task,
            token_budget=config.get('token_budget', 200000),
            token_threshold=threshold
        )

        self._save_cycle_status(status)

        # Create and log cycle report with threshold info
        if report is None:
            percent = config.get('handoff_threshold_percent', 20)
            report = f"Starting {task} (Handoff at {percent}% = {threshold:,} tokens)"
        self._log_cycle_report(cycle_num, report)

        logger.info(f"✅ Started Cycle {cycle_num}: {task} (threshold: {threshold:,} tokens)")

        return status

    def update_progress(
        self,
        current_task: Optional[str] = None,
        tasks_completed: Optional[list] = None,
        next_action: Optional[str] = None
    ) -> CycleStatus:
        """
        Update current cycle progress.

        Args:
            current_task: Update current task description
            tasks_completed: Add completed tasks
            next_action: Update next action

        Returns:
            Updated CycleStatus
        """
        status = self.get_current_cycle()
        if not status:
            logger.warning("No active cycle - creating new one")
            status = self.start_new_cycle(task=current_task or "Unknown task")

        # Update fields
        if current_task:
            status.current_task = current_task

        if tasks_completed:
            status.tasks_completed.extend(tasks_completed)

        if next_action:
            status.next_action = next_action

        status.last_updated = datetime.now().isoformat()

        self._save_cycle_status(status)
        logger.info(f"✅ Updated Cycle {status.cycle_number} progress")

        return status

    def _save_cycle_status(self, status: CycleStatus):
        """Save cycle status to file."""
        try:
            with open(self.cycle_status_file, 'w') as f:
                json.dump(asdict(status), f, indent=2)
            logger.debug(f"Saved cycle status: Cycle {status.cycle_number}")
        except Exception as e:
            logger.error(f"Failed to save cycle status: {e}")
            raise

    def _log_cycle_report(self, cycle_num: int, report: str):
        """
        Log a cycle report to the reports file.

        Args:
            cycle_num: Cycle number
            report: Report text
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] CYCLE {cycle_num}: {report}\n"

        try:
            with open(self.cycle_reports_file, 'a') as f:
                f.write(log_entry)
            logger.debug(f"Logged cycle {cycle_num} report")
        except Exception as e:
            logger.error(f"Failed to log cycle report: {e}")

    # Token Monitoring & Handoff

    def should_handoff(self, current_tokens: int) -> bool:
        """
        Check if handoff is needed based on token usage.

        Args:
            current_tokens: Current token count

        Returns:
            True if handoff should be triggered
        """
        # Always use latest threshold from config
        threshold = self.get_threshold_tokens()

        should_handoff = current_tokens >= threshold

        if should_handoff:
            config = self.get_config()
            percent = config.get('handoff_threshold_percent', 20)
            logger.warning(f"🔄 Handoff threshold reached: {current_tokens:,}/{threshold:,} ({percent}%)")

        return should_handoff

    def trigger_handoff(
        self,
        current_tokens: int,
        next_task: str,
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger handoff to fresh EE instance.

        Steps:
        1. Update cycle status
        2. Commit all changes
        3. Create handoff signal
        4. Spawn fresh EE instance

        Args:
            current_tokens: Current token count
            next_task: What next instance should do
            commit_message: Optional commit message (auto-generated if not provided)

        Returns:
            Dict with handoff details
        """
        status = self.get_current_cycle()
        if not status:
            logger.warning("No active cycle during handoff")
            status = self.start_new_cycle(task="Handoff recovery")

        cycle_num = status.cycle_number

        logger.info(f"🔄 Triggering handoff for Cycle {cycle_num}")

        # Step 1: Update status
        self.update_progress(
            next_action=f"HANDOFF → Cycle {cycle_num + 1}: {next_task}"
        )

        # Step 2: Commit changes
        if commit_message is None:
            commit_message = f"chore: Handoff at {current_tokens} tokens - Cycle {cycle_num} → {cycle_num + 1}"

        try:
            self._commit_all_changes(commit_message)
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            # Continue anyway - handoff is more important

        # Step 3: Create handoff signal
        handoff_info = {
            "cycle": cycle_num,
            "next_cycle": cycle_num + 1,
            "tokens": current_tokens,
            "next_task": next_task,
            "timestamp": datetime.now().isoformat()
        }

        self._create_handoff_signal(handoff_info)

        # Step 4: Spawn fresh instance
        spawn_result = self._spawn_fresh_instance(next_task)

        logger.info(f"✅ Handoff complete: Cycle {cycle_num} → {cycle_num + 1}")

        return {
            "status": "handoff_complete",
            "cycle": cycle_num,
            "next_cycle": cycle_num + 1,
            "spawn_result": spawn_result
        }

    def _commit_all_changes(self, message: str):
        """Commit all changes to git."""
        logger.info(f"Committing changes: {message}")

        # Add all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=self.ee_root,
            check=True
        )

        # Commit with co-author
        commit_msg = f"{message}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=self.ee_root,
            check=True
        )

        # Push to remote
        subprocess.run(
            ["git", "push"],
            cwd=self.ee_root,
            check=True
        )

        logger.info("✓ Changes committed and pushed")

    def _create_handoff_signal(self, info: Dict[str, Any]):
        """Create handoff signal file."""
        signal_text = f"""HANDOFF_NEEDED
Cycle: {info['cycle']} → {info['next_cycle']}
Tokens: {info['tokens']}
Next Task: {info['next_task']}
Timestamp: {info['timestamp']}
"""

        with open(self.handoff_signal_file, 'w') as f:
            f.write(signal_text)

        logger.info(f"✓ Handoff signal created: {self.handoff_signal_file}")

    def _spawn_fresh_instance(self, initial_prompt: str) -> Dict[str, Any]:
        """
        Spawn fresh EE instance to continue work using C3's TerminalManager.

        Args:
            initial_prompt: Initial prompt for new instance

        Returns:
            Dict with spawn details
        """
        logger.info("Spawning fresh EE instance using TerminalManager...")

        try:
            # Get terminal manager
            tm = get_terminal_manager()

            # Determine session ID (next cycle)
            status = self.get_current_cycle()
            next_cycle = (status.cycle_number + 1) if status else 1
            session_id = f"ee_cycle_{next_cycle}"

            # Spawn terminal on left half of screen
            terminal_info = tm.spawn_claude_terminal(
                project_path=self.ee_root,
                session_id=session_id,
                initial_prompt=initial_prompt,
                label=f"EE Cycle {next_cycle}",
                position="left"
            )

            logger.info(f"✓ Fresh EE instance spawned: PID={terminal_info['pid']}, WindowID={terminal_info['terminal_id']}")

            return {
                "status": "spawned",
                "pid": terminal_info['pid'],
                "terminal_id": terminal_info['terminal_id'],
                "session_id": session_id,
                "prompt": initial_prompt
            }

        except Exception as e:
            logger.error(f"Failed to spawn fresh instance: {e}")
            raise

    # Startup & Resume

    def check_handoff_signal(self) -> Optional[Dict[str, Any]]:
        """
        Check if there's a handoff signal from previous instance.

        Returns:
            Handoff info dict or None
        """
        if not self.handoff_signal_file.exists():
            return None

        try:
            with open(self.handoff_signal_file, 'r') as f:
                content = f.read()

            # Parse the signal file
            lines = content.strip().split('\n')
            info = {}

            for line in lines[1:]:  # Skip "HANDOFF_NEEDED"
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip().lower().replace(' ', '_')] = value.strip()

            logger.info(f"📥 Handoff signal detected: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to read handoff signal: {e}")
            return None

    def clear_handoff_signal(self):
        """Clear handoff signal after processing."""
        if self.handoff_signal_file.exists():
            self.handoff_signal_file.unlink()
            logger.info("✓ Handoff signal cleared")

    def get_startup_info(self) -> Dict[str, Any]:
        """
        Get startup information for EE instance.

        Returns:
            Dict with cycle status and handoff info
        """
        cycle_status = self.get_current_cycle()
        handoff_signal = self.check_handoff_signal()

        return {
            "cycle_status": asdict(cycle_status) if cycle_status else None,
            "handoff_signal": handoff_signal,
            "is_handoff": handoff_signal is not None
        }


def main():
    """CLI interface for EE Manager."""
    import argparse

    parser = argparse.ArgumentParser(description="EE Manager - Self-management for EE")
    parser.add_argument(
        "command",
        choices=["status", "start", "update", "handoff", "startup"],
        help="Command to execute"
    )
    parser.add_argument("--task", help="Current task description")
    parser.add_argument("--tokens", type=int, help="Current token count")
    parser.add_argument("--next", help="Next action/task")
    parser.add_argument("--completed", nargs="+", help="Completed tasks")

    args = parser.parse_args()

    manager = EEManager()

    if args.command == "status":
        status = manager.get_current_cycle()
        if status:
            print(json.dumps(asdict(status), indent=2))
        else:
            print("No active cycle")

    elif args.command == "start":
        if not args.task:
            print("Error: --task required for start command")
            return 1
        status = manager.start_new_cycle(args.task)
        print(json.dumps(asdict(status), indent=2))

    elif args.command == "update":
        status = manager.update_progress(
            current_task=args.task,
            tasks_completed=args.completed,
            next_action=args.next
        )
        print(json.dumps(asdict(status), indent=2))

    elif args.command == "handoff":
        if not args.tokens or not args.next:
            print("Error: --tokens and --next required for handoff")
            return 1
        result = manager.trigger_handoff(args.tokens, args.next)
        print(json.dumps(result, indent=2))

    elif args.command == "startup":
        info = manager.get_startup_info()
        print(json.dumps(info, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
