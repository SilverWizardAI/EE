# CCM Test Plans Library

This directory contains test plans for validating CCM (Claude Code Monitor) functionality.

## Plans

### Plan_1.md (ARCHIVED) ✅
**Status:** Completed 2026-02-07
**Type:** Basic monitoring validation
**Steps:** 4 (3 messages)
**Cycles:** Single cycle

**Objective:** Validate basic TCC ↔ CCM communication and watchdog behavior.

**Results:**
- ✅ 100% message delivery (3/3)
- ✅ Watchdog timeout accuracy: 120.0s
- ✅ Clean TCC termination

**Conclusion:** Basic CCM monitoring validated successfully.

---

### Plan_2.md (ACTIVE) 🚧
**Status:** Active
**Type:** Multi-cycle autonomous workflow
**Steps:** 7
**Cycles:** 4 (steps 1-2, 3-4, 5-6, 7)

**Objective:** Validate multi-cycle orchestration with state persistence, git commits, and intelligent cycle management.

**Features:**
- State persistence via Next_Steps.md
- Git commits after each step
- Cycle-aware TCC spawning
- Intelligent termination on "End of Cycle X"
- Plan completion detection on "Plan Fully Executed"

**Expected Behavior:**
```
Cycle 1 (TCC #1): Steps 1-2 → "End of Cycle 1" → CCM terminates
Cycle 2 (TCC #2): Steps 3-4 → "End of Cycle 2" → CCM terminates
Cycle 3 (TCC #3): Steps 5-6 → "End of Cycle 3" → CCM terminates
Cycle 4 (TCC #4): Step 7 → "Plan Fully Executed" → CCM stops
```

**Validation Criteria:**
- ✅ All 7 steps executed
- ✅ Next_Steps.md updated after each step
- ✅ 7 git commits created
- ✅ 3 "End of Cycle" messages
- ✅ 1 "Plan Fully Executed" message
- ✅ 4 TCC lifecycles orchestrated
- ✅ Clean state persistence

---

## Plan Format

Each plan should include:

1. **Metadata**
   - Status (Active, Completed, Archived)
   - Date
   - Objective
   - Type

2. **Overview**
   - Total steps
   - Number of cycles
   - Expected messages

3. **Instructions**
   - Step-by-step actions
   - When to commit
   - When to report

4. **Success Criteria**
   - What validates completion
   - Expected outcomes

5. **Notes**
   - Special considerations
   - Expected timeline

---

## Usage

Plans are automatically copied to test projects by `tcc_setup.py`:

1. CCM instruments project with `TCCSetup.instrument_project()`
2. Active plan (Plan_2.md) copied to project root as `Plan.md`
3. TCC reads and executes `Plan.md`
4. CCM orchestrates based on plan messages

---

## Creating New Plans

To add a new plan:

1. Create `Plan_X.md` in this directory
2. Update `tcc_setup.py` to reference new plan
3. Test thoroughly before marking as active
4. Archive previous active plan with results

---

**Current Active Plan:** Plan_2.md (Multi-cycle workflow)
