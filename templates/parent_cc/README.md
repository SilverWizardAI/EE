# Parent CC Template

**Enterprise-grade Parent CC (Claude Code) template for managing Silver Wizard applications**

---

## Overview

This template creates a fully autonomous Parent CC instance that can:
- ✅ Create applications from templates
- ✅ Launch and manage app lifecycles
- ✅ Provide intelligent assistance via Parent CC Protocol
- ✅ Monitor app health and performance
- ✅ Coordinate communication via MM mesh
- ✅ Maintain git repository

---

## Prerequisites

### Required Libraries

This template uses centralized Silver Wizard libraries:
- **sw_core** - Core infrastructure (base application, mesh integration, etc.)
- **sw_pcc** - PCC-specific tools (registry, app creation, launcher)

Both libraries must be available on Python path before using this template.

### Installation

**Option 1: Manual .pth file (Recommended)**
```bash
echo "/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/EE/shared" > \
  /opt/homebrew/lib/python3.13/site-packages/_sw_manual.pth
```

**Option 2: pip install -e (Editable installs)**
```bash
cd /path/to/EE/shared/sw_core && pip install -e .
cd /path/to/EE/shared/sw_pcc && pip install -e .
```

**Verify Installation:**
```bash
python3 -c "import sw_core, sw_pcc; print('✓ Libraries installed')"
```

---

## Quick Start

### 1. Create New Parent CC Instance

```bash
# From EE templates directory
python setup.py \
  --name Test_App_PCC \
  --location /A_Coding/Test_App_PCC \
  --github-repo https://github.com/SilverWizardAI/Test_App_PCC
```

### 2. Start Parent CC

```bash
cd /A_Coding/Test_App_PCC
claude code
```

### 3. Create Apps

```python
# Within Parent CC instance
python tools/create_app.py \
  --name TestApp1 \
  --template pyqt_app \
  --features counter parent_cc_client \
  --pcc-folder . \
  --registry app_registry.json
```

### 4. Launch Apps

```python
python tools/launch_app.py \
  --app TestApp1 \
  --pcc-folder . \
  --registry app_registry.json
```

---

## Structure

```
parent_cc/
├── .claude/                 # Claude configuration
│   ├── CLAUDE.md           # Role & autonomy definition
│   ├── settings.json       # Permissions
│   └── settings.local.json # Tool permissions
├── apps/                    # Managed applications
│   ├── app1/
│   └── app2/
├── docs/                    # Documentation
│   ├── PARENT_CC_GUIDE.md  # How to be a Parent CC
│   └── APP_MANAGEMENT.md   # App lifecycle guide
├── tools/                   # Management tools
│   ├── registry.py         # App registry management
│   ├── create_app.py       # Create apps from templates
│   ├── launch_app.py       # Launch apps
│   └── spawn_claude.py     # Spawn Claude instances
├── logs/                    # Logs
├── app_registry.json       # App tracking
├── README.md               # This file
└── setup.py                # Setup new instances
```

---

## Features

### Application Management

**Create:** Generate apps from templates
- PyQt6 apps with MM mesh integration
- Automatic version tracking
- Parent CC protocol built-in

**Launch:** Spawn Claude instances for apps
- Background process management
- Initial prompts and guidance
- Automatic registry updates

**Monitor:** Track app health
- Periodic health checks
- Error detection
- Performance metrics

**Control:** Manage app behavior
- Dynamic configuration
- Log level adjustment
- Graceful shutdown

### Parent CC Protocol

**Provide intelligent assistance:**
- HELP requests - Guidance for apps
- PERMISSION requests - Approve/deny risky operations
- ERROR_RECOVERY - Recovery strategies
- DATA_PROCESSING - Complex transformations
- ANALYSIS - Data insights
- DECISION - Choose between options

**See:** `docs/PARENT_CC_GUIDE.md` for complete protocol documentation

### MM Mesh Integration

**Communicate via mesh:**
- Receive assistance requests from apps
- Send control commands to apps
- Coordinate peer-to-peer app communication
- Monitor mesh connectivity

### Git Repository

**Full git control:**
- Initialize repository
- Create branches
- Commit changes
- Push to remote
- Manage remotes

---

## Tools

**Architecture Note:** All tools are lightweight wrappers that import from centralized libraries (sw_core and sw_pcc). This ensures single source of truth and eliminates code duplication across Parent CC instances.

### registry.py

Manage app registry:

```bash
# List all apps
python tools/registry.py --list

# Check app health
python tools/registry.py --check-health TestApp1

# Show statistics
python tools/registry.py --stats
```

### create_app.py

Create apps from templates:

```bash
python tools/create_app.py \
  --name MyApp \
  --template pyqt_app \
  --features counter \
  --pcc-folder . \
  --registry app_registry.json
```

### launch_app.py

Launch and stop apps:

```bash
# Launch
python tools/launch_app.py \
  --app MyApp \
  --pcc-folder . \
  --action launch

# Stop
python tools/launch_app.py \
  --app MyApp \
  --pcc-folder . \
  --action stop
```

---

## Parent CC Responsibilities

### 1. Create & Manage Apps
- Use templates (don't build from scratch)
- Keep registry updated
- Monitor all apps

### 2. Provide Intelligent Assistance
- Answer help requests with context
- Approve/deny risky operations with safeguards
- Provide error recovery strategies
- Make complex decisions

### 3. Monitor Health
- Check every 60 seconds
- Investigate issues
- Proactive intervention

### 4. Maintain Repository
- Regular commits
- Clear messages
- Push to remote

---

## Best Practices

### DO
- ✅ Create apps from templates
- ✅ Update registry after changes
- ✅ Respond quickly to assistance requests (<30s)
- ✅ Explain reasoning in responses
- ✅ Commit changes regularly
- ✅ Monitor apps proactively

### DON'T
- ❌ Create apps without templates
- ❌ Ignore health issues
- ❌ Give vague guidance
- ❌ Approve risky ops without safeguards
- ❌ Modify apps directly (guide them instead)

---

## Documentation

**In this template:**
- `docs/PARENT_CC_GUIDE.md` - How to be a Parent CC
- `docs/APP_MANAGEMENT.md` - App lifecycle management

**In EE project:**
- `/A_Coding/EE/docs/PARENT_CC_PROTOCOL.md` - Protocol specification
- `/A_Coding/EE/docs/PARENT_CC_IMPLEMENTATION.md` - Implementation guide

---

## Example Workflow

```bash
# 1. Parent CC creates TestApp1
python tools/create_app.py --name TestApp1 --template pyqt_app --features counter

# 2. Parent CC launches TestApp1
python tools/launch_app.py --app TestApp1 --action launch

# 3. TestApp1 runs and requests help when count > 100

# 4. Parent CC receives assistance request via MM mesh

# 5. Parent CC analyzes and responds with guidance

# 6. TestApp1 follows guidance

# 7. Parent CC monitors TestApp1 health every 60s

# 8. When done, Parent CC stops TestApp1
python tools/launch_app.py --app TestApp1 --action stop
```

---

## Requirements

- Python 3.13+
- Claude Code CLI
- MM mesh proxy running (port 6001)
- PyQt6 (for created apps)

---

## Template Version

**Version:** 1.0.0
**Created:** 2026-02-05
**Organization:** Silver Wizard Software

---

## Related Projects

- **EE** - Enterprise Edition (templates and infrastructure)
- **MM** - MCP Mesh (communication backbone)
- **PyQt App Template** - Application template

---

**Ready to manage apps!** 🚀
