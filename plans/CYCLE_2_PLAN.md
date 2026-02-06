# Cycle 2 - Library Extraction Plan

**Date:** 2026-02-06
**Token Target:** 20% (40K tokens)
**Status:** Ready to Start

---

## 🎯 Goal

Create **sw_pcc** library with Parent CC tooling extracted from Test_App_PCC.

---

## 📋 Tasks for Cycle 2

### Step 1: Create sw_pcc Directory Structure
- Create `shared/sw_pcc/` directory
- Create `shared/sw_pcc/__init__.py`
- Create `shared/sw_pcc/README.md`

### Step 2: Extract registry.py
- **Source:** `/A_Coding/Test_App_PCC/tools/registry.py`
- **Destination:** `shared/sw_pcc/registry.py`
- **Purpose:** App registry management

### Step 3: Extract create_app.py
- **Source:** `/A_Coding/Test_App_PCC/tools/create_app.py`
- **Destination:** `shared/sw_pcc/create_app.py`
- **Purpose:** App creation from templates

### Step 4: Extract launcher.py
- **Source:** `/A_Coding/Test_App_PCC/tools/launch_app.py`
- **Destination:** `shared/sw_pcc/launcher.py`
- **Purpose:** App launching and management

### Step 5: Create pyproject.toml
- Create `shared/sw_pcc/pyproject.toml`
- Define dependencies
- Make installable package

---

## 🔧 Additional Tasks

### Create EE Comms Helper
**File:** `tools/ee_comms.py`

**Purpose:** Helper for EE to send messages to EEM via MM

**Functions needed:**
```python
def register_with_mm(cycle_num: int) -> bool
def send_cycle_start(cycle: int, token_target: int, total_steps: int)
def send_step_start(step: int, total_steps: int, description: str)
def send_step_complete(step: int, total_steps: int, tokens_used: int)
def send_cycle_end(last_step: int, next_step: int, tokens_used: int)
```

---

## ✅ Expected Completion

By end of Cycle 2:
- ✅ sw_pcc library created
- ✅ 4 modules extracted
- ✅ pyproject.toml created
- ✅ EE comms helper functional
- ✅ Full comms protocol working

---

## 📊 Progress Tracking

**From Cycle 1:**
- sw_core: 8/8 modules complete (100%)

**Cycle 2 Target:**
- sw_pcc: 4/4 modules (registry, create_app, launcher, pyproject)
- ee_comms: 1 helper module

**Total:** 5 items to complete

---

## 🎯 Success Criteria

- [ ] All sw_pcc modules extracted and working
- [ ] pyproject.toml allows `pip install -e shared/sw_pcc`
- [ ] EE comms helper created and tested
- [ ] Messages flow: EE → MM → EEM
- [ ] EEM UI shows live progress updates
- [ ] All changes committed and pushed

---

**Ready for Cycle 2!** 🚀
