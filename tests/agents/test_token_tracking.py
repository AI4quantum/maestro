#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import asyncio
import pytest
import litellm

from maestro.agents.scoring_agent import ScoringAgent
from maestro.agents.utils import TokenUsageExtractor
from maestro.utils import aggregate_token_usage_from_agents
from opik.evaluation.metrics import AnswerRelevance, Hallucination


@pytest.fixture(autouse=True)
def patch_litellm_provider(monkeypatch):
    monkeypatch.setattr(
        litellm,
        "get_llm_provider",
        lambda model_name, **kwargs: (model_name, "openai", None, None),
    )


def test_scoring_agent_token_usage():
    """Test that scoring agent returns appropriate token usage information."""
    agent_def = {
        "metadata": {"name": "score_agent", "labels": {}},
        "spec": {
            "framework": "custom",
            "model": "qwen3:latest",
            "description": "desc",
            "instructions": "instr",
        },
    }
    agent = ScoringAgent(agent_def)

    token_usage = agent.get_token_usage()

    # Scoring agent should return descriptive information, not actual token counts
    assert isinstance(token_usage, dict)
    assert "agent_type" in token_usage
    assert token_usage["agent_type"] == "scoring_agent"
    assert "description" in token_usage


def test_token_usage_extractor():
    """Test the TokenUsageExtractor utility class."""

    class MockUsage:
        def __init__(self, prompt_tokens=10, completion_tokens=20, total_tokens=30):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.total_tokens = total_tokens

    class MockResult:
        def __init__(self, usage=None):
            self.usage = usage

    mock_usage = MockUsage(15, 25, 40)
    mock_result = MockResult(mock_usage)

    printed_messages = []

    def mock_print(msg):
        printed_messages.append(msg)

    result = TokenUsageExtractor.extract_from_result(
        mock_result, "TestAgent", mock_print
    )

    assert result["prompt_tokens"] == 15
    assert result["response_tokens"] == 25
    assert result["total_tokens"] == 40
    assert len(printed_messages) == 1
    assert "Extracted token usage from result" in printed_messages[0]


def test_token_usage_extractor_direct_attributes():
    """Test TokenUsageExtractor with direct token attributes."""

    class MockResult:
        def __init__(self):
            self.prompt_tokens = 5
            self.completion_tokens = 10
            self.total_tokens = 15

    mock_result = MockResult()

    printed_messages = []

    def mock_print(msg):
        printed_messages.append(msg)

    result = TokenUsageExtractor.extract_from_result(
        mock_result, "TestAgent", mock_print
    )

    assert result["prompt_tokens"] == 5
    assert result["response_tokens"] == 10
    assert result["total_tokens"] == 15
    assert len(printed_messages) == 1
    assert "Found token usage in result" in printed_messages[0]


def test_token_usage_extractor_no_tokens():
    """Test TokenUsageExtractor with object that has no token usage."""

    class MockResult:
        pass

    mock_result = MockResult()

    result = TokenUsageExtractor.extract_from_result(mock_result, "TestAgent", None)

    assert result["prompt_tokens"] == 0
    assert result["response_tokens"] == 0
    assert result["total_tokens"] == 0


def test_aggregate_token_usage_from_agents():
    """Test the aggregate_token_usage_from_agents utility function."""

    class MockAgent:
        def __init__(self, name, token_usage):
            self.name = name
            self._token_usage = token_usage

        def get_token_usage(self):
            return self._token_usage

    class MockAgentNoTokens:
        def __init__(self, name):
            self.name = name

    agents = {
        "llm_agent": MockAgent(
            "llm_agent",
            {"prompt_tokens": 10, "response_tokens": 20, "total_tokens": 30},
        ),
        "scoring_agent": MockAgent(
            "scoring_agent",
            {
                "agent_type": "scoring_agent",
                "description": "Uses Opik evaluation metrics",
            },
        ),
        "no_tokens_agent": MockAgentNoTokens("no_tokens_agent"),
    }

    result = aggregate_token_usage_from_agents(agents)
    assert result["total_prompt_tokens"] == 10
    assert result["total_response_tokens"] == 20
    assert result["total_tokens"] == 30

    assert "llm_agent" in result["agent_token_usage"]
    assert "scoring_agent" in result["agent_token_usage"]
    assert "no_tokens_agent" not in result["agent_token_usage"]
    assert result["agent_token_usage"]["llm_agent"]["prompt_tokens"] == 10
    assert result["agent_token_usage"]["scoring_agent"]["agent_type"] == "scoring_agent"


def test_aggregate_token_usage_empty():
    """Test aggregate_token_usage_from_agents with empty agents dict."""
    result = aggregate_token_usage_from_agents({})

    assert result["total_prompt_tokens"] == 0
    assert result["total_response_tokens"] == 0
    assert result["total_tokens"] == 0
    assert result["agent_token_usage"] == {}


def test_aggregate_token_usage_multiple_llm_agents():
    """Test aggregate_token_usage_from_agents with multiple LLM agents."""

    class MockAgent:
        def __init__(self, name, token_usage):
            self.name = name
            self._token_usage = token_usage

        def get_token_usage(self):
            return self._token_usage

    agents = {
        "agent1": MockAgent(
            "agent1", {"prompt_tokens": 5, "response_tokens": 10, "total_tokens": 15}
        ),
        "agent2": MockAgent(
            "agent2", {"prompt_tokens": 8, "response_tokens": 12, "total_tokens": 20}
        ),
        "agent3": MockAgent(
            "agent3", {"prompt_tokens": 3, "response_tokens": 7, "total_tokens": 10}
        ),
    }

    result = aggregate_token_usage_from_agents(agents)

    assert result["total_prompt_tokens"] == 16
    assert result["total_response_tokens"] == 29
    assert result["total_tokens"] == 45

    assert len(result["agent_token_usage"]) == 3
    assert "agent1" in result["agent_token_usage"]
    assert "agent2" in result["agent_token_usage"]
    assert "agent3" in result["agent_token_usage"]


def test_scoring_agent_integration():
    """Test scoring agent integration with token tracking."""

    class DummyScore:
        def __init__(self, value):
            self.value = value
            self.reason = "Test reason"
            self.metadata = {}

    def fake_rel(self, input, output, context):
        return DummyScore(0.50)

    def fake_hall(self, input, output, context):
        return DummyScore(0.20)

    with pytest.MonkeyPatch().context() as m:
        m.setattr(AnswerRelevance, "score", fake_rel)
        m.setattr(Hallucination, "score", fake_hall)

        agent_def = {
            "metadata": {"name": "score_agent", "labels": {}},
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

        assert isinstance(out, dict)
        assert out["prompt"] == response
        assert "scoring_metrics" in out

        token_usage = agent.get_token_usage()
        assert isinstance(token_usage, dict)
        assert token_usage["agent_type"] == "scoring_agent"
