#!/usr/bin/env python3
"""
Test script for the Maestro Builder API
"""

import requests

API_BASE_URL = "http://localhost:5174"


def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✓ Root endpoint working")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the server is running.")
        return False
    return True


def test_chat_builder_agent():
    """Test the chat builder agent endpoint"""
    print("\nTesting chat builder agent...")
    try:
        payload = {"content": "Create an OpenAI agent for text summarization"}
        response = requests.post(
            f"{API_BASE_URL}/api/chat_builder_agent",
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ Chat builder agent working")
            print(f"  Response: {data['response'][:100]}...")
            print(f"  YAML files: {len(data['yaml_files'])} files")
            return data.get("yaml_files", [])
        else:
            print(f"✗ Chat builder agent failed: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Chat builder agent error: {e}")
    return []


def test_get_yamls(chat_id):
    """Test the get YAMLs endpoint"""
    print(f"\nTesting get YAMLs for chat {chat_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/get_yamls/{chat_id}")

        if response.status_code == 200:
            data = response.json()
            print("✓ Get YAMLs working")
            print(f"  YAML files: {len(data)} files")
            for yaml_file in data:
                print(f"    - {yaml_file['name']}: {len(yaml_file['content'])} chars")
        else:
            print(f"✗ Get YAMLs failed: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Get YAMLs error: {e}")


def test_chat_history():
    """Test the chat history endpoint"""
    print("\nTesting chat history...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/chat_history")

        if response.status_code == 200:
            data = response.json()
            print("✓ Chat history working")
            print(f"  Chat sessions: {len(data)}")
            for chat in data:
                print(f"    - {chat['name']}: {chat['message_count']} messages")
        else:
            print(f"✗ Chat history failed: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Chat history error: {e}")


def test_api_docs():
    """Test if API documentation is accessible"""
    print("\nTesting API documentation...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("✓ API documentation accessible")
        else:
            print(f"✗ API documentation failed: {response.status_code}")
    except Exception as e:
        print(f"✗ API documentation error: {e}")


def main():
    """Run all tests"""
    print("Maestro Builder API Test Suite")
    print("=" * 40)

    # Test root endpoint first
    if not test_root_endpoint():
        print("\nAPI server is not running. Please start it first:")
        print("cd api && python main.py")
        return

    # Test API documentation
    test_api_docs()

    # Test chat functionality
    yaml_files = test_chat_builder_agent()

    # If we got YAML files, test the get_yamls endpoint
    if yaml_files:
        # Extract chat_id from the response (this would need to be implemented)
        # For now, we'll use a placeholder
        test_get_yamls("test-chat-id")

    # Test chat history
    test_chat_history()

    print("\n" + "=" * 40)
    print("Test suite completed!")


if __name__ == "__main__":
    main()
