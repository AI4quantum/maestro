#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import asyncio
from dotenv import load_dotenv

from unittest import TestCase

from maestro.cli.common import parse_yaml

from maestro.workflow import Workflow

load_dotenv()


class CrewAITest(TestCase):
    def test_agent_runs(self) -> None:
        agents_yaml = parse_yaml(os.path.join(os.path.dirname(__file__), "agents.yaml"))
        workflow_yaml = parse_yaml(
            os.path.join(os.path.dirname(__file__), "workflow.yaml")
        )

        try:
            workflow = Workflow(agents_yaml, workflow_yaml[0])
        except Exception as excep:
            raise RuntimeError("Unable to create agents") from excep

        result = asyncio.run(workflow.run())
        print(result)

        assert result is not None
        assert result["final_prompt"] == "OK"


if __name__ == "__main__":
    crewtest = CrewAITest()
    crewtest.test_agent_runs()
