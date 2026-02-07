"""
Terminal Manager - From C3

Manages terminal windows running Claude Code sessions.
Spawns new Terminal windows, tracks PIDs, and provides lifecycle management.

Based on C3's proven implementation.
Module Size Target: <400 lines (Current: ~320 lines)
"""

import os
import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class TerminalManager:
    """
    Manages Terminal windows running Claude Code sessions.

    Based on C3's proven implementation for spawning, tracking, and closing
    Claude Code instances.
    """

    def __init__(self):
        """Initialize terminal manager with empty tracking."""
        self.active_terminals: Dict[str, dict] = {}
        logger.info("TerminalManager initialized")

    def spawn_claude_terminal(
        self,
        project_path: Path,
        session_id: str,
        label: Optional[str] = None,
        position: Optional[str] = None
    ) -> dict:
        """
        Spawn a new Terminal window running Claude Code.

        Args:
            project_path: Path to the project directory
            session_id: Identifier for this terminal (e.g., "cycle_1")
            label: Optional label to echo in terminal
            position: Optional window position: "left" or "right" (half-screen)

        Returns:
            dict with keys: terminal_id, pid, session_id, project_path

        Raises:
            RuntimeError: If terminal spawn fails or PID cannot be captured
        """
        logger.info(f"[TerminalManager] Spawning terminal for {session_id} at {project_path}")

        # Ensure project path exists
        if not project_path.exists():
            raise RuntimeError(f"Project path does not exist: {project_path}")

        # Ensure .claude directory exists for PID file
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        pid_file = claude_dir / "ee-claude.pid"

        # Remove old PID file if exists
        if pid_file.exists():
            pid_file.unlink()

        # Build command chain with optional label
        # CRITICAL: Use --permission-mode dontAsk to bypass trust prompt (proven in C3)
        # Startup instructions provided via SessionStart hooks in .claude/settings.json
        if label:
            # Echo label for visibility
            command_chain = f"echo '\\n\\n=== {label} ===\\n' && cd '{project_path}' && echo $$ > .claude/ee-claude.pid && claude --permission-mode dontAsk"
        else:
            command_chain = f"cd '{project_path}' && echo $$ > .claude/ee-claude.pid && claude --permission-mode dontAsk"

        # Build AppleScript command with optional positioning
        position_script = ""
        if position in ["left", "right"]:
            if position == "left":
                position_script = '''
            -- Get screen dimensions
            tell application "Finder"
                set screenBounds to bounds of window of desktop
                set screenWidth to item 3 of screenBounds
                set screenHeight to item 4 of screenBounds
            end tell

            -- Position window on left half
            set bounds of newWin to {0, 0, screenWidth / 2, screenHeight}
            '''
            else:  # right
                position_script = '''
            -- Get screen dimensions
            tell application "Finder"
                set screenBounds to bounds of window of desktop
                set screenWidth to item 3 of screenBounds
                set screenHeight to item 4 of screenBounds
            end tell

            -- Position window on right half
            set bounds of newWin to {screenWidth / 2, 0, screenWidth, screenHeight}
            '''

        script = f'''
        tell application "Terminal"
            activate
            delay 0.2

            -- Press Cmd+N to create NEW window (not tab)
            tell application "System Events"
                keystroke "n" using command down
            end tell

            delay 0.3

            -- Front window is now the new empty window
            set newWin to front window

            -- Execute command in the new window
            do script "{command_chain}" in newWin

            {position_script}

            -- Return the window ID
            return id of newWin
        end tell
        '''

        logger.debug(f"[TerminalManager] Executing AppleScript to spawn terminal")

        try:
            # Execute AppleScript and capture window ID
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"AppleScript failed: {result.stderr}")

            terminal_id = result.stdout.strip()
            logger.info(f"[TerminalManager] Terminal window opened: ID={terminal_id}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Terminal spawn timed out after 30 seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to spawn terminal: {e}")

        # Wait for PID file to be created (with timeout)
        logger.debug(f"[TerminalManager] Waiting for PID file at {pid_file}")
        pid = None

        for attempt in range(50):  # 5 seconds total (50 * 0.1s)
            if pid_file.exists():
                try:
                    pid_content = pid_file.read_text().strip()
                    pid = int(pid_content)
                    logger.info(f"[TerminalManager] PID captured: {pid}")
                    break
                except (ValueError, OSError) as e:
                    logger.warning(f"[TerminalManager] Failed to read PID file: {e}")

            time.sleep(0.1)

        if pid is None:
            raise RuntimeError(f"PID file not created within 5 seconds at {pid_file}")

        # Verify process is running
        if not self._is_pid_alive(pid):
            raise RuntimeError(f"Process {pid} is not running")

        # Store terminal info
        terminal_info = {
            "terminal_id": terminal_id,
            "pid": pid,
            "session_id": session_id,
            "project_path": str(project_path),
            "pid_file": str(pid_file)
        }

        self.active_terminals[session_id] = terminal_info
        logger.info(f"[TerminalManager] Terminal registered for {session_id}: PID={pid}, WindowID={terminal_id}")

        return terminal_info

    def inject_initialization_command(self, terminal_id: str, session_id: str, command: str):
        """
        Inject forced initialization command into Claude Code terminal.

        Uses AppleScript to auto-type the initialization command as a pseudo-user message.
        Based on C3's proven implementation.

        Args:
            terminal_id: Terminal window ID to inject into
            session_id: Session identifier for logging
            command: Command string to inject (e.g., "Run python3 tools/ee_startup.py")
        """
        logger.info(f"[TerminalManager] Injecting initialization command for {session_id}")

        # Wait for Claude Code to fully load and show prompt
        # CC needs time to: load, read CLAUDE.md, show welcome screen, display prompt
        # CRITICAL: Must wait for actual prompt, not just terminal spawn
        time.sleep(8.0)  # 8 seconds to ensure CC is fully ready

        # CRITICAL: Use clipboard method for multi-line commands
        # AppleScript keystroke cannot handle newlines in string literals
        try:
            # Step 1: Copy command to clipboard using pbcopy
            subprocess.run(
                ['pbcopy'],
                input=command.encode('utf-8'),
                check=True,
                timeout=5
            )
            logger.debug(f"[TerminalManager] Command copied to clipboard ({len(command)} chars)")

        except Exception as e:
            logger.error(f"[TerminalManager] Failed to copy to clipboard: {e}")
            return

        # Step 2: AppleScript to paste and submit
        inject_script = f'''
        tell application "Terminal"
            -- Activate the specific terminal window
            set frontmost of window id {terminal_id} to true
            activate
        end tell

        -- Longer delay to ensure Terminal is fully focused
        delay 0.5

        tell application "System Events"
            -- Paste the command (Cmd+V)
            keystroke "v" using command down

            -- CRITICAL: Longer delay before Enter to ensure full text is pasted
            -- Increased from 0.5 to 1.5 based on C3 findings
            delay 1.5

            -- Press Enter to submit
            keystroke return
        end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', inject_script],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"[TerminalManager] Initialization command injected successfully")
            else:
                logger.warning(f"[TerminalManager] Failed to inject command: {result.stderr}")

        except Exception as e:
            logger.error(f"[TerminalManager] Error injecting command: {e}")
            # Don't raise - terminal is still usable, just without auto-init

    def is_terminal_alive(self, session_id: str) -> bool:
        """
        Check if a terminal's Claude process is still running.

        Args:
            session_id: Identifier of the terminal to check

        Returns:
            True if process is running, False otherwise
        """
        if session_id not in self.active_terminals:
            logger.warning(f"[TerminalManager] Session {session_id} not found in active terminals")
            return False

        terminal_info = self.active_terminals[session_id]
        pid = terminal_info["pid"]

        is_alive = self._is_pid_alive(pid)
        logger.debug(f"[TerminalManager] Process {pid} ({session_id}) alive: {is_alive}")

        return is_alive

    def close_terminal(self, session_id: str) -> bool:
        """
        Close a terminal by killing its process tree and closing the window.

        Args:
            session_id: Identifier of the terminal to close

        Returns:
            True if terminal was closed, False if not found or failed
        """
        if session_id not in self.active_terminals:
            logger.warning(f"[TerminalManager] Session {session_id} not found, cannot close")
            return False

        terminal_info = self.active_terminals[session_id]
        pid = terminal_info["pid"]
        terminal_id = terminal_info["terminal_id"]

        logger.info(f"[TerminalManager] Closing terminal for {session_id}: PID={pid}, WindowID={terminal_id}")

        try:
            # Step 1: Kill all child processes first (MCP servers, Node, etc.)
            logger.info(f"[TerminalManager] Killing child processes of PID {pid}")
            try:
                subprocess.run(
                    ['pkill', '-9', '-P', str(pid)],
                    capture_output=True,
                    timeout=2
                )
                time.sleep(0.5)  # Wait for children to die
                logger.debug(f"[TerminalManager] Killed children of PID {pid}")
            except Exception as e:
                logger.debug(f"[TerminalManager] No children or error killing children: {e}")

            # Step 2: Kill the main process
            logger.info(f"[TerminalManager] Sending SIGKILL to PID {pid}")
            os.kill(pid, 9)  # SIGKILL - forceful, no confirmation dialog

            # Wait for complete process death
            time.sleep(1.0)

            # Verify death
            try:
                os.kill(pid, 0)
                logger.warning(f"[TerminalManager] Process {pid} still alive after SIGKILL")
            except OSError:
                logger.info(f"[TerminalManager] Process {pid} confirmed dead")

            # Step 3: Close the window via AppleScript
            logger.info(f"[TerminalManager] Closing window {terminal_id}")
            script = f'''
            tell application "Terminal"
                close window id {terminal_id}
                return "closed"
            end tell
            '''

            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Wait for window to close
            time.sleep(1.0)

            # Clean up PID file
            pid_file = Path(terminal_info["pid_file"])
            if pid_file.exists():
                pid_file.unlink()
                logger.debug(f"[TerminalManager] Removed PID file: {pid_file}")

            # Remove from tracking
            del self.active_terminals[session_id]

            logger.info(f"[TerminalManager] Terminal closed successfully")
            return True

        except ProcessLookupError:
            logger.warning(f"[TerminalManager] Process {pid} not found - already terminated")
            # Clean up anyway
            pid_file = Path(terminal_info["pid_file"])
            if pid_file.exists():
                pid_file.unlink()
            del self.active_terminals[session_id]
            return True

        except Exception as e:
            logger.error(f"[TerminalManager] Failed to close terminal: {e}")
            # Still cleanup
            pid_file = Path(terminal_info["pid_file"])
            if pid_file.exists():
                pid_file.unlink()
            if session_id in self.active_terminals:
                del self.active_terminals[session_id]
            return False

    def get_terminal_info(self, session_id: str) -> Optional[dict]:
        """
        Get information about a tracked terminal.

        Args:
            session_id: Identifier of the terminal

        Returns:
            Terminal info dict or None if not found
        """
        return self.active_terminals.get(session_id)

    def list_active_terminals(self) -> list:
        """
        Get list of all active terminal session IDs.

        Returns:
            List of session IDs
        """
        return list(self.active_terminals.keys())

    def cleanup_dead_terminals(self) -> int:
        """
        Remove dead terminals from tracking.

        Returns:
            Number of dead terminals cleaned up
        """
        dead_sessions = []

        for session_id in list(self.active_terminals.keys()):
            if not self.is_terminal_alive(session_id):
                dead_sessions.append(session_id)

        for session_id in dead_sessions:
            logger.info(f"[TerminalManager] Cleaning up dead terminal: {session_id}")
            terminal_info = self.active_terminals[session_id]

            # Clean up PID file
            pid_file = Path(terminal_info["pid_file"])
            if pid_file.exists():
                pid_file.unlink()

            # Remove from tracking
            del self.active_terminals[session_id]

        return len(dead_sessions)

    def _is_pid_alive(self, pid: int) -> bool:
        """
        Check if a process is running.

        Args:
            pid: Process ID to check

        Returns:
            True if running, False otherwise
        """
        try:
            # Send signal 0 to test if process exists (doesn't actually send a signal)
            os.kill(pid, 0)
            return True
        except OSError:
            return False


# Singleton instance
_terminal_manager = None


def get_terminal_manager() -> TerminalManager:
    """Get singleton instance of TerminalManager."""
    global _terminal_manager
    if _terminal_manager is None:
        _terminal_manager = TerminalManager()
    return _terminal_manager
