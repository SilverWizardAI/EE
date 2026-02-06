# MM Mesh Stats Tracking - Implementation Guide

**Purpose:** MM writes stats to JSON file that EEM displays in UI

**File:** `~/.mm_mesh_stats.json`

---

## 📊 Stats File Format

```json
{
  "total_services": 5,
  "total_messages": 127,
  "last_updated": "2026-02-06T10:30:45.123456",
  "services": [
    {
      "name": "ee_monitor",
      "registered_at": "2026-02-06T10:20:00",
      "message_count": 0
    },
    {
      "name": "ee_cycle_1",
      "registered_at": "2026-02-06T10:25:30",
      "message_count": 12
    }
  ]
}
```

**Minimum Required:**
- `total_services` (int) - Number of active services
- `total_messages` (int) - Total messages processed since startup

**Optional:**
- `last_updated` (str) - ISO timestamp of last update
- `services` (list) - Details about each service

---

## 🔧 MM Implementation

### Location
**File:** `/A_Coding/MM/mcp_mesh/proxy/server.py` (or wherever the main proxy is)

### Add Stats Tracking Class

```python
import json
from pathlib import Path
from datetime import datetime
from threading import Lock

class MeshStats:
    """Track and persist MM mesh statistics."""

    def __init__(self, stats_file: Path = None):
        if stats_file is None:
            stats_file = Path.home() / ".mm_mesh_stats.json"

        self.stats_file = stats_file
        self.lock = Lock()

        # Initialize counters
        self.total_services = 0
        self.total_messages = 0
        self.services = {}  # {name: {"registered_at": timestamp, "count": N}}

        # Load existing stats if available
        self._load()

    def _load(self):
        """Load stats from file if it exists."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_messages = data.get("total_messages", 0)
                    # Don't load total_services - will be recalculated
            except Exception:
                pass  # Start fresh if file is corrupted

    def _save(self):
        """Save stats to file atomically."""
        try:
            data = {
                "total_services": self.total_services,
                "total_messages": self.total_messages,
                "last_updated": datetime.now().isoformat(),
                "services": [
                    {
                        "name": name,
                        "registered_at": info["registered_at"],
                        "message_count": info["count"]
                    }
                    for name, info in self.services.items()
                ]
            }

            # Write atomically (write to temp, then rename)
            temp_file = self.stats_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.stats_file)

        except Exception as e:
            print(f"Error saving stats: {e}")

    def service_registered(self, service_name: str):
        """Record a new service registration."""
        with self.lock:
            if service_name not in self.services:
                self.services[service_name] = {
                    "registered_at": datetime.now().isoformat(),
                    "count": 0
                }
                self.total_services = len(self.services)
                self._save()

    def service_deregistered(self, service_name: str):
        """Record a service deregistration."""
        with self.lock:
            if service_name in self.services:
                del self.services[service_name]
                self.total_services = len(self.services)
                self._save()

    def message_processed(self, service_name: str = None):
        """Record a message being processed."""
        with self.lock:
            self.total_messages += 1

            if service_name and service_name in self.services:
                self.services[service_name]["count"] += 1

            # Save every 10 messages to reduce I/O
            if self.total_messages % 10 == 0:
                self._save()

    def get_stats(self) -> dict:
        """Get current stats as dict."""
        with self.lock:
            return {
                "total_services": self.total_services,
                "total_messages": self.total_messages,
                "services": list(self.services.keys())
            }
```

---

## 🔗 Integration with MM Proxy

### In server.py (or main proxy file)

```python
# At module level
mesh_stats = MeshStats()

# In service registration handler
def register_service(instance_name: str, port: int, tools: list):
    # ... existing registration code ...

    # Track stats
    mesh_stats.service_registered(instance_name)

    return {"status": "registered"}

# In service deregistration handler
def deregister_service(instance_name: str):
    # ... existing deregistration code ...

    # Track stats
    mesh_stats.service_deregistered(instance_name)

    return {"status": "deregistered"}

# In message/tool call handler
def handle_tool_call(service_name: str, tool_name: str, arguments: dict):
    # ... existing handler code ...

    # Track stats
    mesh_stats.message_processed(service_name)

    return result
```

---

## 🧪 Testing

### Manual Test
```bash
# 1. Start MM with stats tracking
cd /A_Coding/MM
python3 -m mcp_mesh.proxy.server --http-only --http-port 6001

# 2. Check stats file created
cat ~/.mm_mesh_stats.json

# Expected:
# {
#   "total_services": 0,
#   "total_messages": 0,
#   "last_updated": "2026-02-06T10:30:00.123456"
# }

# 3. Register a service
curl -X POST http://localhost:6001/register \
  -H "Content-Type: application/json" \
  -d '{"instance_name": "test", "port": 5000, "tools": []}'

# 4. Check stats updated
cat ~/.mm_mesh_stats.json

# Expected:
# {
#   "total_services": 1,
#   "total_messages": 0,
#   ...
# }
```

### Integration Test with EEM
```bash
# 1. Start MM (with stats)
# 2. Start EEM
python3 tools/ee_monitor_gui.py

# 3. Check EEM UI shows:
# "MM: 1 services | 0 msgs"  (after ee_monitor registers)

# 4. Register another service
curl -X POST http://localhost:6001/register \
  -H "Content-Type: application/json" \
  -d '{"instance_name": "test2", "port": 5001, "tools": []}'

# 5. Watch EEM UI update to:
# "MM: 2 services | 0 msgs"
```

---

## 📈 Performance Considerations

### Write Frequency
- ✅ Every service registration/deregistration (rare events)
- ✅ Every 10 messages (reduces I/O)
- ❌ Every single message (too much I/O)

### Atomic Writes
- Write to `.mm_mesh_stats.tmp`
- Then rename to `.mm_mesh_stats.json`
- Prevents corruption if process crashes mid-write

### Thread Safety
- Use `threading.Lock()` to protect counters
- Prevents race conditions in multi-threaded proxy

---

## 🎨 EEM Display

**Format:** `MM: {services} services | {messages} msgs`

**Examples:**
- `MM: 0 services | 0 msgs` (startup, no services)
- `MM: 1 services | 0 msgs` (ee_monitor only)
- `MM: 2 services | 15 msgs` (ee_monitor + ee_cycle_1 active)
- `MM: 5 services | 1,247 msgs` (busy mesh)

**Colors:**
- 🟢 Green: Active and updating
- 🔴 Red: Error reading stats
- ⚫ Gray: No stats file yet

**Update Frequency:** Every 2 seconds

---

## ✅ Implementation Checklist

**MM Side:**
- [ ] Add `MeshStats` class to MM
- [ ] Initialize `mesh_stats = MeshStats()` in server
- [ ] Call `mesh_stats.service_registered()` on registration
- [ ] Call `mesh_stats.service_deregistered()` on deregistration
- [ ] Call `mesh_stats.message_processed()` on each tool call
- [ ] Test stats file is created and updated

**EEM Side (DONE):**
- [x] Add `mm_status_label` to UI
- [x] Add `_update_mm_status()` method
- [x] Add timer to read stats every 2 seconds
- [x] Display format: "MM: X services | Y msgs"
- [x] Color coding based on status

---

## 🔍 Troubleshooting

**"MM: No stats file"**
- MM hasn't created `~/.mm_mesh_stats.json` yet
- Check if MM is running
- Check if MeshStats class is initialized

**"MM: Error reading stats"**
- Stats file exists but is corrupted
- Delete `~/.mm_mesh_stats.json` and restart MM

**Stats not updating**
- Check file timestamp: `ls -la ~/.mm_mesh_stats.json`
- Check if MM is actually processing registrations
- Verify MeshStats methods are being called

---

**Next:** Implement `MeshStats` class in MM proxy server.
