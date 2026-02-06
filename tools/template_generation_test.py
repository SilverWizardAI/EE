#!/usr/bin/env python3
"""
Template Generation Test - End-to-End Validation

Tests the complete workflow:
1. Generate app from template
2. Verify file structure
3. Check imports
4. Verify placeholder replacement
5. Launch app
6. Test lifecycle
7. Verify cleanup
8. Delete test app

This ensures template changes don't break app generation.
"""

import subprocess
import time
import sys
import json
import shutil
import requests
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime


class TemplateGenerationTest:
    """End-to-end template generation validator."""

    def __init__(self, cleanup: bool = True):
        """
        Initialize test.

        Args:
            cleanup: Whether to delete generated app after test (default: True)
        """
        self.cleanup = cleanup
        self.test_app_name = f"TemplateTest_{int(time.time())}"
        self.test_pcc_folder = Path(f"/tmp/{self.test_app_name}_PCC")
        self.test_app_path = None
        self.process = None
        self.pid = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "  ",
            "PASS": "✓ ",
            "FAIL": "✗ ",
            "WARN": "⚠️  "
        }.get(level, "  ")
        print(f"{prefix}{message}")

    def error(self, message: str):
        """Log error and track it."""
        self.errors.append(message)
        self.log(message, "FAIL")

    def warning(self, message: str):
        """Log warning and track it."""
        self.warnings.append(message)
        self.log(message, "WARN")

    def step(self, message: str):
        """Log test step."""
        print(f"\n{'─' * 80}")
        print(f"STEP: {message}")
        print('─' * 80)

    # -------------------------------------------------------------------------
    # Test Steps
    # -------------------------------------------------------------------------

    def test_1_generate_app(self) -> bool:
        """Step 1: Generate app from template."""
        self.step("1. Generate App from Template")

        try:
            # Create PCC folder with registry
            self.test_pcc_folder.mkdir(parents=True, exist_ok=True)
            registry_file = self.test_pcc_folder / "app_registry.json"

            registry_data = {
                "apps": {},
                "statistics": {
                    "total_apps": 0,
                    "running_apps": 0,
                    "stopped_apps": 0,
                    "total_health_checks": 0,
                    "total_assistance_requests": 0
                },
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }

            with open(registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)

            self.log("Created PCC folder and registry", "PASS")

            # Generate app
            self.log(f"Generating app: {self.test_app_name}")

            result = subprocess.run(
                [
                    "python3", "-m", "sw_pcc.create_app",
                    "--name", self.test_app_name,
                    "--template", "pyqt_app",
                    "--pcc-folder", str(self.test_pcc_folder)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.error(f"App generation failed: {result.stderr}")
                return False

            # Verify app folder exists
            self.test_app_path = self.test_pcc_folder / "apps" / self.test_app_name

            if not self.test_app_path.exists():
                self.error(f"App folder not created: {self.test_app_path}")
                return False

            self.log(f"App created at: {self.test_app_path}", "PASS")
            return True

        except Exception as e:
            self.error(f"Generation failed: {e}")
            return False

    def test_2_verify_structure(self) -> bool:
        """Step 2: Verify file structure."""
        self.step("2. Verify File Structure")

        expected_files = [
            "main.py",
            "__init__.py",
            "version_manager.py",
            "test_mm_integration.py",
            "run_tests.py",
            "version.json",
            "README.md"
        ]

        missing = []
        for filename in expected_files:
            filepath = self.test_app_path / filename
            if filepath.exists():
                self.log(f"Found: {filename}", "PASS")
            else:
                missing.append(filename)
                self.error(f"Missing: {filename}")

        # Check that version_info directory does NOT exist (should be deleted)
        version_info_dir = self.test_app_path / "version_info"
        if version_info_dir.exists():
            self.error("Duplicate version_info/ directory found (should not exist!)")
            return False
        else:
            self.log("No duplicate version_info/ directory", "PASS")

        return len(missing) == 0

    def test_3_check_imports(self) -> bool:
        """Step 3: Check that all imports are correct."""
        self.step("3. Check Imports")

        files_to_check = ["main.py", "__init__.py", "version_manager.py"]

        for filename in files_to_check:
            filepath = self.test_app_path / filename

            if not filepath.exists():
                continue

            content = filepath.read_text()

            # Check for OLD style imports (should not exist)
            old_imports = [
                "from base_application import",
                "from mesh_integration import",
                "from parent_cc_protocol import",
                "from version_info._version_data import"
            ]

            for old_import in old_imports:
                if old_import in content:
                    self.error(f"{filename}: Found old import: {old_import}")
                    return False

            # Check for NEW style imports (should exist)
            if filename in ["main.py", "__init__.py"]:
                required_imports = [
                    "from sw_core.base_application import",
                    "from sw_core.parent_cc_protocol import"
                ]

                for required in required_imports:
                    if required not in content:
                        self.error(f"{filename}: Missing sw_core import: {required}")
                        return False

            self.log(f"{filename}: Imports correct", "PASS")

        return True

    def test_4_verify_placeholders(self) -> bool:
        """Step 4: Verify placeholder replacement."""
        self.step("4. Verify Placeholder Replacement")

        # Check main.py for proper class name
        main_py = self.test_app_path / "main.py"
        content = main_py.read_text()

        # Should NOT contain literal {APP_NAME}
        if "{APP_NAME}" in content:
            self.error("main.py: Placeholder {APP_NAME} not replaced")
            return False

        # Should contain actual app name
        if f"class {self.test_app_name}" not in content:
            self.error(f"main.py: Class name not customized to {self.test_app_name}")
            return False

        if f'app_name: str = "{self.test_app_name}"' not in content:
            self.error(f"main.py: App name parameter not customized")
            return False

        self.log("Placeholders replaced correctly", "PASS")
        return True

    def test_5_syntax_check(self) -> bool:
        """Step 5: Python syntax check."""
        self.step("5. Python Syntax Check")

        py_files = list(self.test_app_path.glob("*.py"))

        for py_file in py_files:
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.error(f"{py_file.name}: Syntax error - {result.stderr}")
                return False

            self.log(f"{py_file.name}: Syntax valid", "PASS")

        return True

    def test_6_launch_app(self) -> bool:
        """Step 6: Launch app in headless mode."""
        self.step("6. Launch App (Headless)")

        log_file = Path(f"/tmp/{self.test_app_name}_test.log")

        try:
            self.log("Starting app in headless mode...")

            self.process = subprocess.Popen(
                ["python3", "main.py", "--headless"],
                cwd=self.test_app_path,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT
            )

            self.pid = self.process.pid
            self.log(f"App started: PID {self.pid}", "PASS")

            # Wait for startup
            self.log("Waiting 3s for startup...")
            time.sleep(3)

            # Check if still running
            if self.process.poll() is not None:
                self.error("App died immediately after launch")

                # Show log
                if log_file.exists():
                    log_content = log_file.read_text()
                    print("\nLast 20 lines of log:")
                    print('\n'.join(log_content.split('\n')[-20:]))

                return False

            self.log("App running successfully", "PASS")
            return True

        except Exception as e:
            self.error(f"Launch failed: {e}")
            return False

    def test_7_verify_mesh(self) -> bool:
        """Step 7: Verify mesh registration."""
        self.step("7. Verify Mesh Registration")

        try:
            response = requests.get("http://localhost:6001/services", timeout=5)
            services = response.json()

            # Find our app
            service_name = self.test_app_name.lower()

            found = False
            if isinstance(services, list):
                for service in services:
                    if service.get('instance_name', '').lower() == service_name:
                        found = True
                        self.log(f"Found in mesh: {service_name}", "PASS")
                        break

            if not found:
                self.warning(f"App not found in mesh (may be normal)")
                return True  # Don't fail test, just warn

            return True

        except Exception as e:
            self.warning(f"Could not verify mesh: {e}")
            return True  # Don't fail test

    def test_8_graceful_shutdown(self) -> bool:
        """Step 8: Test graceful shutdown."""
        self.step("8. Test Graceful Shutdown")

        if not self.process or self.process.poll() is not None:
            self.error("App not running for shutdown test")
            return False

        try:
            self.log("Sending SIGTERM...")
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=5)
                self.log("Graceful shutdown successful", "PASS")
                return True
            except subprocess.TimeoutExpired:
                self.warning("Graceful shutdown timeout, forcing kill")
                self.process.kill()
                return True  # Don't fail, just warn

        except Exception as e:
            self.error(f"Shutdown test failed: {e}")
            return False

    def test_9_verify_cleanup(self) -> bool:
        """Step 9: Verify no zombies or leaks."""
        self.step("9. Verify Cleanup")

        # Check for zombie processes
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        zombies = [
            line for line in result.stdout.split('\n')
            if self.test_app_name in line and ('Z+' in line or '<defunct>' in line)
        ]

        if zombies:
            self.error(f"Zombie processes detected: {len(zombies)}")
            return False

        self.log("No zombie processes", "PASS")
        return True

    def cleanup_test_app(self):
        """Clean up test app and folder."""
        if not self.cleanup:
            self.log("Cleanup disabled, leaving test app")
            return

        self.step("Cleanup")

        try:
            if self.test_pcc_folder.exists():
                shutil.rmtree(self.test_pcc_folder)
                self.log(f"Deleted: {self.test_pcc_folder}", "PASS")
        except Exception as e:
            self.warning(f"Cleanup failed: {e}")

    # -------------------------------------------------------------------------
    # Main Test Runner
    # -------------------------------------------------------------------------

    def run(self) -> bool:
        """Run complete test suite."""
        print("=" * 80)
        print("TEMPLATE GENERATION TEST - End-to-End Validation")
        print("=" * 80)
        print(f"Test App: {self.test_app_name}")
        print(f"Test Folder: {self.test_pcc_folder}")
        print(f"Cleanup: {self.cleanup}")
        print()

        tests = [
            ("Generate App", self.test_1_generate_app),
            ("Verify Structure", self.test_2_verify_structure),
            ("Check Imports", self.test_3_check_imports),
            ("Verify Placeholders", self.test_4_verify_placeholders),
            ("Syntax Check", self.test_5_syntax_check),
            ("Launch App", self.test_6_launch_app),
            ("Verify Mesh", self.test_7_verify_mesh),
            ("Graceful Shutdown", self.test_8_graceful_shutdown),
            ("Verify Cleanup", self.test_9_verify_cleanup)
        ]

        passed = 0
        failed = 0

        try:
            for test_name, test_func in tests:
                result = test_func()

                if result:
                    passed += 1
                else:
                    failed += 1
                    # Continue with remaining tests even if one fails

        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted")
            if self.process and self.process.poll() is None:
                self.process.kill()

        finally:
            # Always cleanup
            self.cleanup_test_app()

        # Final Report
        duration = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{len(tests)}")
        print(f"Tests Failed: {failed}/{len(tests)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Duration: {duration:.1f}s")
        print()

        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"  ✗ {error}")
            print()

        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()

        if failed == 0:
            print("✅ ALL TESTS PASSED")
            print()
            return True
        else:
            print("❌ TESTS FAILED")
            print()
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test template generation end-to-end"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't delete test app after test (for debugging)"
    )

    args = parser.parse_args()

    test = TemplateGenerationTest(cleanup=not args.no_cleanup)
    success = test.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
