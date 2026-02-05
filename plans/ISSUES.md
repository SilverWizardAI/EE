# Known Issues - EE (Enterprise Edition)

**Track bugs and problems to fix**

---

## 🐛 Current Issues

### ⚠️ Issue #1: MM Mesh Service Registration Not Automatic
**Severity:** Medium
**Discovered:** 2026-02-05 (Test_App_PCC validation)

**Problem:**
Apps connect to MM mesh proxy as clients but don't automatically register as callable services.

**Evidence:**
- Apps initialize MeshClient successfully
- Apps can discover and call other services
- But: `curl http://localhost:6001/services` returns empty list
- Expected: Apps should register themselves as services

**Impact:**
- Apps can call services but can't be called by peers
- Parent CC can't send control commands to apps via mesh
- Peer-to-peer app communication limited

**Possible Causes:**
1. Registration is manual (requires explicit API call)
2. Template missing service registration code
3. Async timing issue (registration happens later)

**Next Steps:**
- [ ] Review mesh_integration.py for registration logic
- [ ] Check if MeshClient has auto-registration feature
- [ ] Add explicit service registration to template
- [ ] Test service-to-service communication

---

### ⚠️ Issue #2: Health Check Not Implemented
**Severity:** Low
**Discovered:** 2026-02-05 (Test_App_PCC validation)

**Problem:**
Registry health checks return "unknown" status for running apps.

**Evidence:**
```bash
python3 -m tools.registry --check-health TestApp1
# Returns: {"status": "unknown", "last_check": null, "uptime": 0}
```

**Impact:**
- Can't monitor app health proactively
- Can't detect degraded performance
- Parent CC can't trigger health-based interventions

**Possible Causes:**
1. Apps don't expose health endpoints
2. Registry tool doesn't actively probe apps
3. Health protocol not implemented in template

**Next Steps:**
- [ ] Add health endpoint to BaseApplication
- [ ] Implement health check in registry.py
- [ ] Add heartbeat mechanism to apps
- [ ] Test health monitoring workflow

---

## 📝 Notes

- Issues will be added as they're discovered during testing
- Mark resolved issues with ✅ and date
- Move resolved issues to bottom of file

---

## ✅ Resolved Issues

### ✅ Issue #R1: VERSION Import Bug (Fixed 2026-02-05)

**Problem:** Templates imported `get_version()` function instead of `VERSION` constant

**Error:**
```
TypeError: create_application() missing 1 required positional argument: 'app_version'
```

**Root Cause:**
Template used:
```python
from version_info import get_version
sys.exit(create_application(TestApp1, "TestApp1", get_version()))
```

But `get_version()` is a function, not a string. Should use VERSION constant.

**Fix Applied:**
```python
from version_info._version_data import VERSION
sys.exit(create_application(TestApp1, "TestApp1", VERSION))
```

**Files Fixed:**
- `templates/parent_cc/tools/create_app.py` (lines 279, 345, 372, 451)

**Commit:** (pending)

---

### ✅ Issue #R2: Constructor Signature Verified (Already Fixed)

**Status:** Template already has correct signature

**Template has:**
```python
def __init__(self, app_name: str = "{app_name}", app_version: str = "0.1.0", **kwargs):
    super().__init__(app_name=app_name, app_version=app_version, **kwargs)
```

**This was fixed in previous session** ✅
