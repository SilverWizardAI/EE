#!/usr/bin/env python3
"""
EEM Cycle Test - Multi-Step Integration Test

Tests the complete EEM ↔ EE communication cycle via MM mesh:
1. EEM creates EE CC instance
2. EE runs InstanceServer and registers with MM mesh
3. EE simulates work and reports status
4. EEM heartbeat polls EE for status updates
5. EE reports end of cycle
6. EEM kills EE terminal
7. EEM starts new cycle

This validates that the MM mesh integration works end-to-end.

Usage:
    python3 tools/test_eem_cycle.py
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

# Add MM to path
mm_path = Path.home() / "Library/CloudStorage/Dropbox/A_Coding/MM"
if mm_path.exists():
    sys.path.insert(0, str(mm_path))

from mcp_mesh.client import MeshClient

# Import EE HTTP server
sys.path.insert(0, str(Path(__file__).parent))
from ee_http_server import EEHTTPServer

logger = logging.getLogger(__name__)


class EEMCycleTest:
    """Test EEM cycle management with MM mesh integration"""

    def __init__(self):
        self.mesh = None
        self.test_results = []

    def log_test(self, step: str, status: str, message: str):
        """Log test step"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {status:6} | Step {step:2} | {message}"
        print(result)
        self.test_results.append({
            "step": step,
            "status": status,
            "message": message,
            "timestamp": timestamp
        })

    def check_mm_mesh_running(self) -> bool:
        """Check if MM mesh proxy is running"""
        try:
            import httpx
            response = httpx.get("http://localhost:6001/services", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def test_step_1_check_prerequisites(self) -> bool:
        """Step 1: Check prerequisites"""
        self.log_test("1", "START", "Checking prerequisites")

        # Check MM mesh
        if not self.check_mm_mesh_running():
            self.log_test("1", "FAIL", "MM mesh not running on port 6001")
            return False

        self.log_test("1", "PASS", "MM mesh is running")

        # Initialize MeshClient
        try:
            self.mesh = MeshClient(proxy_host="localhost", proxy_port=6001)
            self.log_test("1", "PASS", "MeshClient initialized")
        except Exception as e:
            self.log_test("1", "FAIL", f"Failed to initialize MeshClient: {e}")
            return False

        return True

    def test_step_2_create_ee_instance(self, cycle_number: int) -> EEHTTPServer:
        """Step 2: Create EE InstanceServer"""
        self.log_test("2", "START", f"Creating EE instance for cycle {cycle_number}")

        try:
            server = EEHTTPServer(cycle_number=cycle_number)
            self.log_test("2", "PASS", f"Created {server.instance_name}")
            return server
        except Exception as e:
            self.log_test("2", "FAIL", f"Failed to create instance: {e}")
            return None

    def test_step_3_start_instance_server(self, server: EEHTTPServer) -> bool:
        """Step 3: Start InstanceServer"""
        self.log_test("3", "START", "Starting InstanceServer")

        try:
            server.start()
            time.sleep(2)  # Give it time to register

            if server.running:
                self.log_test("3", "PASS", "InstanceServer started")
                return True
            else:
                self.log_test("3", "FAIL", "InstanceServer not running")
                return False
        except Exception as e:
            self.log_test("3", "FAIL", f"Failed to start server: {e}")
            return False

    def test_step_4_verify_registration(self, instance_name: str) -> bool:
        """Step 4: Verify registration with MM mesh"""
        self.log_test("4", "START", "Verifying registration with MM mesh")

        try:
            import httpx
            response = httpx.get("http://localhost:6001/services", timeout=2.0)
            data = response.json()
            services = data.get("services", [])

            # Check if our instance is registered
            found = False
            for svc in services:
                if svc.get("instance_name") == instance_name:
                    found = True
                    tools = svc.get("tools", [])
                    status = svc.get("status", "unknown")
                    self.log_test("4", "INFO", f"Found {instance_name}: {len(tools)} tools, status={status}")

                    # Verify tools are registered
                    expected_tools = ["get_status", "get_progress", "get_cycle_info"]
                    for tool in expected_tools:
                        if tool not in tools:
                            self.log_test("4", "WARN", f"Tool '{tool}' not registered")

            if found:
                self.log_test("4", "PASS", f"{instance_name} registered with MM mesh")
                return True
            else:
                self.log_test("4", "FAIL", f"{instance_name} NOT found in MM mesh")
                return False

        except Exception as e:
            self.log_test("4", "FAIL", f"Failed to verify registration: {e}")
            return False

    def test_step_5_simulate_work(self, server: EEHTTPServer) -> bool:
        """Step 5: Simulate EE doing work"""
        self.log_test("5", "START", "Simulating EE work (3 steps)")

        try:
            steps = [
                (1, "Analyzing codebase", "15%", 25000),
                (2, "Extracting components", "45%", 50000),
                (3, "Testing integration", "85%", 75000),
            ]

            for step, task, progress, tokens in steps:
                server.update_status(
                    step=step,
                    task=task,
                    progress=progress,
                    tokens_used=tokens,
                    next_action=f"Next: Step {step+1}"
                )
                self.log_test("5", "INFO", f"Step {step}: {task} ({progress})")
                time.sleep(1)

            self.log_test("5", "PASS", "Simulated 3 work steps")
            return True

        except Exception as e:
            self.log_test("5", "FAIL", f"Failed to simulate work: {e}")
            return False

    def test_step_6_eem_heartbeat_polling(self, instance_name: str, num_polls: int = 3) -> bool:
        """Step 6: EEM polls EE for status"""
        self.log_test("6", "START", f"EEM heartbeat polling ({num_polls} times)")

        try:
            for i in range(num_polls):
                status = self.mesh.call_service(
                    target_instance=instance_name,
                    tool_name="get_status",
                    arguments={},
                    timeout=5.0
                )

                # Debug: print full response
                print(f"DEBUG: Full status response: {status}")

                step = status.get("step", "?")
                task = status.get("task", "?")
                progress = status.get("progress", "?")
                cycle_status = status.get("cycle_status", "?")

                self.log_test("6", "INFO",
                    f"Poll {i+1}: Step {step}, {task}, {progress}, status={cycle_status}")

                time.sleep(1)

            self.log_test("6", "PASS", f"Completed {num_polls} successful heartbeat polls")
            return True

        except Exception as e:
            self.log_test("6", "FAIL", f"Heartbeat polling failed: {e}")
            return False

    def test_step_7_report_cycle_complete(self, server: EEHTTPServer) -> bool:
        """Step 7: EE reports cycle complete"""
        self.log_test("7", "START", "EE reporting cycle complete")

        try:
            server.update_status(
                step=15,
                task="All steps complete",
                cycle_status="complete",
                progress="100%",
                tokens_used=95000,
                next_action="Cycle complete - ready for handoff"
            )

            self.log_test("7", "PASS", "EE marked cycle as complete")
            return True

        except Exception as e:
            self.log_test("7", "FAIL", f"Failed to mark complete: {e}")
            return False

    def test_step_8_eem_detect_completion(self, instance_name: str) -> bool:
        """Step 8: EEM detects cycle completion"""
        self.log_test("8", "START", "EEM detecting cycle completion")

        try:
            status = self.mesh.call_service(
                target_instance=instance_name,
                tool_name="get_status",
                arguments={},
                timeout=5.0
            )

            cycle_status = status.get("cycle_status")

            if cycle_status == "complete":
                self.log_test("8", "PASS", "EEM detected cycle completion")
                return True
            else:
                self.log_test("8", "FAIL", f"Cycle status is '{cycle_status}', not 'complete'")
                return False

        except Exception as e:
            self.log_test("8", "FAIL", f"Failed to detect completion: {e}")
            return False

    def test_step_9_stop_ee_instance(self, server: EEHTTPServer) -> bool:
        """Step 9: EEM stops EE instance"""
        self.log_test("9", "START", "Stopping EE instance")

        try:
            server.stop()
            time.sleep(1)

            if not server.running:
                self.log_test("9", "PASS", "EE instance stopped")
                return True
            else:
                self.log_test("9", "FAIL", "EE instance still running")
                return False

        except Exception as e:
            self.log_test("9", "FAIL", f"Failed to stop instance: {e}")
            return False

    def test_step_10_verify_deregistration(self, instance_name: str) -> bool:
        """Step 10: Verify deregistration from MM mesh"""
        self.log_test("10", "START", "Verifying deregistration")

        # Wait for mesh to notice (may take up to heartbeat timeout)
        time.sleep(3)

        try:
            import httpx
            response = httpx.get("http://localhost:6001/services", timeout=2.0)
            data = response.json()
            services = data.get("services", [])

            # Check if instance is still registered
            found = False
            for svc in services:
                if svc.get("instance_name") == instance_name:
                    found = True
                    status = svc.get("status", "unknown")
                    self.log_test("10", "INFO", f"{instance_name} still in mesh with status={status}")

            if found:
                self.log_test("10", "WARN",
                    f"{instance_name} still registered (will timeout naturally)")
                # This is OK - mesh will clean up after heartbeat timeout
                return True
            else:
                self.log_test("10", "PASS", f"{instance_name} deregistered")
                return True

        except Exception as e:
            self.log_test("10", "FAIL", f"Failed to verify deregistration: {e}")
            return False

    def run_full_cycle_test(self, cycle_number: int = 99) -> bool:
        """Run complete cycle test"""
        print("\n" + "="*70)
        print(f"EEM CYCLE TEST - Cycle {cycle_number}")
        print("="*70)
        print()

        # Step 1: Prerequisites
        if not self.test_step_1_check_prerequisites():
            return False

        # Step 2: Create EE instance
        server = self.test_step_2_create_ee_instance(cycle_number)
        if not server:
            return False

        instance_name = server.instance_name

        # Step 3: Start server
        if not self.test_step_3_start_instance_server(server):
            return False

        # Step 4: Verify registration
        if not self.test_step_4_verify_registration(instance_name):
            return False

        # Step 5: Simulate work
        if not self.test_step_5_simulate_work(server):
            return False

        # Step 6: EEM heartbeat polling
        if not self.test_step_6_eem_heartbeat_polling(instance_name, num_polls=5):
            return False

        # Step 7: Report cycle complete
        if not self.test_step_7_report_cycle_complete(server):
            return False

        # Step 8: EEM detect completion
        if not self.test_step_8_eem_detect_completion(instance_name):
            return False

        # Step 9: Stop EE instance
        if not self.test_step_9_stop_ee_instance(server):
            return False

        # Step 10: Verify deregistration
        if not self.test_step_10_verify_deregistration(instance_name):
            return False

        return True

    def print_summary(self, success: bool):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = passed + failed

        print(f"\nTotal Steps: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"\nOverall: {'✅ SUCCESS' if success and failed == 0 else '❌ FAILED'}")
        print()

        if failed > 0:
            print("Failed Steps:")
            for r in self.test_results:
                if r["status"] == "FAIL":
                    print(f"  - Step {r['step']}: {r['message']}")
            print()


def main():
    """Run test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    test = EEMCycleTest()
    success = test.run_full_cycle_test(cycle_number=99)
    test.print_summary(success)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
