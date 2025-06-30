#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import asyncio

from maestro.agents.prompt_agent import PromptAgent


def test_prompt_agent_returns_instruction_string():
    """
    Given spec.instructions as a single string,
    PromptAgent.run() should return that exact string.
    """
    agent_def = {
        "metadata": {"name": "test-prompt-agent", "labels": {}},
        "spec": {
            "framework": "custom",
            "model": "dummy",
            "description": "desc",
            "instructions": "This is a test instruction.",
        },
    }
    agent = PromptAgent(agent_def)
    result = asyncio.run(agent.run("ignored input"))
    assert isinstance(result, str)
    assert result == "This is a test instruction."


def test_prompt_agent_returns_instruction_list_joined():
    """
    Given spec.instructions as a list of strings,
    PromptAgent.run() should return them joined by newline.
    """
    instructions_list = [
        "First instruction line.",
        "Second instruction line.",
        "Third instruction.",
    ]
    agent_def = {
        "metadata": {"name": "test-prompt-agent", "labels": {}},
        "spec": {
            "framework": "custom",
            "model": "dummy",
            "description": "desc",
            "instructions": instructions_list,
        },
    }
    agent = PromptAgent(agent_def)
    result = asyncio.run(agent.run("anything"))
    expected = "\n".join(instructions_list)
    assert result == expected
