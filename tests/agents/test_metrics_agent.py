#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import asyncio
import pytest
import litellm

from src.agents.metrics_agent import MetricsAgent
from opik.evaluation.metrics import AnswerRelevance, Hallucination

# Auto-patch Litellm provider resolution to accept any model
@pytest.fixture(autouse=True)
def patch_litellm_provider(monkeypatch):
    monkeypatch.setattr(
        litellm, "get_llm_provider",
        lambda model_name, **kwargs: (model_name, "openai", None, None)
    )


def test_metrics_agent_run_returns_original_and_prints(monkeypatch):
    # Stub scoring to fixed values
    class DummyScore:
        def __init__(self, value):
            self.value = value
    monkeypatch.setattr(
        AnswerRelevance, "score",
        lambda self, input, output, context: DummyScore(0.75)
    )
    monkeypatch.setattr(
        Hallucination, "score",
        lambda self, input, output, context: DummyScore(0.25)
    )

    printed = []
    monkeypatch.setattr(MetricsAgent, "print", lambda self, msg: printed.append(msg))

    agent_def = {
        "metadata": {"name": "metrics_agent", "labels": {}},
        "spec": {
            "framework":    "custom",
            "model":        "qwen3:latest",
            "description":  "desc",
            "instructions": "instr"
        }
    }
    agent = MetricsAgent(agent=agent_def)

    # Invoke run()
    original = "Test response"
    output = asyncio.run(agent.run(original))

    # Return value should be the original response
    assert isinstance(output, str)
    assert output == original


    assert len(printed) == 1, "Expected one print call for metrics"
    printed_msg = printed[0]
    assert original in printed_msg
    assert "relevance: 0.75" in printed_msg
    assert "hallucination: 0.25" in printed_msg
