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


def test_serve_integration():
    """Test the serve functionality with a real server."""
    print("Starting serve integration test...")

    # Temporarily save and unset DRY_RUN (other tests might set it)
    original_dry_run = os.environ.get("DRY_RUN")
    if "DRY_RUN" in os.environ:
        print(
            "Temporarily unsetting DRY_RUN environment variable to prevent test interference"
        )
        del os.environ["DRY_RUN"]

    # Find the test agent file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(test_dir)))
    agent_file = os.path.join(
        project_root, "tests", "yamls", "agents", "serve_test_agent.yaml"
    )

    assert os.path.exists(agent_file), f"Agent file not found at {agent_file}"

    # Find maestro executable
    maestro_cmd = find_maestro_executable()
    if isinstance(maestro_cmd, str):
        cmd = [
            maestro_cmd,
            "serve",
            agent_file,
            "--port",
            "8001",
            "--host",
            "127.0.0.1",
        ]
    else:
        cmd = maestro_cmd + [
            "serve",
            agent_file,
            "--port",
            "8001",
            "--host",
            "127.0.0.1",
        ]

    print(f"Starting server with command: {' '.join(cmd)}")

    # Start the server
    server_process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    try:
        # Wait for server to start
        print("Waiting for server to start...")
        assert wait_for_server("http://127.0.0.1:8001"), (
            "Server failed to start within timeout"
        )

        print("Server is ready!")

        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8001/health")
        assert response.status_code == 200, (
            f"Health endpoint returned {response.status_code}"
        )

        health_data = response.json()
        print(f"Health check response: {health_data}")

        # Test agents endpoint
        print("Testing agents endpoint...")
        response = requests.get("http://127.0.0.1:8001/agents")
        assert response.status_code == 200, (
            f"Agents endpoint returned {response.status_code}"
        )

        agents_data = response.json()
        print(f"Agents response: {agents_data}")

        # Test chat endpoint
        print("Testing chat endpoint...")
        test_prompt = "Hello, this is a test!"
        response = requests.post(
            "http://127.0.0.1:8001/chat", json={"prompt": test_prompt, "stream": False}
        )

        assert response.status_code == 200, (
            f"Chat endpoint returned {response.status_code}: {response.text}"
        )

        chat_data = response.json()
        print(f"Chat response: {chat_data}")
        response_content = chat_data.get("response", "")

        # Verify the response contains expected content
        assert "Hello from serve-test-agent!" in response_content, (
            f"Response doesn't contain expected content. Expected: 'Hello from serve-test-agent!', Got: '{response_content}'"
        )

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

        # Restore DRY_RUN environment variable
        if original_dry_run is not None:
            print("Restoring DRY_RUN environment variable")
            os.environ["DRY_RUN"] = original_dry_run
        elif "DRY_RUN" in os.environ:
            # If we unset it but it wasn't originally set, remove it again
            del os.environ["DRY_RUN"]


def test_serve_workflow_integration():
    """Test the serve functionality with a real server."""
    print("Starting serve integration test...")

    # Find the test agent file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(test_dir)))
    agent_file = os.path.join(project_root, "tests", "yamls", "agents", "simple_agent.yaml")
    workflow_file = os.path.join(project_root, "tests", "yamls", "workflows", "simple_workflow.yaml")

    assert os.path.exists(agent_file), f"Agent file not found at {agent_file}"
    assert os.path.exists(workflow_file), f"Workflow file not found at {workflow_file}"

    # Find maestro executable
    maestro_cmd = find_maestro_executable()
    if isinstance(maestro_cmd, str):
        cmd = [maestro_cmd, "serve", agent_file, workflow_file, "--port", "8002", "--host", "127.0.0.1"]
    else:
        cmd = maestro_cmd + ["serve", agent_file, workflow_file, "--port", "8002", "--host", "127.0.0.1"]

    print(f"Starting server with command: {' '.join(cmd)}")

    # Start the server
    test_env = os.environ.copy()
    test_env["DRY_RUN"] = "1"
    server_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=test_env
    )

    try:
        original_dry_run = os.environ.get("DRY_RUN")
        os.environ["DRY_RUN"] = "1"
        # Wait for server to start
        print("Waiting for server to start...")
        assert wait_for_server("http://127.0.0.1:8002"), "Server failed to start within timeout"

        print("Server is ready!")

        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8002/health")
        assert response.status_code == 200, f"Health endpoint returned {response.status_code}"

        health_data = response.json()
        print(f"Health check response: {health_data}")

        # Test chat endpoint
        print("Testing chat endpoint...")
        test_prompt = "Hello, this is a test!"
        response = requests.post(
            "http://127.0.0.1:8002/chat",
            json={"prompt": test_prompt, "stream": False}
        )

        assert response.status_code == 200, f"Chat endpoint returned {response.status_code}: {response.text}"

        chat_data = response.json()
        print(f"Chat response: {chat_data}")
        response_content = chat_data.get("response", "")

        # Verify the response contains expected content
        assert "Hello, this is a test!" in response_content, (
            f"Response doesn't contain expected content. Expected: 'Hello from serve-test-agent!', Got: '{response_content}'"
        )

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
        test_serve_integration()
        test_serve_workflow_integration()
        print("Test completed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
