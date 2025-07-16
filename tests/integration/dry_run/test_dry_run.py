#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import subprocess
import traceback
import unittest

from unittest import TestCase


def _maestro(*args) -> (str, int):
    """
    Calls maestro script using subprocess.

    Args:
        *args: Arguments to pass to the script.

    Returns:
        str: Output from the script.
    """
    try:
        result = subprocess.run(
            ["uv", "run", "maestro", *args], capture_output=True, text=True, check=True
        )
        return (result.stdout, 0)
    except subprocess.CalledProcessError as e:
        print(traceback.format_exc())
        return (f"Error: {e}", 1)


class TestCommand(TestCase):
    def setUp(self):
        self.agents_yaml_file = "tests/yamls/agents/simple_agent.yaml"
        self.workflow_yaml_file = "tests/yamls/workflows/simple_workflow.yaml"
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../..")
        )
        self.agent_schema_file = os.path.join(project_root, "schemas/agent_schema.json")
        self.workflow_schema_file = os.path.join(
            project_root, "schemas/workflow_schema.json"
        )

    def tearDown(self):
        self.agents_yaml_file = None
        self.workflow_yaml_file = None
        self.agent_schema_file = None
        self.workflow_schema_file = None


# CLI-level --dry-run integration tests
class DryRunIntegrationTest(TestCommand):
    def _validate(self, schema_file, yaml_file) -> (str, int):
        args = ["--dry-run", "validate", schema_file, yaml_file]
        return _maestro(*args)

    def _create(self, yaml_file) -> (str, int):
        args = ["--dry-run", "create", yaml_file]
        return _maestro(*args)

    def _run(self, agents_yaml_file, workflow_yaml_file) -> (str, int):
        args = ["--dry-run", "run", agents_yaml_file, workflow_yaml_file]
        return _maestro(*args)

    def test_validate_create_run(self):
        # validate agents yaml
        output, rc = self._validate(self.agent_schema_file, self.agents_yaml_file)
        self.assertTrue(
            rc == 0,
            f"`maestro validate --dry-run {self.agent_schema_file} {self.agents_yaml_file}`: rc: {rc} and output: {output}",
        )

        # validate workflow yaml
        output, rc = self._validate(self.workflow_schema_file, self.workflow_yaml_file)
        self.assertTrue(
            rc == 0,
            f"`maestro validate --dry-run {self.workflow_schema_file} {self.workflow_yaml_file}`: rc: {rc} and output: {output}",
        )

        # create agents yaml
        output, rc = self._create(self.agents_yaml_file)
        self.assertTrue(
            rc == 0,
            f"`maestro create --dry-run {self.agents_yaml_file}`: rc: {rc} and output: {output}",
        )

        # run agents workflow yaml
        output, rc = self._run(self.agents_yaml_file, self.workflow_yaml_file)
        self.assertTrue(
            rc == 0,
            f"`maestro run --dry-run {self.agents_yaml_file} {self.workflow_yaml_file}`: rc: {rc} and output: {output}",
        )


if __name__ == "__main__":
    unittest.main()
