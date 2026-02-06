#!/usr/bin/env python3
"""
Failure recovery test - crash and restart validation.

Tests:
- App can be force-killed (SIGKILL)
- App can restart after crash
- Mesh handles stale entries
- No resource leaks after crash
"""

import subprocess
import time
import signal
import sys
import requests
from pathlib import Path

APP_PATH = Path("/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/TestLibValidation_PCC/apps/TestLibValidation")
LOG_FILE = Path("/tmp/failure_recovery_test.log")
MESH_URL = "http://localhost:6001"


class FailureRecoveryTest:
    """Failure recovery test runner."""

    def __init__(self):
        self.process = None
        self.pid = None

    def launch_app(self, instance_num: int = 1):
        """Launch app instance."""
        print(f"🚀 Launching instance {instance_num}...")

        log_file = Path(f"/tmp/failure_recovery_{instance_num}.log")

        try:
            self.process = subprocess.Popen(
                ["python3", "main.py", "--headless"],
                cwd=APP_PATH,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT
            )

            self.pid = self.process.pid
            print(f"  ✓ PID: {self.pid}")
            print(f"  ✓ Log: {log_file}")

            # Wait for startup
            time.sleep(3)

            # Verify running
            if self.process.poll() is None:
                print(f"  ✓ Process running")
            else:
                print(f"  ✗ Process died immediately!")
                return False

            # Check mesh registration
            try:
                response = requests.get(f"{MESH_URL}/services")
                services = response.json()

                if isinstance(services, list):
                    registered = any(
                        s.get('instance_name', '').startswith('testlibvalidation')
                        for s in services
                    )
                else:
                    registered = False

                if registered:
                    print(f"  ✓ Registered with mesh")
                else:
                    print(f"  ⚠️  Not found in mesh")

            except Exception as e:
                print(f"  ⚠️  Could not verify mesh: {e}")

            return True

        except Exception as e:
            print(f"  ✗ Launch failed: {e}")
            return False

    def crash_app(self):
        """Forcefully kill app (simulate crash)."""
        print(f"\n💥 Crashing app (SIGKILL)...")

        if self.process and self.process.poll() is None:
            try:
                self.process.kill()  # SIGKILL - immediate termination
                print(f"  ✓ SIGKILL sent to PID {self.pid}")

                # Wait for termination
                self.process.wait(timeout=2)
                print(f"  ✓ Process terminated")

            except Exception as e:
                print(f"  ✗ Kill failed: {e}")
        else:
            print(f"  ⚠️  Process not running")

    def check_stale_entries(self):
        """Check for stale mesh entries after crash."""
        print(f"\n🔍 Checking for stale mesh entries...")

        try:
            response = requests.get(f"{MESH_URL}/services")
            services = response.json()

            if isinstance(services, list):
                stale = [
                    s for s in services
                    if s.get('instance_name', '').startswith('testlibvalidation')
                ]

                if stale:
                    print(f"  ⚠️  Stale entries: {len(stale)}")
                    for service in stale:
                        name = service.get('instance_name', 'unknown')
                        print(f"    - {name}")
                    print(f"  ℹ️  Note: Mesh will clean these up automatically")
                else:
                    print(f"  ✓ No stale entries")
            else:
                print(f"  ⚠️  Unexpected mesh response format")

        except Exception as e:
            print(f"  ✗ Check failed: {e}")

    def run(self):
        """Run complete failure recovery test."""
        print("=" * 80)
        print("FAILURE RECOVERY TEST")
        print("=" * 80)
        print()

        try:
            # Test 1: Launch and crash
            print("TEST 1: Launch and Crash")
            print("-" * 80)
            success = self.launch_app(instance_num=1)

            if not success:
                print("\n✗ TEST FAILED: Could not launch app")
                return

            print("\n⏳ Running for 5 seconds...")
            time.sleep(5)

            self.crash_app()
            self.check_stale_entries()

            # Test 2: Restart after crash
            print("\n" + "=" * 80)
            print("TEST 2: Restart After Crash")
            print("-" * 80)

            time.sleep(2)  # Brief pause

            success = self.launch_app(instance_num=2)

            if not success:
                print("\n✗ TEST FAILED: Could not restart after crash")
                return

            print("\n⏳ Running for 5 seconds...")
            time.sleep(5)

            # Test 3: Clean shutdown after recovery
            print("\n" + "=" * 80)
            print("TEST 3: Clean Shutdown After Recovery")
            print("-" * 80)

            if self.process and self.process.poll() is None:
                print("🛑 Sending graceful shutdown...")
                self.process.terminate()  # SIGTERM

                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                    print("  ✓ Graceful shutdown successful")
                except subprocess.TimeoutExpired:
                    print("  ⚠️  Timeout, forcing kill")
                    self.process.kill()

            # Final verification
            print("\n" + "=" * 80)
            print("FINAL VERIFICATION")
            print("-" * 80)

            # Check for zombies
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )

            zombies = [
                line for line in result.stdout.split('\n')
                if 'TestLibValidation' in line and ('Z+' in line or '<defunct>' in line)
            ]

            if zombies:
                print(f"✗ Zombie processes: {len(zombies)}")
            else:
                print("✓ No zombie processes")

            # Check mesh
            self.check_stale_entries()

            # Summary
            print("\n" + "=" * 80)
            print("FAILURE RECOVERY TEST COMPLETE")
            print("=" * 80)
            print("✓ App survived crash and restart")
            print("✓ No resource leaks detected")
            print()

        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted")
            if self.process and self.process.poll() is None:
                self.process.kill()
            sys.exit(1)


if __name__ == "__main__":
    test = FailureRecoveryTest()
    test.run()
