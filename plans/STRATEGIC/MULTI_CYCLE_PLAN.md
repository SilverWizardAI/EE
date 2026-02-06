# 🔄 MULTI-CYCLE PLAN (Strategic Roadmap)

**Project:** EE Shared Library Extraction
**Expected Duration:** 3-10 cycles
**Cycle Length:** ~170K tokens per cycle (~85% of 200K limit)

---

## 🎯 Purpose of This Document

This document provides the **strategic roadmap** across multiple EE instance cycles. Each cycle hands off to the next when approaching token limit (85% = 170K tokens).

**When to read this:**
- 📘 Step 1 (MISSION.md) if confused about overall goal
- 📗 Step 2 (CURRENT_CYCLE.md) to understand THIS cycle ← **START HERE**
- 📕 Step 3 (IMMEDIATE_NEXT.md) to know next action
- 📙 This file for long-term roadmap view

---

## 📊 Cycle Breakdown

### Cycle 1: Foundation Components (No Dependencies)

**Goal:** Extract standalone components that have no internal dependencies

**Tasks:**
1. ✅ Set up `EE/shared/sw_core/` directory structure
2. ✅ Set up `EE/shared/sw_pcc/` directory structure
3. Extract `mesh_integration.py` from Test_App_PCC template
4. Extract `settings_manager.py` from Test_App_PCC template
5. Extract `spawn_claude.py` from Test_App_PCC/tools
6. Extract `version_info/` from PIW
7. Test each component individually
8. Create basic `__init__.py` files

**Success Criteria:**
- [ ] All 4 components extracted
- [ ] All imports work
- [ ] Basic tests pass
- [ ] No errors when importing modules

**Estimated Tokens:** 50K-80K (light cycle, mostly file operations)

**Handoff Prompt for Cycle 2:**
```
Continue library extraction. Cycle 1 completed foundation components.

Next: Extract base_application.py and parent_cc_protocol.py (depend on Cycle 1 components).

Read plans/CURRENT_CYCLE.md for status.
```

---

### Cycle 2: Core Application Framework

**Goal:** Extract main application class and Parent CC protocol

**Dependencies:** Requires Cycle 1 components

**Tasks:**
1. Extract `base_application.py` from Test_App_PCC template
2. Test BaseApplication with mesh integration
3. Test BaseApplication with settings manager
4. Extract `parent_cc_protocol.py` from Test_App_PCC template
5. Test ParentCCProtocol with spawn_claude
6. Test full app lifecycle (spawn → run → shutdown)
7. Extract `module_monitor.py` (optional, lower priority)

**Success Criteria:**
- [ ] BaseApplication works standalone
- [ ] Can create minimal app using BaseApplication
- [ ] App connects to MM mesh
- [ ] App can spawn workers via ParentCCProtocol
- [ ] Clean shutdown works

**Estimated Tokens:** 80K-120K (complex testing and integration)

**Handoff Prompt for Cycle 3:**
```
Continue library extraction. Cycle 2 completed sw_core library.

Next: Extract sw_pcc tools (create_app.py, registry.py, launcher.py).

Read plans/CURRENT_CYCLE.md for status.
```

---

### Cycle 3: Parent CC Tools

**Goal:** Extract app creation and management tools

**Dependencies:** Requires sw_core library from Cycle 2

**Tasks:**
1. Extract `registry.py` from Test_App_PCC/tools
2. Test app registration and discovery
3. Extract `create_app.py` from Test_App_PCC/tools
4. Test app creation from template
5. Extract `launcher.py` from Test_App_PCC/tools (launch_app.py)
6. Test app launching
7. Test end-to-end: create → register → launch

**Success Criteria:**
- [ ] Can create new app from command line
- [ ] Registry tracks apps correctly
- [ ] Can launch apps by name
- [ ] All CLI commands work

**Estimated Tokens:** 70K-100K (tool extraction and testing)

**Handoff Prompt for Cycle 4:**
```
Continue library extraction. Cycle 3 completed sw_pcc tools.

Next: Create packaging configuration (pyproject.toml, README files).

Read plans/CURRENT_CYCLE.md for status.
```

---

### Cycle 4: Packaging & Documentation

**Goal:** Make libraries installable packages with documentation

**Dependencies:** Requires both sw_core and sw_pcc libraries

**Tasks:**
1. Create `pyproject.toml` for sw_core
2. Create `pyproject.toml` for sw_pcc
3. Create `README.md` for sw_core
4. Create `README.md` for sw_pcc
5. Test installation: `pip install -e shared/sw_core`
6. Test installation: `pip install -e shared/sw_pcc`
7. Create API documentation
8. Create usage examples

**Success Criteria:**
- [ ] Both packages install successfully
- [ ] All imports work after installation
- [ ] CLI commands available in PATH
- [ ] Documentation complete and accurate

**Estimated Tokens:** 40K-60K (mostly documentation)

**Handoff Prompt for Cycle 5:**
```
Continue library extraction. Cycle 4 completed packaging.

Next: Update PyQt template to use shared libraries.

Read plans/CURRENT_CYCLE.md for status.
```

---

### Cycle 5: Template Integration

**Goal:** Update pyqt_app template to use shared libraries

**Dependencies:** Requires installable packages from Cycle 4

**Tasks:**
1. Update `templates/pyqt_app/requirements.txt` to include sw_core
2. Update `templates/pyqt_app/base_application.py` → remove (use sw_core version)
3. Update `templates/pyqt_app/main.py` imports
4. Update all template files to import from sw_core
5. Update template documentation
6. Create migration guide for existing apps
7. Test template generation with new structure

**Success Criteria:**
- [ ] Template generates working apps
- [ ] Apps use sw_core library
- [ ] No duplicate code in template
- [ ] All template features preserved

**Estimated Tokens:** 60K-90K (template refactoring and testing)

**Handoff Prompt for Cycle 6:**
```
Continue library extraction. Cycle 5 completed template integration.

Next: End-to-end validation - create and test new app.

Read plans/CURRENT_CYCLE.md for status.
```

---

### Cycle 6: Validation & Testing

**Goal:** Prove everything works end-to-end

**Dependencies:** Requires updated template from Cycle 5

**Tasks:**
1. Create test app from updated template
2. Test app startup and MM mesh connection
3. Test app spawning worker
4. Test app settings management
5. Test app clean shutdown
6. Run for extended period (stability test)
7. Check for memory leaks
8. Verify all logs clean (no errors)

**Success Criteria:**
- [ ] Test app runs successfully
- [ ] All features work correctly
- [ ] No errors in logs
- [ ] Clean startup/shutdown
- [ ] Stable for 1+ hours
- [ ] No memory leaks

**Estimated Tokens:** 50K-80K (thorough testing)

**Handoff Prompt for Cycle 7 (if needed):**
```
Continue library extraction. Cycle 6 completed validation.

Next: Fix any issues found during testing OR mark project complete.

Read plans/CURRENT_CYCLE.md for status.
```

---

### Cycle 7+: Refinement & Optimization (If Needed)

**Goal:** Address any issues, optimize, improve documentation

**Dependencies:** Requires all previous cycles

**Tasks:**
- Fix bugs discovered during validation
- Optimize performance bottlenecks
- Improve documentation based on usage
- Add missing features
- Refactor large modules (>600 lines)
- Add comprehensive test coverage
- Create troubleshooting guide

**Success Criteria:**
- [ ] All known issues resolved
- [ ] Documentation comprehensive
- [ ] Code quality meets standards
- [ ] Ready for production use

---

## 🚦 State Transitions

```
START
  ↓
Cycle 1: Foundation Components (standalone)
  ↓
Cycle 2: Core Application (uses Cycle 1)
  ↓
Cycle 3: PCC Tools (uses Cycle 2)
  ↓
Cycle 4: Packaging & Docs
  ↓
Cycle 5: Template Integration (uses Cycle 4)
  ↓
Cycle 6: End-to-End Validation (uses Cycle 5)
  ↓
Cycle 7+: Refinement (if needed)
  ↓
COMPLETE ✅
```

---

## 📈 Progress Tracking

### How to Know Which Cycle You're In

**Check `plans/CURRENT_CYCLE.md`** - it will explicitly state:
```markdown
## Current Cycle: 3

You are working on: PCC Tools Extraction
Previous cycle completed: Core Application Framework
Next cycle will work on: Packaging & Documentation
```

### How to Know What to Do Next

**Check `plans/IMMEDIATE_NEXT.md`** - it will explicitly state:
```markdown
## Step 3: Next Immediate Action

Do this next: Extract registry.py from Test_App_PCC/tools

Source: /A_Coding/Test_App_PCC/tools/registry.py
Destination: /A_Coding/EE/shared/sw_pcc/registry.py
```

---

## ⚡ Handoff Protocol

### When You Reach 85% Tokens (~170K)

**DO NOT PANIC.** This is expected and normal.

**Execute handoff:**

1. **Commit current work:**
   ```bash
   cd /A_Coding/EE
   git add .
   git commit -m "chore: Cycle N handoff - [brief status]"
   git push
   ```

2. **Update status files:**
   - Mark completed tasks in `status/LIBRARY_EXTRACTION_STATUS.md`
   - Update `plans/CURRENT_CYCLE.md` with progress
   - Update `plans/IMMEDIATE_NEXT.md` with next action

3. **Commit status updates:**
   ```bash
   git add status/ plans/
   git commit -m "chore: Update status for Cycle N handoff"
   git push
   ```

4. **Signal handoff** (if automated system exists):
   ```bash
   python tools/ee_manager.py handoff \
     --tokens <current_token_count> \
     --next "Brief description of what next instance should do"
   ```

5. **Your work is done!** The next instance will:
   - Read CURRENT_CYCLE.md (Step 2)
   - Read IMMEDIATE_NEXT.md (Step 3)
   - Continue exactly where you left off

---

## 🎯 Success Metrics (Overall Project)

### Code Quality
- ✅ All modules < 600 lines (ideally < 400)
- ✅ All public APIs documented
- ✅ No hardcoded paths or credentials
- ✅ No circular dependencies
- ✅ All components tested

### Functionality
- ✅ 100% feature parity with template
- ✅ All existing functionality preserved
- ✅ No regressions in existing projects
- ✅ Clean startup/shutdown
- ✅ Stable for extended operation

### Integration
- ✅ Libraries install correctly
- ✅ Template generates working apps
- ✅ New apps work out of the box
- ✅ Migration path documented for existing apps

### Documentation
- ✅ README files complete
- ✅ API documentation comprehensive
- ✅ Usage examples provided
- ✅ Troubleshooting guide available
- ✅ Architecture documented

---

## 🔗 Quick Reference

**Strategic Planning (Read if confused):**
- `plans/STRATEGIC/MISSION.md` - The big picture (Step 1)
- `plans/STRATEGIC/LIBRARY_COMPONENTS.md` - Detailed component list
- `plans/STRATEGIC/MULTI_CYCLE_PLAN.md` - This file

**Tactical Execution (Read first normally):**
- `plans/CURRENT_CYCLE.md` - What THIS cycle is doing (Step 2)
- `plans/IMMEDIATE_NEXT.md` - Next immediate action (Step 3)

**Status Tracking:**
- `status/LIBRARY_EXTRACTION_STATUS.md` - Completion checkboxes
- `status/COMPLETED.md` - Achievement log
- `status/EE_CYCLE_STATUS.json` - Machine-readable status

---

## 💡 Pro Tips

**For Efficient Cycles:**
1. ✅ Read CURRENT_CYCLE.md FIRST (Step 2)
2. ✅ Read IMMEDIATE_NEXT.md SECOND (Step 3)
3. ✅ Only read MISSION.md (Step 1) if confused
4. ✅ Commit after each component extraction
5. ✅ Test immediately after extraction
6. ✅ Update status files frequently
7. ✅ When approaching 85% tokens, prepare handoff

**For Quality Results:**
1. ✅ Preserve working code exactly first
2. ✅ Test before moving to next component
3. ✅ Document what you extracted and why
4. ✅ Keep modules small (<400 lines ideal)
5. ✅ No TODOs or incomplete code
6. ✅ Clean commit messages

**For Smooth Handoffs:**
1. ✅ Commit all changes before handoff
2. ✅ Update CURRENT_CYCLE.md with progress
3. ✅ Update IMMEDIATE_NEXT.md with next action
4. ✅ Update status checkboxes
5. ✅ Push to remote
6. ✅ Clear handoff message for next instance

---

**Remember:** This is a marathon, not a sprint. Each cycle builds on the previous. Quality and thoroughness over speed. You've got this! 🚀
