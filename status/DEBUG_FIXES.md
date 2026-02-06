# EE Comms Protocol - Debug Fixes

**Created:** 2026-02-06
**Issue:** No communications between EE and EEM via MM mesh

---

## 🎯 Required Fixes

### 1. EEM: Check MM Running
### 2. EEM: Start MM if Not Running
### 3. EEM: Register with MM
### 4. EE: Register with MM on Cycle Start
### 5. EE: Send Progress Messages to EEM
### 6. Both: Prefix Log Messages with Source

---

## 📝 Fix #1-3: EEM Startup Code

**File:** `tools/ee_monitor_gui.py`

**Add to imports:**
```python
import subprocess
import time
import httpx
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
```

**Add after line 30 (in __init__):**
```python
def __init__(self, ee_root: Path):
    super().__init__()

    self.ee_root = ee_root
    self.next_steps_file = ee_root / "plans" / "NextSteps.md"
    self.current_cycle = 1

    # Setup file logging
    self.log_dir = ee_root / "logs"
    self.log_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    self.log_file = self.log_dir / f"ee_monitor_{today}.log"
    self.log_fh = open(self.log_file, 'a', encoding='utf-8')

    self.log_to_file("EEM: " + "="*60)
    self.log_to_file(f"EEM: EE Monitor started at {datetime.now().isoformat()}")
    self.log_to_file("EEM: " + "="*60 + "\n")

    # ===== NEW CODE STARTS HERE =====

    # 1. Check if MM mesh is running
    self.log_to_file("EEM: Checking if MM mesh is running...")
    if not self._check_mm_running():
        self.log_to_file("EEM: MM mesh NOT running - starting it...")
        if not self._start_mm_mesh():
            self.log_to_file("EEM: ❌ Failed to start MM mesh!")
            QMessageBox.critical(self, "Startup Error",
                "Failed to start MM mesh. Please start manually.")
            # Continue anyway - monitor can still work without MM
        else:
            self.log_to_file("EEM: ✅ MM mesh started successfully")
    else:
        self.log_to_file("EEM: ✅ MM mesh already running")

    # 2. Register EEM with MM mesh
    self.mm_registered = False
    if self._check_mm_running():
        self.log_to_file("EEM: Registering with MM mesh...")
        if self._register_with_mm():
            self.log_to_file("EEM: ✅ Registered with MM as 'ee_monitor'")
            self.mm_registered = True
        else:
            self.log_to_file("EEM: ⚠️ Failed to register with MM")

    # 3. Setup MM message polling
    if self.mm_registered:
        self.mm_poll_timer = QTimer(self)
        self.mm_poll_timer.timeout.connect(self._poll_mm_messages)
        self.mm_poll_timer.start(1000)  # Poll every second
        self.log_to_file("EEM: Message polling started (1s interval)")

    # ===== NEW CODE ENDS HERE =====

    self.init_ui()

    self.monitor_timer = QTimer(self)
    self.monitor_timer.timeout.connect(self.check_ee_status)
    self.monitor_timer.start(5000)
```

**Add these new methods to EEMonitorWindow class:**

```python
def _check_mm_running(self) -> bool:
    """Check if MM mesh is running on port 6001."""
    try:
        response = httpx.get("http://localhost:6001/services", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False

def _start_mm_mesh(self) -> bool:
    """Start MM mesh proxy in background."""
    try:
        mm_path = Path.home() / "Library/CloudStorage/Dropbox/A_Coding/MM"

        # Start MM mesh in background
        subprocess.Popen(
            ["python3", "-m", "mcp_mesh.proxy.server",
             "--http-only", "--http-port", "6001"],
            cwd=str(mm_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent
        )

        # Wait for it to start (max 10 seconds)
        for i in range(20):
            time.sleep(0.5)
            if self._check_mm_running():
                return True

        return False
    except Exception as e:
        self.log_to_file(f"EEM: Error starting MM: {e}")
        return False

def _register_with_mm(self) -> bool:
    """Register EEM as a service with MM mesh."""
    try:
        response = httpx.post(
            "http://localhost:6001/register",
            json={
                "instance_name": "ee_monitor",
                "port": 9998,  # Placeholder - EEM doesn't expose tools
                "tools": ["receive_message"]  # Tool to receive EE messages
            },
            timeout=5.0
        )
        return response.status_code == 200
    except Exception as e:
        self.log_to_file(f"EEM: Registration error: {e}")
        return False

def _poll_mm_messages(self):
    """Poll MM mesh for messages sent to ee_monitor."""
    # This is a simplified version - in production, MM would push messages
    # For now, we'll just check if EE is registered
    try:
        response = httpx.get("http://localhost:6001/services", timeout=2.0)
        if response.status_code == 200:
            services = response.json().get("services", [])

            # Look for EE instance
            for svc in services:
                if svc["instance_name"].startswith("ee_cycle_"):
                    # EE is registered - this is good
                    pass
    except Exception:
        pass

# Note: Real MM message receiving would require MM to support
# message queuing or webhooks. For now, EE will call HTTP endpoints.
```

**Update log_to_file to accept source prefix:**

```python
def log_to_file(self, text: str, source: str = None):
    """Log to file with optional source prefix."""
    if source:
        self.log_fh.write(f"{source}: {text}\n")
    else:
        # If text already has "EEM:" or "EE:" prefix, use as-is
        self.log_fh.write(f"{text}\n")
    self.log_fh.flush()
```

---

## 📝 Fix #4-5: EE Cycle Startup and Comms

**What I (EE) need to do at cycle start:**

```python
import httpx
import os

# At very start of cycle (before any work):

# 1. Verify MM is running
def check_mm_running() -> bool:
    try:
        response = httpx.get("http://localhost:6001/services", timeout=2.0)
        return response.status_code == 200
    except:
        return False

if not check_mm_running():
    print("❌ MM mesh not running! Cannot proceed.")
    exit(1)

# 2. Register with MM
cycle_num = 1  # Get from startup
instance_name = f"ee_cycle_{cycle_num}"

response = httpx.post(
    "http://localhost:6001/register",
    json={
        "instance_name": instance_name,
        "port": 9997,  # Placeholder
        "tools": []
    },
    timeout=5.0
)

if response.status_code != 200:
    print("⚠️ Failed to register with MM")

# 3. Send startup message to EEM
def send_to_eem(action: str, payload: dict):
    """Send message to EEM via MM mesh."""
    try:
        # Direct HTTP to EEM's endpoint (simpler than full MM routing)
        response = httpx.post(
            "http://localhost:6001/message/ee_monitor",
            json={
                "source": "ee",
                "cycle": cycle_num,
                "action": action,
                **payload
            },
            timeout=5.0
        )

        # Also log locally with "EE:" prefix
        with open(f"{ee_root}/logs/ee_comms.log", "a") as f:
            f.write(f"EE: [{datetime.now().isoformat()}] SENT {action}: {payload}\n")

        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Failed to send to EEM: {e}")
        return False

# Send cycle start
send_to_eem("cycle_start", {
    "cycle": cycle_num,
    "token_target": 20,
    "total_steps": 4
})

# 4. Before each step
send_to_eem("step_start", {
    "step": 1,
    "total_steps": 4,
    "description": "Extract mesh_integration.py"
})

# 5. After each step
send_to_eem("step_complete", {
    "step": 1,
    "total_steps": 4,
    "tokens_used": 20000,
    "tokens_limit": 200000
})

# 6. At cycle end
send_to_eem("cycle_end", {
    "last_step": 4,
    "next_step": 5,
    "tokens_used": 82000,
    "tokens_limit": 200000
})
```

---

## 📝 Fix #6: Log File Prefixes

### EEM Logs (ee_monitor_YYYYMMDD.log)

All EEM messages prefixed with `EEM:`
```
EEM: [2026-02-06 10:30:00] ═══ START CYCLE 1 ═══
EEM: Token target: 20%
EEM: Spawned EE instance
```

All EE messages prefixed with `EE:`
```
EE: [2026-02-06 10:30:05] CYCLE 1 | STEP 1/4 START
EE: Extracting mesh_integration.py
EE: [2026-02-06 10:32:15] CYCLE 1 | STEP 1/4 COMPLETE (tokens: 20K/200K)
```

### EE Logs (ee_comms.log)

New file for EE's communication log:
```
EE: [2026-02-06T10:30:05] SENT cycle_start: {'cycle': 1, 'token_target': 20}
EE: [2026-02-06T10:30:05] SENT step_start: {'step': 1, 'description': '...'}
EE: [2026-02-06T10:32:15] SENT step_complete: {'step': 1, 'tokens_used': 20000}
```

---

## 🔧 Implementation Order

1. **First:** Fix EEM (all 3 fixes at once)
2. **Test:** Restart EEM, confirm MM starts and EEM registers
3. **Then:** Create EE comms helper in `tools/ee_comms.py`
4. **Finally:** I use the helper in next cycle

---

## ✅ Verification Steps

After implementing:

1. **Start EEM** → Check log shows:
   ```
   EEM: Checking if MM mesh is running...
   EEM: ✅ MM mesh already running
   EEM: ✅ Registered with MM as 'ee_monitor'
   ```

2. **Check MM services:**
   ```bash
   curl http://localhost:6001/services | jq '.services[].instance_name'
   # Should show: "ee_monitor"
   ```

3. **Start EE cycle** → Check both logs show messages

4. **Verify prefixes** → All messages have "EE:" or "EEM:"

---

## 🎓 Architecture

```
┌─────────────┐
│  EE Monitor │ (EEM)
│   (GUI)     │
└──────┬──────┘
       │ 1. Checks MM running
       │ 2. Starts MM if needed
       │ 3. Registers as "ee_monitor"
       │ 4. Polls for messages
       │
       ▼
┌─────────────┐
│   MM Mesh   │ (Port 6001)
│   (Proxy)   │
└──────┬──────┘
       │
       │ Service registry:
       │ - ee_monitor (EEM)
       │ - ee_cycle_1 (EE instance)
       │
       ▼
┌─────────────┐
│     EE      │ (This Claude instance)
│  (Worker)   │
└──────┬──────┘
       │ 1. Checks MM at startup
       │ 2. Registers as "ee_cycle_N"
       │ 3. Sends messages to ee_monitor
       │ 4. Logs with "EE:" prefix
       │
       ▼
    Work done!
```

---

**Next:** Implement these fixes to EEM first, then create EE comms helper.
