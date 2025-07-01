#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os, yaml, sys, io
import pytest
from unittest import TestCase
from maestro.workflow import Workflow

import asyncio

def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data

# `exception` tests
class TestException(TestCase):
    def tearDown(self):
        self.workflow = None

    def test_exception(self):
        self.agents_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/agents/simple_agent.yaml"))
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/exception_workflow.yaml"))
        self.workflow = Workflow(self.agents_yaml, self.workflow_yaml[0])
        output = io.StringIO()
        sys.stdout = output
        response = asyncio.run(self.workflow.run())
        assert "Running test4..." in output.getvalue()

    def test_exception_no_exception(self):
        self.agents_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/agents/simple_agent.yaml"))
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/exception_no_exception_workflow.yaml"))
        self.workflow = Workflow(self.agents_yaml, self.workflow_yaml[0])
        with pytest.raises(Exception) as exc_info:
                    asyncio.run(self.workflow.run())

        assert "Could not find agent named" in str(exc_info.value)



if __name__ == '__main__':
    unittest.main()
