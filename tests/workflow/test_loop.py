#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os, yaml
import pytest
from unittest import TestCase
from maestro.workflow import Workflow

import asyncio

def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data

# `loop` tests
class TestLoop(TestCase):
    def setUp(self):
        self.agents_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/agents/dry_run_loop_agent.yaml"))
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/loop_workflow.yaml"))
        try:
            self.workflow = Workflow(self.agents_yaml, self.workflow_yaml[0])
        except Exception as excep:
            raise RuntimeError("Unable to create agents") from excep

    def tearDown(self):
        self.workflow = None

    def test_loop(self):
        response = asyncio.run(self.workflow.run())
        assert "happy" in response["final_prompt"]

class TestLoopList(TestCase):
    def setUp(self):
        self.agents_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/agents/dry_run_loop_list_agent.yaml"))
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/loop_workflow.yaml"))
        try:
            self.workflow = Workflow(self.agents_yaml, self.workflow_yaml[0])
        except Exception as excep:
            raise RuntimeError("Unable to create agents") from excep

    def tearDown(self):
        self.workflow = None

    def test_loop(self):
        response = asyncio.run(self.workflow.run())
        assert "['This', 'is', 'a', 'test', 'for', 'loop']" in response["final_prompt"]

if __name__ == '__main__':
    unittest.main()
