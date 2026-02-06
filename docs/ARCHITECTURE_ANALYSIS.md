# CC Monitor - Deep Architectural Analysis

## Question 1: MM Mesh Auto-Cleanup - **BROKEN**

### What I Found

The MM mesh **HAS** health monitoring code but **DOES NOT RUN IT**.

**Evidence:**
```python
# In mcp_mesh/proxy/health.py
SERVICE_TIMEOUT_SECONDS = 120  # 2 minutes - mark as dead if no heartbeat

def check_service_health(registry):
    """Mark services with no heartbeat for 120s as dead"""
    # Updates status = 'dead' for services with old last_seen

def cleanup_dead_services(registry, older_than_hours=24):
    """Remove dead services that have been dead for a long time"""
    # Deletes dead services older than threshold
```

**Problem:** These functions exist but are NEVER called automatically!

- No background thread runs health checks
- No periodic cleanup scheduled
- Services stay "active" forever unless they manually heartbeat or deregister

**Current State:** The 4 stale services in the mesh (ee_cycle_4, ee_cycle_98, ee_cycle_99) prove this:
- They haven't sent heartbeat in HOURS
- They're still marked "active"
- No automatic cleanup occurred

### Root Cause

The proxy server (`mcp_mesh/proxy/server.py`) should start a background thread on startup:
```python
def _start_health_monitor(self):
    """Run health checks every 60 seconds"""
    while self.running:
        self.registry.check_service_health()
        time.sleep(60)
```

**This doesn't exist.** It's a missing feature, not a configuration issue.

### Impact on CC Monitor

Since auto-cleanup doesn't work, CC Monitor MUST:
1. Clean stale registrations on startup
2. Clean before starting new cycle
3. Implement its own health checking

**This is a workaround for a mesh bug, not a design flaw in CC Monitor.**

---

## Question 2: EE Monitor → CC Monitor Generalization

### Current State: Project-Specific

The current implementation is HARDCODED to "EE":
- Reads from `plans/NextSteps.md` (EE-specific file)
- Uses "ee_cycle_N" as instance names
- GUI title says "EE Monitor"
- All logs say "EE"

### Desired State: General-Purpose

**CC Monitor should work with ANY Claude Code project:**

```
User selects: /path/to/any/project
CC Monitor:
  1. Spawns Claude Code in that directory
  2. Injects prompt: "Read NextSteps.md, work until token limit"
  3. Monitors token usage
  4. Cycles when threshold reached
  5. Repeats until plan complete
```

### Required Changes

**Minimal changes needed - architecture already supports this!**

1. **Add directory picker** to GUI
   - User selects any folder
   - Monitor spawns Claude Code there

2. **Parameterize instance names**
   - Instead of: `ee_cycle_N`
   - Use: `{project_name}_cycle_N`
   - Example: `myapp_cycle_3`

3. **Parameterize prompt**
   - Current prompt assumes EE structure
   - New prompt should be generic: "Continue work from NextSteps.md"

4. **Configuration per project**
   - Token threshold
   - Heartbeat interval
   - Custom instructions (optional)

### Why This Works

The fundamental pattern is UNIVERSAL:
- **Any** long-running Claude Code task hits token limits
- **Any** multi-step plan benefits from cycling
- **Any** project can use NextSteps.md convention

**CC Monitor becomes a general automation tool.**

---

## Question 3: Is Polling the Right Architecture?

### The Core Problem: Agent Cognitive Load

You said: *"EE was having difficulty working asynchronously. It forgot to send messages."*

This is THE key insight. Let me analyze why:

### Why Agents Forget

Claude Code agents have limited working memory:
1. **Primary task focus** - "Implement feature X"
2. **Context tracking** - "I'm on step 3 of 10"
3. **Tool usage** - "I need to read this file, edit that file"
4. **Status reporting** - "I should update the monitor every 5 minutes"

**Problem:** #4 competes with #1-3. When deep in problem-solving, the agent forgets housekeeping.

### Architecture Options Compared

#### Option A: Pure Push (Original Attempt)

```
Agent -> sends updates -> Monitor
```

**Pros:**
- Real-time notifications
- Event-driven, efficient

**Cons:**
- Agent must REMEMBER to send updates
- If agent forgets, monitor has no visibility
- Requires agent to context-switch from main work
- **PROVEN TO FAIL** (your experience)

#### Option B: Pure Polling (Current Implementation)

```
Monitor -> polls status -> Agent
```

**Pros:**
- Agent doesn't need to remember
- Monitor always gets updates (if agent responds)
- Simpler agent mental model

**Cons:**
- Wasted polls when nothing happening
- Still requires agent to RUN HTTP server
- Still requires agent to MAINTAIN state
- If agent crashes, server dies anyway

#### Option C: File-Based Monitoring (Simplest)

```
Agent -> writes to file -> Monitor polls file
```

**Pros:**
- No HTTP server needed!
- Agent just writes a file (natural for Claude Code)
- File persists even if agent crashes
- Extremely simple

**Cons:**
- No direct token count access (need to parse logs?)
- File writes could be forgotten too (same as push)

#### Option D: Built-in Claude Code Monitoring (Ideal)

```
Claude Code exposes /status endpoint natively
Monitor -> polls Claude Code directly -> No agent cooperation needed
```

**Pros:**
- Agent does NOTHING
- Token count always available
- Works even if agent is stuck/confused
- Most reliable

**Cons:**
- Requires Claude Code core changes
- May not be feasible

#### Option E: Hybrid with Tooling

```
Agent has MCP tool "cc_monitor.update_status"
Monitor polls as fallback
```

**Pros:**
- Agent CAN push updates (optional, for responsiveness)
- Monitor polls as safety net (catches forgotten updates)
- Best of both worlds

**Cons:**
- More complex
- Tool call is still something agent can forget

### My Recommendation: **Polling + Tool (Option E)**

Here's why:

1. **Keep polling as PRIMARY** - Reliable, catches everything
2. **Add MCP tool as OPTIONAL** - If agent remembers, great; if not, polling catches it
3. **Minimize agent burden** - Make status reporting DEAD SIMPLE

### Making Polling Work Better

The current polling approach fails on one thing: **Agent must run HTTP server**

**Solutions:**

**A) Simplify Server Startup**
Instead of asking agent to:
```python
from tools.ee_http_server import init_server, update_status
server = init_server(cycle_number=1)
update_status(step=1, task="...", tokens_used=20000)
```

Provide a simple MCP tool:
```python
# Agent just calls this tool naturally
cc_status.update(step=1, task="Working on auth", tokens=20000)
```

The tool:
- Starts HTTP server automatically (if not running)
- Registers with mesh
- Updates status
- Agent doesn't manage server lifecycle

**B) Make It Required, Not Optional**

Current prompt says "CRITICAL FIRST STEP" but this gets buried. Instead:

**Inject server startup BEFORE agent prompt:**
```python
# CC Monitor starts server on agent's behalf
# Agent just updates status via tool calls
# If agent forgets, polling still works
```

**C) Use Claude Code's Built-in Tools (if available)**

Does Claude Code itself provide:
- Token usage API?
- Status reporting mechanism?
- Progress tracking?

If yes, use those. If no, we need the HTTP server approach.

---

## Architectural Recommendation

### Short-term: Fix Current Design

1. **Fix MM mesh auto-cleanup** (add health check thread)
2. **Simplify HTTP server startup** (make it automatic/invisible)
3. **Add file-based status as fallback** (agent writes, monitor reads)
4. **Improve polling reliability** (better error handling)

### Long-term: Generalize to CC Monitor

1. **Add directory picker** (any project)
2. **Parameterize configuration** (per-project settings)
3. **Provide MCP tool** (`cc_monitor.update_status`)
4. **Document pattern** (NextSteps.md convention)

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│ CC Monitor (PyQt6 GUI)                          │
│                                                 │
│ - Directory picker: Select any CC project      │
│ - Token threshold: 80%                          │
│ - Heartbeat polling: Every 5 minutes            │
│ - Cycle management: Terminate + Restart         │
└──────────────┬──────────────────────────────────┘
               │
               │ (polls every 5 min)
               ↓
┌─────────────────────────────────────────────────┐
│ MM Mesh Proxy (Service Registry)                │
│                                                 │
│ - Auto health checks (every 60s) ← FIX THIS     │
│ - Routes: call_service(target, tool, args)      │
│ - Cleanup: Removes dead services automatically  │
└──────────────┬──────────────────────────────────┘
               │
               │ (routes to)
               ↓
┌─────────────────────────────────────────────────┐
│ Claude Code Instance (Terminal)                 │
│                                                 │
│ Working on: /path/to/any/project                │
│ Current: Step 3 of 10, tokens: 65%              │
│                                                 │
│ HTTP Server (auto-started by monitor)           │
│ - GET /status → {step, tokens, task}            │
│ - Updates status via MCP tool (optional)        │
│                                                 │
│ Fallback: Writes status.json if all else fails  │
└─────────────────────────────────────────────────┘
```

### Why This Works

1. **Minimal agent burden** - Agent just works, status happens automatically
2. **Reliable polling** - Monitor always knows state
3. **Graceful degradation** - If HTTP fails, file fallback works
4. **Universal pattern** - Works for any Claude Code project
5. **Automatic cleanup** - Dead services removed by mesh (once fixed)

---

## Critical Path Forward

### Must Fix:
1. **MM mesh auto-cleanup** - This is a bug, must be fixed
2. **HTTP server auto-start** - Agent shouldn't manage this
3. **Generalize to any project** - Remove EE hardcoding

### Should Add:
4. **File-based fallback** - status.json as safety net
5. **MCP tool for status** - Make reporting natural for agent
6. **Better error handling** - Distinguish real errors from expected events

### Could Enhance:
7. **Multi-project tracking** - Monitor multiple projects simultaneously
8. **Cycle history viewer** - See all past cycles, token usage trends
9. **Smart prompting** - Inject context from previous cycle

---

## Final Answer

**Q1: MM mesh auto-cleanup?**
- Exists but broken (not running)
- Needs background health check thread
- CC Monitor must work around this bug

**Q2: Generalize to CC Monitor?**
- Yes, absolutely!
- Minimal changes needed
- Architecture already supports it

**Q3: Is polling the right approach?**
- **Yes, polling is correct** given agent cognitive load
- But simplify what agent must do (auto-start server)
- Add file fallback for resilience
- Optional push via MCP tool for efficiency

**Bottom line:** Keep polling, fix mesh cleanup, remove agent burden, generalize to any project.
