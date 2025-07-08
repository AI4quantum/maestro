#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import yaml
import io
import sys
import unittest
from unittest import TestCase
from maestro.workflow import Workflow
import asyncio


def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data


# `code` tests
class TestCode(TestCase):
    def setUp(self):
        self.agents_yaml = parse_yaml(
            os.path.join(os.path.dirname(__file__), "../yamls/agents/code_agent.yaml")
        )
        self.workflow_yaml = parse_yaml(
            os.path.join(
                os.path.dirname(__file__), "../yamls/workflows/code_workflow.yaml"
            )
        )
        try:
            self.workflow = Workflow(self.agents_yaml, self.workflow_yaml[0])
        except Exception as excep:
            raise RuntimeError("Unable to create agents") from excep

    def tearDown(self):
        self.workflow = None

    def test_code(self):
        response = asyncio.run(self.workflow.run())
        if os.getenv("DRY_RUN") and os.getenv("DRY_RUN") != "":
            assert "Hello code" in response["final_prompt"]
        else:
            assert "Hi!" in response["final_prompt"]


class TestExeptionCode(TestCase):
    def setUp(self):
        self.agents_yaml = parse_yaml(
            os.path.join(
                os.path.dirname(__file__), "../yamls/agents/code_exception_agent.yaml"
            )
        )
        self.workflow_yaml = parse_yaml(
            os.path.join(
                os.path.dirname(__file__),
                "../yamls/workflows/code_exception_workflow.yaml",
            )
        )
        try:
            self.workflow = Workflow(self.agents_yaml, self.workflow_yaml[0])
        except Exception as excep:
            raise RuntimeError("Unable to create agents") from excep

    def tearDown(self):
        self.workflow = None

    def test_code(self):
        output = io.StringIO()
        sys.stdout = output
        response = asyncio.run(self.workflow.run())
        if os.getenv("DRY_RUN") and os.getenv("DRY_RUN") != "":
            assert "Hello code" in response["final_prompt"]
        else:
            assert (
                "Response from test1: name 'oops' is not defined" in output.getvalue()
            )


if __name__ == "__main__":
    unittest.main()
