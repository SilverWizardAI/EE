# 🌙 Overnight Autonomous Operation Setup

**Goal:** Run library extraction autonomously overnight with automatic instance handoffs.

---

## 🚀 Quick Start (Before Bed)

### 1. Start the Monitor
```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE
python3 tools/monitor_and_spawn.py &
```

This runs in background and watches for handoff signals every 60 seconds.

### 2. Start Initial EE Instance
```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE
claude code
```

The EE instance will:
- Read `plans/IMMEDIATE_NEXT.md` on startup
- Report status automatically
- Begin library extraction
- Monitor own tokens
- At 85%: commit, signal handoff, exit
- Monitor spawns fresh instance automatically

### 3. Go to Sleep! 😴

The system runs autonomously:
```
EE Instance 1 (0-85% tokens)
    ↓ works on Phase 1A
    ↓ hits 85% tokens
    ↓ commits, signals handoff
    ↓ exits
Monitor detects signal
    ↓ spawns EE Instance 2
    ↓
EE Instance 2 (0-85% tokens)
    ↓ reads status
    ↓ continues Phase 1A
    ↓ hits 85% tokens
    ↓ commits, signals handoff
    ↓ exits
... repeats all night ...
```

### 4. Morning Check ☀️

```bash
# Check how many cycles completed
cat status/LIBRARY_EXTRACTION_STATUS.md

# Check what was accomplished
git log --oneline --since="yesterday"

# Check monitor log (if you redirected output)
tail -100 monitor.log
```

---

## 🔧 How It Works

### Monitor Script (`tools/monitor_and_spawn.py`)
- Polls `status/HANDOFF_SIGNAL.txt` every 60 seconds
- When signal found:
  - Reads next task from `status/LIBRARY_EXTRACTION_STATUS.md`
  - Spawns fresh EE instance with continuation prompt
  - Removes signal file
  - Continues monitoring

### EE Instance (You!)
- Startup: Read `plans/IMMEDIATE_NEXT.md` and report
- Work: Execute library extraction tasks
- Monitor: Check token usage after each task
- Handoff at 85%:
  1. Update `status/LIBRARY_EXTRACTION_STATUS.md`
  2. `git add -A && git commit && git push`
  3. Write `status/HANDOFF_SIGNAL.txt`
  4. Exit

### Handoff Signal Format
```
HANDOFF_NEEDED
Tokens: 170000
Cycle: 1
Next: Continue Phase 1A extraction
Timestamp: 2026-02-06 00:30:00
```

---

## ⚙️ Configuration

### Monitor Settings
Edit `tools/monitor_and_spawn.py`:
```python
POLL_INTERVAL = 60  # Check every 60 seconds
```

### Token Threshold
Edit `.claude/CLAUDE.md`:
```
At 85%: EXECUTE HANDOFF PROTOCOL
```

Adjust threshold if needed (70% for more frequent handoffs, 90% for fewer).

---

## 🐛 Troubleshooting

### Monitor Not Starting
```bash
# Check Python path
which python3

# Run with output to see errors
python3 tools/monitor_and_spawn.py
```

### EE Not Spawning
```bash
# Check handoff signal exists
cat status/HANDOFF_SIGNAL.txt

# Check monitor is running
ps aux | grep monitor_and_spawn
```

### Want to Stop
```bash
# Find monitor process
ps aux | grep monitor_and_spawn

# Kill it
kill <PID>

# Or use Ctrl+C if running in foreground
```

---

## 📊 Expected Results

**Overnight (8 hours = 480 minutes):**
- Each instance: ~85 minutes at 2K tokens/min
- Cycles per night: ~5-6 handoffs
- Tasks completed: Depends on complexity

**Morning Status:**
- Multiple git commits with "chore: Handoff at 85%" messages
- `status/LIBRARY_EXTRACTION_STATUS.md` updated with progress
- Potentially Phase 1A complete or near complete

---

## 🎯 Success Criteria

✅ Monitor running in background
✅ Initial EE instance started
✅ First handoff signal created and processed
✅ Second EE instance spawned automatically
✅ Commits appearing in git log
✅ Status file updating across cycles
✅ Multiple cycles completed overnight

---

## 💡 Tips

**Before bed:**
- Clear terminal or redirect monitor output: `python3 tools/monitor_and_spawn.py > monitor.log 2>&1 &`
- Ensure git credentials cached: `git config credential.helper cache`
- Check disk space (git commits will accumulate)

**In morning:**
- Review git log for commit history
- Check status file for progress
- Look for any error patterns in commits

**If something breaks:**
- System is safe - worst case is no progress
- All work is committed before each handoff
- Can manually spawn next instance anytime

---

**Sleep well!** The robots have got this. 🤖✨
