#!/bin/bash
# Launch EE with split-screen monitoring
#
# Left pane: Claude Code EE instance
# Right pane: EE Monitor GUI

# Get EE root directory
EE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🏛️  Launching EE Split-Screen Setup..."
echo "Left pane: Claude Code EE"
echo "Right pane: EE Monitor GUI"
echo ""

# Launch monitor GUI in background
cd "$EE_ROOT"
python3 tools/ee_monitor_gui.py &
MONITOR_PID=$!

echo "✅ Monitor GUI launched (PID: $MONITOR_PID)"
echo ""
echo "Now launching Claude Code EE..."
echo "Position your terminal on the LEFT half of screen"
echo ""

# Give GUI time to launch
sleep 2

# Launch Claude Code in this terminal
claude code --cwd "$EE_ROOT"

# When EE exits, kill the monitor
kill $MONITOR_PID 2>/dev/null

echo ""
echo "✅ EE session ended. Monitor closed."
