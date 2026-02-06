# 📕 IMMEDIATE NEXT ACTION (Step 3 - DO THIS NOW)

**Last Updated:** 2026-02-06
**Current Cycle:** 1
**Current Phase:** Foundation Components Extraction

---

## 🚨 YOU ARE HERE - STEP 3

**Reading Order:**
1. ❌ Step 1 (MISSION.md) - Skip unless confused
2. ✅ Step 2 (CURRENT_CYCLE.md) - You just read this
3. ✅ **YOU ARE HERE** - This is Step 3 - DO THIS NOW

---

## 🎯 NEXT IMMEDIATE ACTION

### Extract mesh_integration.py

**Priority:** HIGH (everything depends on this)
**Estimated Time:** 15-20 minutes
**Estimated Tokens:** 8K-12K

---

## 📝 Exact Steps to Execute

### Step 3.1: Read the Source File

```bash
# Location of source file
SOURCE="/A_Coding/Test_App_PCC/templates/pyqt_app/mesh_integration.py"

# Read it completely to understand what it does
cat "$SOURCE"
```

**What to look for:**
- Dependencies (what it imports)
- Hardcoded paths or values
- Any app-specific customizations
- Size (should be 200-300 lines)

---

### Step 3.2: Create Destination Directory (if needed)

```bash
# Ensure sw_core directory exists
mkdir -p /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared/sw_core

# Create __init__.py if it doesn't exist
touch /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared/sw_core/__init__.py
```

---

### Step 3.3: Copy the File

```bash
# Copy to destination
cp "$SOURCE" /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared/sw_core/mesh_integration.py

# Verify it was copied
ls -lh /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared/sw_core/mesh_integration.py
```

---

### Step 3.4: Review for Hardcoded Values

**Common things to check:**
- ❌ Hardcoded proxy URL (should use parameter or env var)
- ❌ Hardcoded app names
- ❌ Absolute file paths
- ❌ Development-only debug code

**If found:** Replace with configurable parameters

---

### Step 3.5: Test the Import

```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE

# Test basic import
python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE')

try:
    from shared.sw_core.mesh_integration import MeshIntegration
    print("✅ Import successful!")
    print(f"MeshIntegration class: {MeshIntegration}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
EOF
```

**Expected output:** `✅ Import successful!`

---

### Step 3.6: Test Basic Functionality

**Prerequisites:**
- MM mesh must be running on port 6001
- If not running, start it first

```bash
# Check if MM mesh is running
curl http://localhost:6001/services 2>/dev/null && echo "✅ MM mesh is running" || echo "❌ MM mesh not running"

# If not running, start it:
# cd /A_Coding/MM
# python -m mcp_mesh.proxy.server &
```

**Test mesh connection:**

```python
# Test script (save or run inline)
import sys
sys.path.insert(0, '/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE')

from shared.sw_core.mesh_integration import MeshIntegration

# Create instance
mesh = MeshIntegration(
    app_name="TestApp",
    app_version="1.0.0",
    proxy_url="http://localhost:6001"
)

# Try to connect
result = mesh.register()
print(f"Registration result: {result}")

# Try a heartbeat
hb_result = mesh.send_heartbeat()
print(f"Heartbeat result: {hb_result}")

print("✅ mesh_integration works!")
```

**Expected:** Registration and heartbeat succeed

---

### Step 3.7: Update Status File

```bash
# Mark task complete
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE

# Update LIBRARY_EXTRACTION_STATUS.md
# Change this line:
#   - [ ] Extracted mesh_integration.py
# To:
#   - [x] Extracted mesh_integration.py
```

**Or use helper script (if it exists):**

```bash
python tools/update_extraction_status.py "Extracted mesh_integration.py"
```

---

### Step 3.8: Commit Your Work

```bash
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE

git add shared/sw_core/mesh_integration.py
git add shared/sw_core/__init__.py
git add status/LIBRARY_EXTRACTION_STATUS.md

git commit -m "feat: Extract mesh_integration from Test_App_PCC template

- Copied from Test_App_PCC/templates/pyqt_app/
- Tested import and basic functionality
- Verified mesh connection and heartbeat
- Part of Cycle 1: Foundation Components

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push
```

---

### Step 3.9: Update CURRENT_CYCLE.md

**Move completed task:**

In `plans/CURRENT_CYCLE.md`, move mesh_integration from "In Progress" to "Completed":

```markdown
### ✅ Completed This Cycle
- [x] ...existing items...
- [x] Extract `mesh_integration.py`  ← ADD THIS

### 🚧 In Progress
- [ ] Extract `settings_manager.py` ← NEXT
```

---

### Step 3.10: Update THIS File (IMMEDIATE_NEXT.md)

**Change "NEXT IMMEDIATE ACTION" to next component:**

```markdown
## 🎯 NEXT IMMEDIATE ACTION

### Extract settings_manager.py

**Priority:** HIGH
**Estimated Time:** 15-20 minutes
**Estimated Tokens:** 8K-12K
```

---

## ✅ Success Criteria for This Action

**You're done when:**
- ✅ File copied to `shared/sw_core/mesh_integration.py`
- ✅ Import works without errors
- ✅ Basic functionality tested (register + heartbeat)
- ✅ Status file updated with [x]
- ✅ Changes committed and pushed
- ✅ CURRENT_CYCLE.md updated
- ✅ THIS file (IMMEDIATE_NEXT.md) updated to next action

---

## 🔄 After Completing This Action

**NEXT ACTION:** Extract settings_manager.py

**Source:** `/A_Coding/Test_App_PCC/templates/pyqt_app/settings_manager.py`
**Destination:** `EE/shared/sw_core/settings_manager.py`

**Follow same process:**
1. Read source
2. Copy to destination
3. Test import
4. Test functionality (save/load settings)
5. Update status
6. Commit
7. Update CURRENT_CYCLE.md
8. Update THIS file to next action (spawn_claude.py)

---

## ⚠️ If Something Goes Wrong

### Import Fails
**Check:**
- ✅ File actually copied to correct location?
- ✅ Python path includes EE directory?
- ✅ No syntax errors in copied file?
- ✅ All dependencies available?

### Mesh Connection Fails
**Check:**
- ✅ MM mesh running on port 6001?
- ✅ Firewall blocking connection?
- ✅ Proxy URL correct in code?

### Can't Commit
**Check:**
- ✅ Git repository initialized?
- ✅ Remote configured?
- ✅ Authentication working?

**If truly stuck:**
1. Document the blocker
2. Commit what you have
3. Move to next independent task (settings_manager doesn't depend on mesh)
4. Come back to this later

---

## 📊 Token Tracking

**After completing this action:**
- Starting tokens: ~65K
- This action: ~8-12K
- Estimated total: ~73-77K
- Status: ✅ Healthy (well below 85% threshold)

**Continue to next action without concern.**

---

## 🔗 Quick Reference

**If you need more context:**
- `plans/STRATEGIC/LIBRARY_COMPONENTS.md` - Detailed spec for mesh_integration
- `plans/CURRENT_CYCLE.md` - Full cycle status
- `plans/STRATEGIC/MISSION.md` - Big picture (if confused)

**Status tracking:**
- `status/LIBRARY_EXTRACTION_STATUS.md` - Completion checkboxes

---

## 💡 Pro Tip

**Speed up the process:**

```bash
# All-in-one extraction script (optional)
cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE

# 1. Copy
cp /A_Coding/Test_App_PCC/templates/pyqt_app/mesh_integration.py shared/sw_core/

# 2. Test import
python3 -c "from shared.sw_core.mesh_integration import MeshIntegration; print('OK')"

# 3. Commit
git add shared/sw_core/mesh_integration.py
git commit -m "feat: Extract mesh_integration from Test_App_PCC template"
git push

# 4. Update status
# (Do this part manually or with helper script)
```

**But recommended:** Follow the detailed steps first time to ensure quality.

---

**GO! Start with Step 3.1 - Read the source file!** 🚀
