#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Simple integration test for serve functionality."""

import os
import sys
import time
import subprocess
import requests
import shutil
import socket


def find_maestro_executable():
    """Find the maestro executable."""
    # Try to find maestro in the current directory or PATH
    if os.path.exists("./maestro"):
        return "./maestro"
    elif shutil.which("maestro"):
        return "maestro"
    else:
        # Try python -m maestro
        return ["python", "-m", "maestro"]


def find_free_port():
    """Find a free port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def wait_for_server(url, timeout=30):
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    return False


def test_wow_integration():
    """Test the serve functionality with a real server."""
    print("Starting serve integration test...")

    # Find the test agent file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(test_dir)))
    agent_remote_file = os.path.join(
        project_root, "tests", "yamls", "agents", "simple_remote_agents.yaml"
    )
    agent_wow_file = os.path.join(
        project_root, "tests", "yamls", "agents", "simple_wow_agents.yaml"
    )
    workflow_remote_file = os.path.join(
        project_root, "tests", "yamls", "workflows", "simple_remote_workflow.yaml"
    )
    workflow_wow_file = os.path.join(
        project_root, "tests", "yamls", "workflows", "simple_wow_workflow.yaml"
    )

    assert os.path.exists(agent_wow_file), f"Agent file not found at {agent_wow_file}"
    assert os.path.exists(agent_remote_file), (
        f"Agent file not found at {agent_remote_file}"
    )
    assert os.path.exists(workflow_wow_file), (
        f"Workflow file not found at {workflow_wow_file}"
    )
    assert os.path.exists(workflow_remote_file), (
        f"Workflow file not found at {workflow_remote_file}"
    )

    # Find maestro executable
    maestro_cmd = find_maestro_executable()
    if isinstance(maestro_cmd, str):
        cmd = [
            maestro_cmd,
            "serve",
            agent_remote_file,
            workflow_remote_file,
            "--port",
            "8003",
            "--host",
            "127.0.0.1",
        ]
    else:
        cmd = maestro_cmd + [
            "serve",
            agent_remote_file,
            workflow_remote_file,
            "--port",
            "8003",
            "--host",
            "127.0.0.1",
        ]

    print(f"Starting server with command: {' '.join(cmd)}")

    # Start the server
    test_env = os.environ.copy()
    test_env["DRY_RUN"] = "1"
    server_process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=test_env
    )

    try:
        # Wait for server to start
        print("Waiting for server to start...")
        assert wait_for_server("http://127.0.0.1:8003"), (
            "Server failed to start within timeout"
        )

        print("Server is ready!")

        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8003/health")
        assert response.status_code == 200, (
            f"Health endpoint returned {response.status_code}"
        )

        health_data = response.json()
        print(f"Health check response: {health_data}")

        # Test chat endpoint
        print("Testing chat endpoint...")
        test_prompt = "Hello, this is a test!"
        response = requests.post(
            "http://127.0.0.1:8003/chat", json={"prompt": test_prompt}
        )

        assert response.status_code == 200, (
            f"Chat endpoint returned {response.status_code}: {response.text}"
        )

        chat_data = response.json()
        print(f"Chat response: {chat_data}")
        response_content = chat_data.get("response", "")

        # Verify the response contains expected content
        assert "Hello, this is a test!" in response_content, (
            f"Response doesn't contain expected content. Expected: 'Hello from serve-test-agent!', Got: '{response_content}'"
        )

        if isinstance(maestro_cmd, str):
            cmd = [maestro_cmd, "run", agent_wow_file, workflow_wow_file]
        else:
            cmd = maestro_cmd + ["run", agent_wow_file, workflow_wow_file]

        print(f"Starting workflow with command: {' '.join(cmd)}")

        # Start the workflow
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=test_env
        )

        # Verify the response contains expected content
        assert str(result).find("remote_step2") != -1

        print("✅ All tests passed!")

    except Exception as e:
        print(f"Error during testing: {e}")
        raise

    finally:
        # Clean up
        print("Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("Server didn't stop gracefully, killing...")
            server_process.kill()
            server_process.wait()

            del os.environ["DRY_RUN"]


if __name__ == "__main__":
    try:
        test_wow_integration()
        print("Test completed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
