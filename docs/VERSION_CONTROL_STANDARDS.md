# 🔒 Version Control Standards - Silver Wizard Software

**Established:** 2026-02-07
**Scope:** All EE projects and sister projects
**Enforcement:** MANDATORY for all Claude Code instances

---

## 🚨 CRITICAL RULES - NO EXCEPTIONS

### 1. NEVER Make Uncommitted Major Changes

**RULE:** Any change that affects functionality, UI, or architecture MUST be committed before moving to next task.

**Definition of "Major Change":**
- UI modifications (layout, components, behavior)
- API changes (function signatures, endpoints)
- Architecture changes (new patterns, refactoring)
- Configuration changes (settings, defaults)
- Dependency changes (new libraries, version updates)
- File moves/renames/deletions

**Protocol:**
```bash
# After EVERY major change:
git add <files>
git commit -m "type: Brief description

Detailed explanation of what changed and why.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git status  # Verify clean
```

**If you crash or hit token limit without committing → USER LOSES WORK!**

---

### 2. NEVER Work Outside Your Scope

**RULE:** EE instances have FULL write access to `/A_Coding/EE/**` ONLY.

**Sister Projects are READ-ONLY:**
- CMC/CCM - Content Management & Control
- MM - MCP Mesh
- MacR - Mac Retriever
- PIW - Python Install Wizard
- All other `/A_Coding/*` projects

**Exception Process:**
1. Identify need to modify sister project
2. **STOP** and ask user for permission
3. Document reason in request
4. Only proceed after explicit approval
5. Create separate commit in sister project's git repo
6. Update sister project's documentation

**DO NOT:**
- Create files in sister project directories
- Modify sister project code "temporarily"
- Copy files from sister projects without documentation
- Create duplicate directory structures

---

### 3. ALWAYS Document Architecture Changes

**RULE:** Any architectural change requires documentation BEFORE implementation.

**Required Documentation:**
1. **Architecture Decision Record (ADR)** in `docs/adr/`
2. **Update COMPLETED.md** with change summary
3. **Update README.md** if user-facing
4. **Update code comments** for complex logic

**ADR Template:**
```markdown
# ADR-NNNN: Title

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue we're facing?

## Decision
What did we decide to do?

## Consequences
What becomes easier/harder after this change?

## Alternatives Considered
What other options did we evaluate?
```

---

### 4. NEVER Create Duplicate Directories

**RULE:** Each logical component has ONE canonical location.

**Problem Pattern:**
```
CCM_V3/              ← Correct
CCM_V3/CCM_V3/       ← WRONG! Duplicate!
```

**Prevention:**
- Use absolute paths in all scripts
- Verify directory structure before creating files
- Check git status regularly
- Never nest project directories

**If you create a duplicate → STOP and clean it up immediately**

---

### 5. ALWAYS Update Status After Each Task

**RULE:** Update `status/COMPLETED.md` after EVERY completed task (not just at end of session).

**Required Format:**
```markdown
## Task Name - STATUS ✅/⚠️/❌

**Date:** YYYY-MM-DD
**Session:** Brief session identifier
**Status:** ✅ Complete | ⚠️ Partial | ❌ Failed

### Summary
1-2 sentence overview

### Deliverables
- ✅ File/feature created
- ✅ Tests passed
- ⚠️ Known issues

### Git Commits
- `abc1234` - Commit message
```

**Update frequency:**
- ✅ After completing each major task
- ✅ Before handoff to next instance
- ✅ After fixing critical bugs
- ✅ When changing direction/approach

---

## 📋 GIT COMMIT STANDARDS

### Commit Message Format

```
type: Brief summary (50 chars max)

Detailed explanation of what changed and why.
Include:
- What was the problem?
- What is the solution?
- What are the consequences?
- Any breaking changes?

Related: #issue-number (if applicable)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Commit Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation only
- **refactor:** Code restructuring (no behavior change)
- **test:** Adding/updating tests
- **chore:** Maintenance (dependencies, build)
- **perf:** Performance improvement
- **style:** Formatting only (no logic change)

### Commit Frequency

**MINIMUM:**
- After each completed task
- Before token handoff
- After fixing bugs
- When switching tasks

**OPTIMAL:**
- After each logical unit of work
- When tests pass
- Before risky operations
- Every 30 minutes of work

---

## 🏗️ ARCHITECTURE CHANGE PROTOCOL

### Before Making Architecture Changes

1. **Document Current State**
   - Capture current architecture in `docs/`
   - Take snapshots of critical files
   - Document current behavior

2. **Design New Architecture**
   - Create ADR (Architecture Decision Record)
   - Sketch diagrams if complex
   - List all affected files
   - Identify breaking changes

3. **Get Approval** (if significant)
   - Ask user via AskUserQuestion
   - Present alternatives
   - Explain trade-offs
   - Get explicit confirmation

4. **Implement Incrementally**
   - Make smallest possible changes
   - Commit after each step
   - Test after each commit
   - Document as you go

5. **Update Documentation**
   - Update all affected docs
   - Update COMPLETED.md
   - Create migration guide if needed
   - Update README

### After Making Architecture Changes

1. **Verify Everything Works**
   - Run all tests
   - Test manually if needed
   - Check for regressions
   - Verify documentation accuracy

2. **Final Commit**
   - Comprehensive commit message
   - Reference ADR number
   - List all breaking changes
   - Update version if applicable

3. **Update Status**
   - Mark task complete in COMPLETED.md
   - Document known issues
   - List follow-up tasks

---

## 🚫 ANTI-PATTERNS - NEVER DO THIS

### ❌ The "Temporary" Hack
```python
# TODO: Fix this properly later
# WRONG! Either fix it now or don't change it
quick_hack = True
```

**Instead:** Either implement properly or create ticket for later.

---

### ❌ The Uncommitted Experiment
```bash
# Made changes, testing...
# [Session crashes]
# [User loses all work]
```

**Instead:** Commit working code, then create experimental branch.

---

### ❌ The Scope Creep
```bash
# Working on EE...
# "Oh, I'll just quickly fix this in CMC..."
# [Modifies sister project]
# [Creates mess across projects]
```

**Instead:** Note the issue, ask permission, work in correct scope.

---

### ❌ The Duplicate Directory
```bash
mkdir CCM_V3/CCM_V3  # WRONG!
mkdir CCM_V3_backup  # WRONG!
mkdir CCM_V3_new     # WRONG!
```

**Instead:** Use git branches for versions, not directory duplication.

---

### ❌ The Orphan File
```bash
# Creates file in random location
touch /tmp/important_config.json
# [Never committed, lost forever]
```

**Instead:** All project files belong in project directory, committed to git.

---

### ❌ The Undocumented Rewrite
```python
# Completely rewrites major component
# No commit, no documentation, no explanation
# [Crashes before explaining]
```

**Instead:**
1. Document current state
2. Create ADR
3. Implement incrementally
4. Commit each step
5. Update docs

---

## 📊 VERIFICATION CHECKLIST

Before ending session or hitting token limit, verify:

- [ ] All changes committed to git
- [ ] `git status` is clean (or only has intentional untracked files)
- [ ] COMPLETED.md updated with session work
- [ ] All documentation updated
- [ ] No duplicate directories created
- [ ] No sister projects modified without permission
- [ ] All ADRs created for architecture changes
- [ ] Tests still pass
- [ ] No uncommitted "temporary" changes

**If ANY item is unchecked → DO NOT END SESSION until fixed!**

---

## 🔄 HANDOFF PROTOCOL

When approaching token limit (>85%):

1. **Commit Everything**
   ```bash
   git add -A
   git commit -m "chore: Session handoff preparation"
   git push
   ```

2. **Update Status**
   - COMPLETED.md with session summary
   - plans/NEXT_STEPS.md with clear instructions
   - Any open issues in plans/ISSUES.md

3. **Verify Clean State**
   ```bash
   git status  # Should be clean
   find . -name "*.pyc" -delete  # Clean temp files
   ```

4. **Create Handoff**
   ```bash
   python3 tools/ee_manager.py handoff \
     --tokens <current> \
     --next "Clear description of next task"
   ```

5. **Final Verification**
   - All work committed
   - Documentation complete
   - Next instance can continue seamlessly

---

## 💡 BEST PRACTICES

### 1. Commit Early, Commit Often
- Small commits > large commits
- Easier to debug issues
- Easier to revert if needed
- Clearer history

### 2. Make Atomic Commits
- Each commit = one logical change
- Don't mix refactoring with features
- Don't mix fixes with new features

### 3. Write Meaningful Messages
- Future you will thank you
- Other developers will understand
- Makes debugging easier
- Enables automation

### 4. Test Before Committing
- Broken commits block other work
- Hard to bisect issues
- Frustrates users

### 5. Document as You Code
- Don't defer documentation
- Context is fresh in your mind
- Easier than reconstructing later

---

## 🎓 LEARNING FROM MISTAKES

### Case Study: CCM V3 Duplicate Directory Incident

**Date:** 2026-02-07

**What Happened:**
- Previous instance created `CCM_V3/CCM_V3/` duplicate directory
- Modified CCM V3 (sister project) without permission
- Created conflicting versions of Plan_3.md
- Crashed before cleanup
- User lost context on what changed

**What Went Wrong:**
1. Worked outside EE scope (in CCM_V3 sister project)
2. Created duplicate directory structure
3. Made uncommitted major changes
4. No documentation of changes
5. Crashed before cleanup

**How We Fixed It:**
1. Investigated duplicate directory
2. Preserved both Plan_3.md versions
3. Removed duplicate directory
4. Created version control standards (this document)
5. Committed cleanup with documentation

**Lessons Learned:**
1. ✅ ALWAYS check scope before creating files
2. ✅ NEVER create duplicate directories
3. ✅ COMMIT after each major change
4. ✅ DOCUMENT architectural decisions
5. ✅ VERIFY clean state before ending

**Prevention:**
- Created this standards document
- Added verification checklist
- Documented anti-patterns
- Established clear protocols

---

## 🔧 ENFORCEMENT

### Self-Enforcement
- Read this document at session start
- Follow checklist before session end
- Review git status frequently
- Document as you go

### Automated Checks (Future)
- Pre-commit hooks to verify standards
- Automated documentation checks
- Scope validation
- Duplicate directory detection

### User Oversight
- User reviews commits
- User can reject non-compliant work
- User enforces scope boundaries

---

## 📚 RELATED DOCUMENTS

- `docs/ARCHITECTURE_ANALYSIS.md` - Current architecture
- `docs/LIBRARY_EXTRACTION_COMPLETE.md` - Example of good documentation
- `status/COMPLETED.md` - Session work log
- `plans/NEXT_STEPS.md` - Immediate next actions
- `.claude/CLAUDE.md` - Project scope and permissions

---

## ✅ SUMMARY - GOLDEN RULES

1. **COMMIT EARLY, COMMIT OFTEN** - Never leave uncommitted major changes
2. **STAY IN SCOPE** - EE writes to `/A_Coding/EE/**` only
3. **DOCUMENT EVERYTHING** - Future you/others will thank you
4. **NO DUPLICATES** - One canonical location per component
5. **UPDATE STATUS** - COMPLETED.md after every task
6. **TEST BEFORE COMMIT** - Broken commits block progress
7. **VERIFY BEFORE HANDOFF** - Clean state for next instance

**When in doubt, ask the user. It's always better to ask than to create a mess.**

---

*This document is version-controlled and will evolve. Last updated: 2026-02-07*
