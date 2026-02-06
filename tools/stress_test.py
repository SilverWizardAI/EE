#!/usr/bin/env python3
"""
Stress test for library validation - launch multiple concurrent apps.

Tests:
- 10+ concurrent app instances
- Mesh registration under load
- Clean shutdown of all instances
- No zombie processes
- No stale mesh entries
"""

import subprocess
import time
import signal
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any

APP_PATH = Path("/Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/TestLibValidation_PCC/apps/TestLibValidation")
LOG_DIR = Path("/tmp/stress_test_logs")
MESH_URL = "http://localhost:6001"


class StressTest:
    """Stress test runner."""

    def __init__(self, num_instances: int = 10):
        self.num_instances = num_instances
        self.processes: List[subprocess.Popen] = []
        self.pids: List[int] = []

    def launch_instances(self):
        """Launch multiple app instances."""
        print(f"🚀 Launching {self.num_instances} concurrent instances...")

        for i in range(1, self.num_instances + 1):
            log_file = LOG_DIR / f"instance_{i}.log"

            try:
                # Launch in headless mode
                proc = subprocess.Popen(
                    ["python3", "main.py", "--headless"],
                    cwd=APP_PATH,
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT,
                    preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL)
                )

                self.processes.append(proc)
                self.pids.append(proc.pid)
                print(f"  ✓ Instance {i}: PID {proc.pid}")

                # Small delay to avoid overwhelming the mesh
                time.sleep(0.2)

            except Exception as e:
                print(f"  ✗ Instance {i}: Failed - {e}")

        print(f"✓ Launched {len(self.processes)} instances\n")

    def verify_startup(self, wait_time: int = 5):
        """Wait and verify all instances started."""
        print(f"⏳ Waiting {wait_time}s for startup...")
        time.sleep(wait_time)

        # Check processes
        running = sum(1 for p in self.processes if p.poll() is None)
        print(f"✓ Running processes: {running}/{len(self.processes)}")

        # Check mesh registrations
        try:
            response = requests.get(f"{MESH_URL}/services")
            services = response.json()

            test_services = [
                s for s in services
                if s.get('instance_name', '').startswith('testlibvalidation')
            ]

            print(f"✓ Mesh registrations: {len(test_services)}")

            if len(test_services) < len(self.processes):
                print(f"⚠️  Warning: {len(self.processes) - len(test_services)} apps not registered")

        except Exception as e:
            print(f"✗ Failed to check mesh: {e}")

        print()

    def check_logs(self):
        """Check logs for errors."""
        print("🔍 Checking logs for errors...")

        errors = []
        for i in range(1, self.num_instances + 1):
            log_file = LOG_DIR / f"instance_{i}.log"

            if log_file.exists():
                content = log_file.read_text()

                # Look for error indicators
                if "ERROR" in content or "Exception" in content or "Traceback" in content:
                    errors.append(f"Instance {i}: Errors detected")

        if errors:
            print(f"✗ Errors found in {len(errors)} logs:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ No errors detected in logs")

        print()

    def shutdown_instances(self):
        """Gracefully shutdown all instances."""
        print(f"🛑 Shutting down {len(self.processes)} instances...")

        # Send SIGTERM to all
        for i, proc in enumerate(self.processes, 1):
            if proc.poll() is None:
                try:
                    proc.terminate()
                    print(f"  ✓ Instance {i}: SIGTERM sent")
                except Exception as e:
                    print(f"  ✗ Instance {i}: Failed - {e}")

        # Wait for graceful shutdown
        print("⏳ Waiting 5s for graceful shutdown...")
        time.sleep(5)

        # Check if any are still running
        still_running = []
        for i, proc in enumerate(self.processes, 1):
            if proc.poll() is None:
                still_running.append((i, proc))

        if still_running:
            print(f"⚠️  {len(still_running)} instances still running, forcing kill...")
            for i, proc in still_running:
                proc.kill()
                print(f"  ✓ Instance {i}: SIGKILL sent")

        # Final cleanup
        for proc in self.processes:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

        print("✓ All instances stopped\n")

    def verify_cleanup(self):
        """Verify clean shutdown."""
        print("🔍 Verifying cleanup...")

        # Check for zombie processes
        import subprocess
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        zombies = [
            line for line in result.stdout.split('\n')
            if 'TestLibValidation' in line and 'Z+' in line
        ]

        if zombies:
            print(f"✗ Zombie processes: {len(zombies)}")
            for zombie in zombies:
                print(f"  - {zombie}")
        else:
            print("✓ No zombie processes")

        # Check mesh cleanup
        try:
            response = requests.get(f"{MESH_URL}/services")
            services = response.json()

            stale_services = [
                s for s in services
                if s.get('instance_name', '').startswith('testlibvalidation')
            ]

            if stale_services:
                print(f"✗ Stale mesh entries: {len(stale_services)}")
                for service in stale_services:
                    print(f"  - {service.get('instance_name')}")
            else:
                print("✓ No stale mesh entries")

        except Exception as e:
            print(f"✗ Failed to check mesh: {e}")

        print()

    def run(self):
        """Run complete stress test."""
        print("=" * 80)
        print("STRESS TEST - 10+ Concurrent Instances")
        print("=" * 80)
        print()

        try:
            self.launch_instances()
            self.verify_startup()
            self.check_logs()

            # Keep running for a bit
            print("⏳ Running for 10 seconds...")
            time.sleep(10)
            print()

            self.shutdown_instances()
            self.verify_cleanup()

            # Final summary
            print("=" * 80)
            print("STRESS TEST COMPLETE")
            print("=" * 80)
            print(f"Instances launched: {len(self.processes)}")
            print(f"PIDs: {self.pids}")
            print("Logs: /tmp/stress_test_logs/")
            print()

        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted, cleaning up...")
            self.shutdown_instances()
            sys.exit(1)


if __name__ == "__main__":
    test = StressTest(num_instances=10)
    test.run()
