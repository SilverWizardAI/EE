# ✅ Version Control Checklist - Quick Reference

**Print this and keep visible during all sessions!**

---

## 🚨 BEFORE Starting Any Task

- [ ] Read `docs/VERSION_CONTROL_STANDARDS.md`
- [ ] Check current git status: `git status`
- [ ] Verify working in correct scope: `pwd` (should be in `/A_Coding/EE/`)
- [ ] Check token budget: `<current tokens> / 200000`

---

## 📝 DURING Every Task

- [ ] Commit after each logical unit of work
- [ ] Update documentation as you code
- [ ] Test before committing
- [ ] Verify no duplicate directories created
- [ ] Stay within EE scope (no sister project modifications)

---

## ✅ AFTER Completing Each Task

- [ ] All changes committed: `git status` is clean
- [ ] COMPLETED.md updated with task summary
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (README, ADRs, etc.)
- [ ] No uncommitted "temporary" code
- [ ] No duplicate directories created
- [ ] Send status to monitor: `python3 tools/send_to_monitor.py "Task complete"`

---

## 🔄 BEFORE Handoff/Session End

- [ ] **CRITICAL:** All changes committed: `git add -A && git commit`
- [ ] Git status clean: `git status`
- [ ] COMPLETED.md updated with full session summary
- [ ] plans/NEXT_STEPS.md updated with clear instructions
- [ ] Any issues documented in plans/ISSUES.md
- [ ] All documentation up to date
- [ ] No sister projects modified without permission
- [ ] No duplicate directories exist
- [ ] Run handoff protocol: `python3 tools/ee_manager.py handoff`

---

## 🚫 NEVER DO

- ❌ Make major changes without committing
- ❌ Create duplicate directories (e.g., `CCM_V3/CCM_V3/`)
- ❌ Modify sister projects without permission
- ❌ Leave uncommitted "temporary" code
- ❌ Skip documentation updates
- ❌ End session with uncommitted work

---

## 💾 COMMIT TEMPLATE

```bash
git add <files>
git commit -m "type: Brief summary (50 chars max)

Detailed explanation:
- What changed?
- Why did it change?
- Any breaking changes?

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Types:** feat, fix, docs, refactor, test, chore, perf, style

---

## 🆘 IF YOU CRASH

**Before crashing (if you see token limit approaching):**
1. IMMEDIATELY commit all work: `git add -A && git commit -m "chore: Emergency pre-crash commit"`
2. Update COMPLETED.md with current state
3. Run handoff protocol

**The user loses ALL uncommitted work if you crash!**

---

## 📊 VERIFICATION COMMANDS

```bash
# Check git status
git status

# Verify in EE directory
pwd  # Should be: /Users/stevedeighton/.../A_Coding/EE

# Find duplicate directories
find . -type d -name "$(basename $(pwd))" 2>/dev/null

# Check for uncommitted changes
git diff --stat

# Check for untracked files
git ls-files --others --exclude-standard

# Verify no sister projects modified
git status /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/
```

---

## 🎯 REMEMBER

**"Commit early, commit often. Stay in scope. Document everything."**

If you're unsure about anything:
1. Check the full standards: `docs/VERSION_CONTROL_STANDARDS.md`
2. Ask the user
3. Err on the side of over-communication

---

*Last updated: 2026-02-07*
