# 🎯 STRATEGIC MISSION (Step 1 - Read if Confused/Lost)

**Project:** EE - Shared Library Extraction
**Mission Owner:** Silver Wizard Software - Enterprise Architect
**Started:** 2026-02-05
**Expected Completion:** Multi-cycle (3-10 cycles)

---

## 🚨 WHEN TO READ THIS

**Read this file ONLY if:**
- ✅ You're confused about the overall goal
- ✅ You've lost context about what you're supposed to be doing
- ✅ CURRENT_CYCLE.md and IMMEDIATE_NEXT.md don't make sense

**Otherwise:**
- ➡️ Skip this and go straight to **Step 2** (CURRENT_CYCLE.md)

---

## 🎯 THE BIG PICTURE

### Mission Statement

**Extract reusable components from working sister projects and package them as shared libraries for the entire Silver Wizard Software ecosystem.**

### Why This Matters

Currently, every Silver Wizard project (CMC, MacR, C3, MM, etc.) has its own copies of common infrastructure:
- Base application framework (PyQt6 setup, mesh integration, settings)
- Parent CC protocol (spawn, monitor, control)
- Module monitoring and health checks
- Version management
- App creation tools

**This creates:**
- ❌ Code duplication across 8+ projects
- ❌ Bug fixes must be applied multiple times
- ❌ Inconsistent implementations
- ❌ Slow onboarding for new projects

**After library extraction:**
- ✅ Single source of truth for shared code
- ✅ Fix once, benefit everywhere
- ✅ Consistent patterns across ecosystem
- ✅ New projects start with working infrastructure

---

## 📦 What We're Building

### Two Main Libraries

**1. sw_core** (Application Framework)
- Base application class with PyQt6 setup
- MM mesh integration
- Parent CC protocol
- Settings management
- Module monitoring
- Version info management

**2. sw_pcc** (Parent CC Tools)
- App creation tool (create_app.py)
- App registry and discovery
- App launcher (launch_app.py)
- Batch operations

---

## 🔄 The Multi-Cycle Strategy

### Why Multiple Cycles?

This is a **large extraction project** that spans multiple working codebases. It requires:
- Reading source code from 4+ sister projects
- Careful extraction to preserve functionality
- Testing each component after extraction
- Documenting APIs and usage
- Updating templates to use new libraries

**You will NOT finish this in one cycle.** That's expected and by design.

### How Handoffs Work

When you approach 85% token usage (~170K tokens):
1. ✅ Commit your current work
2. ✅ Update status files (LIBRARY_EXTRACTION_STATUS.md)
3. ✅ Update CURRENT_CYCLE.md with progress
4. ✅ Push to remote
5. ✅ Signal handoff (the system handles spawning)

**The next instance will:**
- Read CURRENT_CYCLE.md (Step 2) to understand progress
- Read IMMEDIATE_NEXT.md (Step 3) to know what to do next
- Continue exactly where you left off

---

## 📋 Source Projects

### Where to Scavenge From

**Primary Sources:**
1. `/A_Coding/Test_App_PCC/` - Latest template with all features
2. `/A_Coding/CMC/` - Production app with working mesh integration
3. `/A_Coding/PIW/` - Has excellent version_info module
4. `/A_Coding/C3/` - Has advanced monitoring and control

**What to Extract:**
- ✅ Code that's proven to work
- ✅ Patterns used across multiple projects
- ✅ Infrastructure, not business logic
- ✅ Well-tested, stable code

**What NOT to Extract:**
- ❌ App-specific business logic
- ❌ Experimental/unproven code
- ❌ Hard-coded paths or credentials
- ❌ UI-specific code (belongs in templates)

---

## ✅ Definition of Success

### Project Complete When:

1. **sw_core package exists**
   - ✅ All modules extracted and working
   - ✅ pyproject.toml with proper dependencies
   - ✅ Can be installed with `pip install -e shared/sw_core`
   - ✅ Documentation complete

2. **sw_pcc package exists**
   - ✅ All tools extracted and working
   - ✅ Can create new apps from command line
   - ✅ Can launch/manage apps
   - ✅ Documentation complete

3. **Templates updated**
   - ✅ pyqt_app template uses sw_core
   - ✅ No more inline copies of shared code
   - ✅ New apps get shared libraries automatically

4. **Proven to work**
   - ✅ Created test app from template
   - ✅ Test app runs correctly
   - ✅ Test app integrates with MM mesh
   - ✅ No regressions in existing projects

---

## 🎓 Architectural Principles

### When Extracting Code

**DO:**
- ✅ Preserve working code exactly as-is first
- ✅ Extract complete modules (don't break dependencies)
- ✅ Test after each extraction
- ✅ Document what you extracted and from where
- ✅ Keep modules small (<400 lines ideal)

**DON'T:**
- ❌ Refactor while extracting (extract first, refactor later)
- ❌ Mix code from multiple sources without testing
- ❌ Break working functionality
- ❌ Skip documentation
- ❌ Leave TODOs or incomplete code

### Code Quality Standards

- **Module size:** <400 lines (ideal), <600 (acceptable), >800 (must refactor)
- **Cyclomatic complexity:** <10 per function
- **Function length:** <50 lines
- **Documentation:** All public APIs documented
- **Testing:** All modules have test coverage

---

## 📊 Progress Tracking

### Where to Check Progress

**For cycle-level progress:**
- Read `plans/STRATEGIC/LIBRARY_COMPONENTS.md` - detailed task list
- Read `status/LIBRARY_EXTRACTION_STATUS.md` - completion status

**For current work:**
- Read `plans/CURRENT_CYCLE.md` (Step 2) - what THIS cycle is doing
- Read `plans/IMMEDIATE_NEXT.md` (Step 3) - next immediate action

### Your Responsibility

After completing any task:
1. ✅ Update `status/LIBRARY_EXTRACTION_STATUS.md`
2. ✅ Mark tasks complete with [x]
3. ✅ Update token usage and cycle info
4. ✅ Commit changes regularly
5. ✅ When approaching 85% tokens, prepare handoff

---

## 🔗 Quick Navigation

**Reading Order:**
1. 📘 **MISSION.md** (this file) ← Read if confused
2. 📗 **CURRENT_CYCLE.md** ← Read THIS first normally
3. 📕 **IMMEDIATE_NEXT.md** ← Then read THIS
4. 📙 **LIBRARY_COMPONENTS.md** ← Reference for detailed tasks

**Status Files:**
- `status/LIBRARY_EXTRACTION_STATUS.md` - Overall progress
- `status/COMPLETED.md` - Achievement log
- `status/EE_CYCLE_STATUS.json` - Machine-readable status

---

## 🤝 Need Help?

If you're stuck:
1. ✅ Re-read CURRENT_CYCLE.md - are you on the right task?
2. ✅ Check LIBRARY_COMPONENTS.md - see detailed subtasks
3. ✅ Read source code - understand before extracting
4. ✅ Test frequently - don't extract blindly
5. ✅ Commit often - don't lose work

**If truly blocked:**
- Update status with blocker details
- Commit what you have
- Move to next independent task
- Document blocker for next instance or user review

---

**Remember:** This is a marathon, not a sprint. Quality over speed. Test everything. Document thoroughly. You've got this! 🚀
