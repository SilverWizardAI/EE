# Test Plan 2 - Multi-Cycle Autonomous Workflow

**Status:** 🚧 Active
**Date:** 2026-02-07
**Objective:** Validate multi-cycle orchestration with state persistence, git commits, and intelligent cycle management.

---

## Overview

**Total Steps:** 7
**Cycles:** 4
- Cycle 1: Steps 1-2
- Cycle 2: Steps 3-4
- Cycle 3: Steps 5-6
- Cycle 4: Step 7

**Your Cycle Number:** [CCM will tell you in the startup prompt]

---

## How This Works

1. **Check Next_Steps.md** - This file tracks which step to execute next
2. **Execute the step** - Follow instructions for that step
3. **Update Next_Steps.md** - Write the next step number
4. **Commit** - Use git to commit your change
5. **Report** - Send log_message to CCM
6. **End of Cycle** - After even steps (2, 4, 6), report "End of Cycle X"
7. **CCM restarts you** - New TCC instance continues from Next_Steps.md

---

## Instructions

**IMPORTANT:** Always read Next_Steps.md first to see which step to execute!

### Step 1: Initialize Workflow

**Actions:**
1. Create Next_Steps.md with content: "Next: Step 2"
2. Commit with message: "Step 1: Initialize workflow"
3. Send log_message: "Step 1 complete"

**DO NOT** report "End of Cycle" (odd step)

---

### Step 2: Complete Cycle 1

**Actions:**
1. Update Next_Steps.md to: "Next: Step 3"
2. Commit with message: "Step 2: Complete Cycle 1"
3. Send log_message: "Step 2 complete"
4. Send log_message: "End of Cycle 1"

**This will trigger CCM to terminate you and start Cycle 2!**

---

### Step 3: Start Cycle 2

**Actions:**
1. Update Next_Steps.md to: "Next: Step 4"
2. Commit with message: "Step 3: Start Cycle 2"
3. Send log_message: "Step 3 complete"

**DO NOT** report "End of Cycle" (odd step)

---

### Step 4: Complete Cycle 2

**Actions:**
1. Update Next_Steps.md to: "Next: Step 5"
2. Commit with message: "Step 4: Complete Cycle 2"
3. Send log_message: "Step 4 complete"
4. Send log_message: "End of Cycle 2"

**This will trigger CCM to terminate you and start Cycle 3!**

---

### Step 5: Start Cycle 3

**Actions:**
1. Update Next_Steps.md to: "Next: Step 6"
2. Commit with message: "Step 5: Start Cycle 3"
3. Send log_message: "Step 5 complete"

**DO NOT** report "End of Cycle" (odd step)

---

### Step 6: Complete Cycle 3

**Actions:**
1. Update Next_Steps.md to: "Next: Step 7"
2. Commit with message: "Step 6: Complete Cycle 3"
3. Send log_message: "Step 6 complete"
4. Send log_message: "End of Cycle 3"

**This will trigger CCM to terminate you and start Cycle 4!**

---

### Step 7: Finalize Workflow

**Actions:**
1. Update Next_Steps.md to: "All steps complete"
2. Commit with message: "Step 7: Finalize workflow"
3. Send log_message: "Step 7 complete"
4. Send log_message: "Plan Fully Executed"

**This signals CCM that the entire plan is complete!**

---

## How to Send Messages

Use the MCP server's `log_message` tool. Since TCC doesn't have direct MCP tool access, use the Unix socket:

```bash
echo '{"method":"log_message","message":"YOUR MESSAGE HERE"}' | \
  nc -U /tmp/ccm_session_*.sock
```

Example for Step 1:
```bash
echo '{"method":"log_message","message":"Step 1 complete"}' | \
  nc -U /tmp/ccm_session_*.sock
```

---

## How to Commit

Use standard git commands:

```bash
git add Next_Steps.md
git commit -m "Step X: Description"
```

**DO NOT PUSH** - Just commit locally. CCM project doesn't need remote pushes.

---

## Success Criteria

- ✅ All 7 steps executed successfully
- ✅ Next_Steps.md updated after each step
- ✅ Git commits created for each step
- ✅ "End of Cycle" reported at steps 2, 4, 6
- ✅ "Plan Fully Executed" reported at step 7
- ✅ CCM orchestrates 4 TCC lifecycles
- ✅ State persists across TCC restarts
- ✅ Final state: Next_Steps.md says "All steps complete"

---

## Notes

- **State File:** Next_Steps.md is your memory across cycles
- **Cycle Context:** CCM tells you your cycle number in startup prompt
- **Termination:** CCM terminates you immediately on "End of Cycle"
- **Continuation:** New TCC reads Next_Steps.md and continues
- **Completion:** "Plan Fully Executed" stops the orchestration

---

## Expected Timeline

```
Cycle 1 (TCC #1): Steps 1-2 → "End of Cycle 1"
         ↓ (CCM terminates and restarts)
Cycle 2 (TCC #2): Steps 3-4 → "End of Cycle 2"
         ↓ (CCM terminates and restarts)
Cycle 3 (TCC #3): Steps 5-6 → "End of Cycle 3"
         ↓ (CCM terminates and restarts)
Cycle 4 (TCC #4): Step 7 → "Plan Fully Executed"
         ↓ (CCM terminates and stops)
```

**Total TCC Instances:** 4
**Total Commits:** 7
**Total Messages:** 7 completions + 3 end-of-cycle + 1 fully executed = 11 messages

---

Good luck! 🚀
