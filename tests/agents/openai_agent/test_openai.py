#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os, dotenv, yaml
import asyncio

from unittest import TestCase
import pytest

from maestro.cli.common import parse_yaml

from maestro.workflow import Workflow
from maestro.agents.openai_agent import OpenAIAgent

dotenv.load_dotenv()

class OpenAIAgentMock:
    def __init__(self):
        pass

    async def run(self, prompt: str) -> str:
        return 'OK:'+prompt

def test_agent_runs(monkeypatch) -> None:
    # setup mocks
    mock_openai=OpenAIAgentMock()
    monkeypatch.setattr(OpenAIAgent, "__new__", lambda *args, **kwargs: mock_openai)

    agents_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"agents.yaml"))
    workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"workflow.yaml"))
    try:
        workflow = Workflow(agents_yaml, workflow_yaml[0])
    except Exception as excep:
        raise RuntimeError("Unable to create agents") from excep
    result = asyncio.run(workflow.run())
    print(result)

    assert result is not None
    assert result["final_prompt"].startswith("OK:Welcome") or result["final_prompt"].startswith("Mock agent")
