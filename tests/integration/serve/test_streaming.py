#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Maestro Streaming Test
======================

A single, self-contained test file that:
1. Starts the Maestro workflow server automatically
2. Tests the streaming functionality
3. Verifies step-by-step responses
4. Cleans up automatically

Usage: python test_streaming.py
"""

import json
import time
import requests
import subprocess
import sys


class StreamingTester:
    """Self-contained streaming tester."""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.server_process = None
        self.test_results = []

    def start_server(self):
        """Start the Maestro workflow server."""
        print("🚀 Starting Maestro workflow server...")

        agents_file = "tests/yamls/agents/simple_agent.yaml"
        workflow_file = "tests/yamls/workflows/simple_workflow.yaml"

        cmd = [sys.executable, "-m", "maestro", "serve", agents_file, workflow_file]

        self.server_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        print("⏳ Waiting for server to start...")
        for attempt in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{self.base_url}/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        print("❌ Server failed to start within 30 seconds")
        return False

    def test_streaming(self):
        """Test the streaming functionality."""
        print("\n📡 Testing streaming endpoint...")

        url = f"{self.base_url}/chat/stream"
        payload = {"prompt": "Write a short story about a cat"}

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            if response.status_code != 200:
                print(f"❌ Streaming request failed with status {response.status_code}")
                return False

            step_responses = []
            final_response = None

            print("📊 Collecting streaming responses...")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        try:
                            data = json.loads(data_str)

                            if "step_name" in data:
                                step_responses.append(
                                    {
                                        "step_name": data["step_name"],
                                        "step_result": data["step_result"],
                                        "agent_name": data["agent_name"],
                                        "step_complete": data["step_complete"],
                                    }
                                )
                                print(
                                    f"   ✅ Step: {data['step_name']} (Agent: {data['agent_name']})"
                                )
                            elif "workflow_complete" in data:
                                final_response = data
                                print("   🎉 Workflow completed!")

                        except json.JSONDecodeError:
                            continue

            print("\n📈 Test Results:")
            print(f"   - Steps received: {len(step_responses)}")
            print(f"   - Final response: {'✅' if final_response else '❌'}")

            if len(step_responses) < 1:
                print("❌ No step responses received")
                return False

            for step in step_responses:
                if not all(
                    key in step
                    for key in [
                        "step_name",
                        "step_result",
                        "agent_name",
                        "step_complete",
                    ]
                ):
                    print(f"❌ Invalid step structure: {step}")
                    return False
                if not step["step_complete"]:
                    print(f"❌ Step not marked as complete: {step}")
                    return False

            if not final_response:
                print("❌ No final workflow response received")
                return False
            if "workflow_complete" not in final_response:
                print("❌ Final response missing workflow_complete flag")
                return False
            if not final_response["workflow_complete"]:
                print("❌ Final response not marked as complete")
                return False

            print("✅ All streaming tests passed!")
            return True

        except requests.exceptions.Timeout:
            print("❌ Streaming request timed out")
            return False
        except Exception as e:
            print(f"❌ Streaming test failed: {e}")
            return False

    def test_step_order(self):
        """Test that steps stream in the correct order."""
        print("\n🔍 Testing step order...")

        url = f"{self.base_url}/chat/stream"
        payload = {"prompt": "Test prompt"}

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            if response.status_code != 200:
                print(f"❌ Step order test failed with status {response.status_code}")
                return False

            step_order = []

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        try:
                            data = json.loads(data_str)

                            if "step_name" in data:
                                step_order.append(data["step_name"])

                        except json.JSONDecodeError:
                            continue

            expected_order = ["step1", "step2", "step3"]
            if step_order == expected_order:
                print(f"✅ Steps streamed in correct order: {step_order}")
                return True
            else:
                print(
                    f"❌ Steps streamed in wrong order. Expected {expected_order}, got {step_order}"
                )
                return False

        except Exception as e:
            print(f"❌ Step order test failed: {e}")
            return False

    def cleanup(self):
        """Clean up the server process."""
        if self.server_process:
            print("\n🧹 Cleaning up server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✅ Server stopped successfully")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop gracefully, forcing...")
                self.server_process.kill()
                self.server_process.wait()

    def run_all_tests(self):
        """Run all streaming tests."""
        print("🧪 Maestro Streaming Test Suite")
        print("=" * 40)

        try:
            if not self.start_server():
                return False

            tests = [
                ("Streaming Functionality", self.test_streaming),
                ("Step Order", self.test_step_order),
            ]

            all_passed = True
            for test_name, test_func in tests:
                print(f"\n{'=' * 20} {test_name} {'=' * 20}")
                if not test_func():
                    all_passed = False

            print(f"\n{'=' * 50}")
            if all_passed:
                print("🎉 ALL TESTS PASSED!")
                print("✅ Streaming functionality is working correctly")
            else:
                print("❌ SOME TESTS FAILED!")
                print("Please check the output above for details")

            return all_passed

        finally:
            self.cleanup()


def main():
    """Main test runner."""
    tester = StreamingTester()
    success = tester.run_all_tests()

    if success:
        print("\n Working as expected!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix the issues above")
        sys.exit(1)


if __name__ == "__main__":
    main()
