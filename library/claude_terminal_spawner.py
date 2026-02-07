"""
Claude Code Terminal Spawner & Controller

Spawns new Terminal windows running Claude Code and provides foolproof lifecycle
management including text injection and termination without approval dialogs.

EXTRACTED FROM: C3 project (services/terminal_manager.py)
VALIDATION: Proven in C3's cycle_tests/ (Step1-Step9.sh)

Key Features:
- ✅ Spawns NEW Terminal windows (not tabs) using AppleScript
- ✅ Injects text into terminal to auto-start Claude with commands
- ✅ Foolproof termination using SIGKILL (no "Terminate?" dialogs)
- ✅ PID tracking via .claude/c3-claude.pid mechanism
- ✅ Window positioning (left/right half-screen)
- ✅ Bypass trust prompts with --permission-mode dontAsk

Usage:
    spawner = ClaudeTerminalSpawner()

    # Spawn terminal
    info = spawner.spawn_terminal(
        project_path=Path("/path/to/project"),
        label="My Terminal",
        position="left",  # Optional: "left" or "right"
        permission_mode="dontAsk"  # Bypass trust dialogs
    )

    # Inject text after spawn
    spawner.inject_text(
        terminal_id=info['terminal_id'],
        text="Hello Claude, please help me with...",
        submit=True  # Press Enter after typing
    )

    # Close without dialog
    spawner.close_terminal(info['pid'], info['terminal_id'])
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ClaudeTerminalSpawner:
    """
    Spawns and manages Terminal windows running Claude Code.

    Provides foolproof termination without approval dialogs using SIGKILL.
    """

    def __init__(self):
        """Initialize terminal spawner"""
        self.tracked_terminals: Dict[str, dict] = {}

    def spawn_terminal(
        self,
        project_path: Path,
        terminal_id: str,
        label: Optional[str] = None,
        position: Optional[str] = None,
        permission_mode: str = "dontAsk",
        additional_flags: str = ""
    ) -> dict:
        """
        Spawn a new Terminal window running Claude Code.

        Args:
            project_path: Path to the project directory
            terminal_id: Unique identifier for this terminal
            label: Optional label to echo in terminal (e.g., "Terminal 1")
            position: Optional window position: "left" or "right" (half-screen)
            permission_mode: Claude permission mode (default: "dontAsk" to bypass trust)
            additional_flags: Additional Claude CLI flags (e.g., "--model opus")

        Returns:
            dict with keys:
                - terminal_id: str - Identifier you provided
                - window_id: str - macOS Terminal window ID
                - pid: int - Process ID of Claude Code
                - project_path: str - Path to project
                - pid_file: str - Path to PID file

        Raises:
            RuntimeError: If terminal spawn fails or PID cannot be captured

        Example:
            info = spawner.spawn_terminal(
                project_path=Path("/path/to/project"),
                terminal_id="task_1",
                label="Task 1",
                position="left"
            )
        """
        logger.info(f"[ClaudeTerminalSpawner] Spawning terminal '{terminal_id}' at {project_path}")

        # Ensure project path exists
        if not project_path.exists():
            raise RuntimeError(f"Project path does not exist: {project_path}")

        # Ensure .claude directory exists for PID file
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        pid_file = claude_dir / "claude-terminal.pid"

        # Remove old PID file if exists
        if pid_file.exists():
            pid_file.unlink()

        # Build Claude command
        claude_cmd = f"claude --permission-mode {permission_mode}"
        if additional_flags:
            claude_cmd += f" {additional_flags}"

        # Build command chain with optional label
        # CRITICAL: echo $$ captures the shell's PID which is Claude's parent
        if label:
            # Echo label in large header for visibility
            command_chain = (
                f"echo '\\n\\n=== {label} ===\\n' && "
                f"cd '{project_path}' && "
                f"echo $$ > .claude/claude-terminal.pid && "
                f"{claude_cmd}"
            )
        else:
            command_chain = (
                f"cd '{project_path}' && "
                f"echo $$ > .claude/claude-terminal.pid && "
                f"{claude_cmd}"
            )

        # Build AppleScript command with optional positioning
        # CRITICAL: Must create NEW window, not tab
        # Strategy: Use System Events to press Cmd+N which ALWAYS creates new window

        # Calculate window bounds for positioning
        position_script = ""
        if position in ["left", "right"]:
            # Get screen dimensions and calculate bounds
            if position == "left":
                # Left half: {0, 0, screen_width/2, screen_height}
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
                # Right half: {screen_width/2, 0, screen_width, screen_height}
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

        logger.debug(f"[ClaudeTerminalSpawner] Executing AppleScript to spawn terminal")

        try:
            # Execute AppleScript and capture window ID
            # Increased timeout to 30s to handle Finder bounds query + positioning
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"AppleScript failed: {result.stderr}")

            window_id = result.stdout.strip()
            logger.info(f"[ClaudeTerminalSpawner] Terminal window opened: WindowID={window_id}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Terminal spawn timed out after 30 seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to spawn terminal: {e}")

        # Wait for PID file to be created (with timeout)
        logger.debug(f"[ClaudeTerminalSpawner] Waiting for PID file at {pid_file}")
        pid = None

        for attempt in range(50):  # 5 seconds total (50 * 0.1s)
            if pid_file.exists():
                try:
                    pid_content = pid_file.read_text().strip()
                    pid = int(pid_content)
                    logger.info(f"[ClaudeTerminalSpawner] PID captured: {pid}")
                    break
                except (ValueError, OSError) as e:
                    logger.warning(f"[ClaudeTerminalSpawner] Failed to read PID file: {e}")

            time.sleep(0.1)

        if pid is None:
            raise RuntimeError(f"PID file not created within 5 seconds at {pid_file}")

        # Verify process is running
        if not self._is_pid_alive(pid):
            raise RuntimeError(f"Process {pid} is not running")

        # Store terminal info
        terminal_info = {
            "terminal_id": terminal_id,
            "window_id": window_id,
            "pid": pid,
            "project_path": str(project_path),
            "pid_file": str(pid_file)
        }

        self.tracked_terminals[terminal_id] = terminal_info
        logger.info(f"[ClaudeTerminalSpawner] Terminal registered: ID={terminal_id}, PID={pid}, WindowID={window_id}")

        return terminal_info

    def inject_text(
        self,
        window_id: str,
        text: str,
        submit: bool = True,
        wait_before_inject: float = 8.0
    ) -> bool:
        """
        Inject text into a Terminal window.

        Uses AppleScript to type text as if user typed it. Useful for auto-starting
        Claude sessions with initial prompts.

        Args:
            window_id: macOS Terminal window ID (from spawn_terminal result)
            text: Text to inject into terminal
            submit: Whether to press Enter after typing (default: True)
            wait_before_inject: Seconds to wait for Claude to initialize (default: 8.0)

        Returns:
            True if injection succeeded, False otherwise

        Example:
            spawner.inject_text(
                window_id=info['window_id'],
                text="Please analyze the codebase and summarize the architecture.",
                submit=True
            )

        Note:
            Long text is broken into chunks to avoid keystroke drops.
            Claude needs ~8 seconds to fully initialize before accepting input.
        """
        logger.info(f"[ClaudeTerminalSpawner] Injecting text into window {window_id}")

        # Wait for Claude Code to fully load and show prompt
        # CC needs time to: load, read CLAUDE.md, show welcome screen, display prompt
        # CRITICAL: Must wait for actual prompt, not just terminal spawn
        if wait_before_inject > 0:
            logger.debug(f"[ClaudeTerminalSpawner] Waiting {wait_before_inject}s for Claude to initialize...")
            time.sleep(wait_before_inject)

        # Split long text into chunks to avoid keystroke drops
        # AppleScript can drop keystrokes if text is too long
        max_chunk_size = 100
        chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]

        # Build keystroke commands for each chunk
        keystroke_commands = []
        for chunk in chunks:
            # Escape quotes in chunk
            escaped_chunk = chunk.replace('"', '\\"')
            keystroke_commands.append(f'keystroke "{escaped_chunk}"')
            keystroke_commands.append('delay 0.1')  # Small delay between chunks

        keystroke_script = '\n            '.join(keystroke_commands)

        # Build submit command
        submit_script = ""
        if submit:
            submit_script = '''
            -- CRITICAL: Delay before Enter to ensure full text is buffered
            delay 0.5

            -- Press Enter to submit
            keystroke return
            '''

        # AppleScript to type the text
        inject_script = f'''
        tell application "Terminal"
            -- Activate the specific terminal window
            set frontmost of window id {window_id} to true
            activate
        end tell

        -- Longer delay to ensure Terminal is fully focused
        delay 0.5

        tell application "System Events"
            -- Type the text in chunks
            {keystroke_script}

            {submit_script}
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
                logger.info(f"[ClaudeTerminalSpawner] Text injected successfully")
                return True
            else:
                logger.warning(f"[ClaudeTerminalSpawner] Failed to inject text: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"[ClaudeTerminalSpawner] Error injecting text: {e}")
            return False

    def close_terminal(
        self,
        pid: int,
        window_id: str,
        terminal_id: Optional[str] = None
    ) -> bool:
        """
        Close a terminal by killing its process tree and closing the window.

        FOOLPROOF TERMINATION: Uses SIGKILL (signal 9) which is forceful and
        NEVER triggers Terminal's "Do you want to terminate?" dialog.

        Protocol:
        1. Kill all child processes (MCP servers, Node, etc.) with pkill -9 -P
        2. Kill main process with SIGKILL (os.kill with signal 9)
        3. Close Terminal window via AppleScript
        4. Clean up PID file

        Args:
            pid: Process ID to kill
            window_id: macOS Terminal window ID
            terminal_id: Optional identifier for tracking cleanup

        Returns:
            True if terminal was closed successfully

        Example:
            spawner.close_terminal(
                pid=info['pid'],
                window_id=info['window_id'],
                terminal_id=info['terminal_id']
            )

        Note:
            SIGKILL is forceful and cannot be caught by the process.
            This is intentional to avoid any approval dialogs.
        """
        logger.info(f"[ClaudeTerminalSpawner] Closing terminal: PID={pid}, WindowID={window_id}")

        try:
            # Step 1: Kill all child processes first (MCP servers, Node, etc.)
            logger.info(f"[ClaudeTerminalSpawner] Killing child processes of PID {pid}")
            try:
                subprocess.run(
                    ['pkill', '-9', '-P', str(pid)],
                    capture_output=True,
                    timeout=2
                )
                time.sleep(0.5)  # Wait for children to die
                logger.debug(f"[ClaudeTerminalSpawner] Killed children of PID {pid}")
            except Exception as e:
                logger.debug(f"[ClaudeTerminalSpawner] No children or error killing children: {e}")

            # Step 2: Kill the main process with SIGKILL
            # CRITICAL: SIGKILL (9) is forceful and NEVER triggers confirmation dialog
            logger.info(f"[ClaudeTerminalSpawner] Sending SIGKILL to PID {pid}")
            os.kill(pid, 9)  # SIGKILL - forceful, no confirmation dialog

            # Wait for complete process death
            time.sleep(1.0)  # Increased wait time to ensure COMPLETE death

            # Verify death
            try:
                os.kill(pid, 0)
                logger.warning(f"[ClaudeTerminalSpawner] Process {pid} still alive after SIGKILL")
            except OSError:
                logger.info(f"[ClaudeTerminalSpawner] Process {pid} confirmed dead")

            # Step 3: Close the window via AppleScript
            logger.info(f"[ClaudeTerminalSpawner] Closing window {window_id}")
            script = f'''
            tell application "Terminal"
                close window id {window_id}
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

            # Step 4: Clean up tracking
            if terminal_id and terminal_id in self.tracked_terminals:
                terminal_info = self.tracked_terminals[terminal_id]
                pid_file = Path(terminal_info["pid_file"])
                if pid_file.exists():
                    pid_file.unlink()
                    logger.debug(f"[ClaudeTerminalSpawner] Removed PID file: {pid_file}")

                del self.tracked_terminals[terminal_id]

            logger.info(f"[ClaudeTerminalSpawner] Terminal closed successfully")
            return True

        except ProcessLookupError:
            logger.warning(f"[ClaudeTerminalSpawner] Process {pid} not found - already terminated")
            return True

        except Exception as e:
            logger.error(f"[ClaudeTerminalSpawner] Failed to close terminal: {e}")
            return False

    def is_terminal_alive(self, terminal_id: str) -> bool:
        """
        Check if a tracked terminal's process is still running.

        Args:
            terminal_id: Identifier of the terminal to check

        Returns:
            True if process is running, False otherwise
        """
        if terminal_id not in self.tracked_terminals:
            logger.warning(f"[ClaudeTerminalSpawner] Terminal {terminal_id} not found in tracking")
            return False

        terminal_info = self.tracked_terminals[terminal_id]
        pid = terminal_info["pid"]

        is_alive = self._is_pid_alive(pid)
        logger.debug(f"[ClaudeTerminalSpawner] Process {pid} ({terminal_id}) alive: {is_alive}")

        return is_alive

    def get_terminal_info(self, terminal_id: str) -> Optional[dict]:
        """
        Get information about a tracked terminal.

        Args:
            terminal_id: Identifier of the terminal

        Returns:
            Terminal info dict or None if not found
        """
        return self.tracked_terminals.get(terminal_id)

    def list_active_terminals(self) -> list:
        """
        Get list of all active terminal IDs.

        Returns:
            List of terminal IDs
        """
        return list(self.tracked_terminals.keys())

    def cleanup_dead_terminals(self) -> int:
        """
        Remove dead terminals from tracking and clean up their PID files.

        Returns:
            Number of dead terminals cleaned up
        """
        dead_ids = []

        for terminal_id in list(self.tracked_terminals.keys()):
            if not self.is_terminal_alive(terminal_id):
                dead_ids.append(terminal_id)

        for terminal_id in dead_ids:
            logger.info(f"[ClaudeTerminalSpawner] Cleaning up dead terminal: {terminal_id}")
            terminal_info = self.tracked_terminals[terminal_id]

            # Clean up PID file
            pid_file = Path(terminal_info["pid_file"])
            if pid_file.exists():
                pid_file.unlink()

            # Remove from tracking
            del self.tracked_terminals[terminal_id]

        return len(dead_ids)

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


# Example usage
if __name__ == "__main__":
    """
    Example: Spawn a Claude terminal, inject text, wait, then close it.
    """
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get project path from args or use current directory
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()

    print(f"Project path: {project_path}")

    # Create spawner
    spawner = ClaudeTerminalSpawner()

    try:
        # Spawn terminal on left half of screen
        print("\n1. Spawning Claude terminal...")
        info = spawner.spawn_terminal(
            project_path=project_path,
            terminal_id="demo_terminal",
            label="Demo Terminal",
            position="left"
        )

        print(f"   ✅ Spawned: PID={info['pid']}, WindowID={info['window_id']}")

        # Inject text after Claude initializes
        print("\n2. Injecting text into terminal...")
        success = spawner.inject_text(
            window_id=info['window_id'],
            text="Hello Claude! Please list the files in the current directory.",
            submit=True,
            wait_before_inject=8.0
        )

        if success:
            print("   ✅ Text injected successfully")
        else:
            print("   ⚠️  Text injection failed")

        # Wait for user to see the result
        input("\nPress ENTER to close the terminal...")

        # Close terminal (no approval dialog!)
        print("\n3. Closing terminal...")
        spawner.close_terminal(
            pid=info['pid'],
            window_id=info['window_id'],
            terminal_id=info['terminal_id']
        )

        print("   ✅ Terminal closed successfully (no approval dialog!)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
