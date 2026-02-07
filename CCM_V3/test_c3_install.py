#!/usr/bin/env python3
"""
Test C3 installation in a temporary workspace.
"""

import json
import logging
import shutil
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Import TCCSetup
import sys
sys.path.insert(0, str(Path(__file__).parent))
from tcc_setup import TCCSetup

def test_c3_installation():
    """Test C3 installation in a temp directory."""

    # Create temp workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "test_workspace"
        workspace.mkdir()

        logger.info(f"Created test workspace: {workspace}")

        # Create a fake socket path (won't actually use it)
        socket_path = Path(tmpdir) / "test.sock"

        # Test 1: Fresh install
        logger.info("\n=== Test 1: Fresh Install ===")
        result = TCCSetup.instrument_project(
            project_path=workspace,
            mcp_socket_path=socket_path,
            plan_file="Plan_2.md"
        )

        # Verify C3 was installed
        c3_dir = workspace / ".C3"
        assert c3_dir.exists(), "C3 directory not created"
        assert (c3_dir / "README.md").exists(), "C3 README.md not created"
        assert (c3_dir / "send_to_monitor.py").exists(), "send_to_monitor.py not copied"
        assert (c3_dir / "ee_manager.py").exists(), "ee_manager.py not copied"
        assert (c3_dir / "token_checker.py").exists(), "token_checker.py not copied"
        assert (c3_dir / "terminate_cycle.py").exists(), "terminate_cycle.py not copied"

        # Verify README has correct version
        readme = (c3_dir / "README.md").read_text()
        assert "**Version:** 1.0.0" in readme, "Version not in README"
        assert "Claude Code Controller (C3)" in readme, "C3 title not in README"

        # Verify cycle_state.json was created
        state_file = workspace / "cycle_state.json"
        assert state_file.exists(), "cycle_state.json not created"
        state = json.loads(state_file.read_text())
        assert state["cycle"] == 1, "cycle should be 1"
        assert state["next_step"] == 1, "next_step should be 1"
        assert "history" in state, "history should exist"

        logger.info("✅ Fresh install: PASSED")
        logger.info(f"   C3 action: {result['c3_action']}")
        logger.info(f"   C3 version: {result['c3_version']}")

        # Test 2: Re-run instrumentation (should skip)
        logger.info("\n=== Test 2: Re-instrument (should skip) ===")
        result2 = TCCSetup.instrument_project(
            project_path=workspace,
            mcp_socket_path=socket_path,
            plan_file="Plan_2.md"
        )

        assert result2['c3_action'] == "skip", f"Should skip, got: {result2['c3_action']}"
        logger.info("✅ Skip existing: PASSED")

        # Test 3: Upgrade (simulate new version)
        logger.info("\n=== Test 3: Upgrade to v1.0.1 ===")
        result3 = TCCSetup.instrument_project(
            project_path=workspace,
            mcp_socket_path=socket_path,
            plan_file="Plan_2.md",
            c3_version="1.0.1"
        )

        assert result3['c3_action'] == "upgrade", f"Should upgrade, got: {result3['c3_action']}"

        # Verify backup was created
        backup_dir = workspace / ".C3.backup"
        assert backup_dir.exists(), "Backup directory not created"
        assert (backup_dir / "README.md").exists(), "Backup README not found"

        # Verify new version
        readme_new = (c3_dir / "README.md").read_text()
        assert "**Version:** 1.0.1" in readme_new, "Version not updated in README"

        logger.info("✅ Upgrade: PASSED")
        logger.info(f"   Backup created: {backup_dir}")
        logger.info(f"   New version: 1.0.1")

        # Summary
        logger.info("\n" + "="*60)
        logger.info("ALL TESTS PASSED ✅")
        logger.info("="*60)
        logger.info(f"\nC3 structure created in test workspace:")
        logger.info(f"  .C3/")
        logger.info(f"    ├── README.md (v1.0.1)")
        logger.info(f"    ├── send_to_monitor.py")
        logger.info(f"    ├── ee_manager.py")
        logger.info(f"    ├── token_checker.py")
        logger.info(f"    └── terminate_cycle.py")
        logger.info(f"  .C3.backup/ (from v1.0.0)")
        logger.info(f"  cycle_state.json")
        logger.info(f"  .claude/")
        logger.info(f"    ├── CLAUDE.md")
        logger.info(f"    └── settings.json")

if __name__ == "__main__":
    try:
        test_c3_installation()
    except AssertionError as e:
        logger.error(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        sys.exit(1)
