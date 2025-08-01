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
import pytest


class TestStreaming:
    """Self-contained streaming tester."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        cls.base_url = "http://127.0.0.1:8000"
        cls.server_process = None
        cls.test_results = []

        if not cls.start_server():
            pytest.fail("Failed to start server")

    @classmethod
    def start_server(cls):
        """Start the Maestro workflow server."""
        print("🚀 Starting Maestro workflow server...")

        agents_file = "tests/yamls/agents/simple_agent.yaml"
        workflow_file = "tests/yamls/workflows/simple_workflow.yaml"

        cmd = ["maestro", "serve", agents_file, workflow_file, "--host", "127.0.0.1"]

        cls.server_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        print("⏳ Waiting for server to start...")
        for attempt in range(15):
            try:
                response = requests.get(f"{cls.base_url}/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        if cls.server_process.poll() is not None:
            stdout, stderr = cls.server_process.communicate()
            print("❌ Server process failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        else:
            print("❌ Server failed to start within 15 seconds")
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()

        return False

    def test_streaming(self):
        """Test the streaming functionality."""
        print("\n📡 Testing streaming endpoint...")

        url = f"{self.base_url}/chat/stream"
        payload = {"prompt": "Write a short story about a cat"}

        response = requests.post(url, json=payload, stream=True, timeout=30)
        assert response.status_code == 200, (
            f"Streaming request failed with status {response.status_code}"
        )

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

        assert len(step_responses) >= 1, "No step responses received"

        for step in step_responses:
            assert all(
                key in step
                for key in [
                    "step_name",
                    "step_result",
                    "agent_name",
                    "step_complete",
                ]
            ), f"Invalid step structure: {step}"
            assert step["step_complete"], f"Step not marked as complete: {step}"

        assert final_response is not None, "No final workflow response received"
        assert "workflow_complete" in final_response, (
            "Final response missing workflow_complete flag"
        )
        assert final_response["workflow_complete"], (
            "Final response not marked as complete"
        )

        print("✅ All streaming tests passed!")

    def test_step_order(self):
        """Test that steps stream in the correct order."""
        print("\n🔍 Testing step order...")

        url = f"{self.base_url}/chat/stream"
        payload = {"prompt": "Test prompt"}

        response = requests.post(url, json=payload, stream=True, timeout=30)
        assert response.status_code == 200, (
            f"Step order test failed with status {response.status_code}"
        )

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
        assert step_order == expected_order, (
            f"Steps streamed in wrong order. Expected {expected_order}, got {step_order}"
        )
        print(f"✅ Steps streamed in correct order: {step_order}")

    @classmethod
    def teardown_class(cls):
        """Clean up after all tests."""
        if cls.server_process:
            print("\n🧹 Cleaning up server...")
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=5)
                print("✅ Server stopped successfully")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop gracefully, forcing...")
                cls.server_process.kill()
                cls.server_process.wait()
