#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import pytest
import os
import unittest
import yaml
import asyncio
from maestro.agents.code_agent import CodeAgent


class TestCodeAgentDependencies(unittest.IsolatedAsyncioTestCase):
    """Test the dependency installation feature of the CodeAgent class."""

    def setUp(self):
        """Set up the test environment."""
        # Path to the example agent definition
        self.example_agent_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "tests",
            "examples",
            "code_agent_with_dependencies.yaml",
        )

        # Load the example agent definition
        with open(self.example_agent_path, "r") as f:
            self.agent_def = yaml.safe_load(f)

        self.example_agent_requirements_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "tests",
            "examples",
            "code_agent_with_dependencies_requirements.yaml",
        )

        # Load the example agent definition
        with open(self.example_agent_requirements_path, "r") as f:
            self.agent_requirements_def = yaml.safe_load(f)

    def tearDown(self):
        """Reinstall dependencies after tests."""
        # Create a CodeAgent instance with the example agent definition
        agent = CodeAgent(self.agent_def)

        # Reinstall dependencies
        agent._install_dependencies()

    def test_missing_dependencies(self):
        """Test that code execution fails when dependencies are missing."""
        # Create a copy of the agent definition with code that imports a non-existent module
        agent_def_no_deps = self.agent_def.copy()
        agent_def_no_deps["metadata"]["dependencies"] = ""
        agent_def_no_deps["spec"]["code"] = """
# Import a module that definitely doesn't exist
import nonexistent_module_for_testing

# This code should never run
output = "This should not be returned"
"""

        # Create a CodeAgent instance with the modified agent definition
        agent = CodeAgent(agent_def_no_deps)

        # Run the agent - this should fail because the module doesn't exist
        # and won't be installed because dependencies is empty
        with self.assertRaises(Exception) as context:
            asyncio.run(agent.run("https://www.example.com"))

        # Verify the exception is related to missing modules
        error_msg = str(context.exception)
        self.assertTrue(
            "ModuleNotFoundError" in error_msg
            or "ImportError" in error_msg
            or "No module named" in error_msg,
            f"Expected import error, got: {error_msg}",
        )

    @pytest.mark.asyncio
    async def test_dependencies_installation(self):
        """Test that dependencies are installed before code execution."""
        # Create a CodeAgent instance with the example agent definition
        agent = CodeAgent(self.agent_def)

        # Actually run the agent with the example URL
        result = await agent.run("https://www.example.com")

        # Check that the code executed successfully and returned a result
        self.assertIsNotNone(result)
        self.assertEqual(result, "Example Domain")

    @pytest.mark.asyncio
    async def test_dependencies_installation_requirements_file(self):
        """Test that dependencies are installed before code execution."""
        # Create a CodeAgent instance with the example agent definition
        print(self.agent_requirements_def)
        agent = CodeAgent(self.agent_requirements_def)

        # Actually run the agent with the example URL
        result = await agent.run("https://www.example.com")

        # Check that the code executed successfully and returned a result
        self.assertIsNotNone(result)
        self.assertEqual(result, "Example Domain")

    @pytest.mark.asyncio
    async def test_dependencies_installation_streaming(self):
        """Test that dependencies are installed before code execution."""
        # Create a CodeAgent instance with the example agent definition
        agent = CodeAgent(self.agent_def)

        # Actually run the agent with the example URL
        result = await agent.run_streaming("https://www.example.com")

        # Check that the code executed successfully and returned a result
        self.assertIsNotNone(result)
        self.assertEqual(result, "Example Domain")


if __name__ == "main":
    asyncio.run(unittest.main())
