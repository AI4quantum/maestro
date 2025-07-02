#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import asyncio
import pytest
import litellm

from maestro.agents.scoring_agent import ScoringAgent
from opik.evaluation.metrics import AnswerRelevance, Hallucination


@pytest.fixture(autouse=True)
def patch_litellm_provider(monkeypatch):
    monkeypatch.setattr(
        litellm,
        "get_llm_provider",
        lambda model_name, **kwargs: (model_name, "openai", None, None),
    )


def test_metrics_agent_run_with_context(monkeypatch):
    seen = {"relevance": None, "hallucination": None}

    class DummyScore:
        def __init__(self, value):
            self.value = value

    def fake_rel(self, input, output, context):
        seen["relevance"] = context
        return DummyScore(0.50)

    def fake_hall(self, input, output, context):
        seen["hallucination"] = context
        return DummyScore(0.20)

    monkeypatch.setattr(AnswerRelevance, "score", fake_rel)
    monkeypatch.setattr(Hallucination, "score", fake_hall)

    printed = []
    monkeypatch.setattr(ScoringAgent, "print", lambda self, msg: printed.append(msg))

    agent_def = {
        "metadata": {"name": "metrics_agent", "labels": {}},
        "spec": {
            "framework": "custom",
            "model": "qwen3:latest",
            "description": "desc",
            "instructions": "instr",
        },
    }
    agent = ScoringAgent(agent_def)
    prompt = "What is the capital of France?"
    response = "Lyon"
    context = ["Paris is the capital of France."]
    out = asyncio.run(agent.run(prompt, response, context=context))

    assert out == response

    assert seen["relevance"] is context
    assert seen["hallucination"] is context

    assert len(printed) == 1
    assert printed[0] == "Lyon\n[relevance: 0.50, hallucination: 0.20]"
