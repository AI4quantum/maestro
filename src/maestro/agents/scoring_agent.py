#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
from maestro.agents.agent import Agent
from opik.evaluation.metrics import AnswerRelevance, Hallucination
from opik import opik_context

from dotenv import load_dotenv

load_dotenv()


class ScoringAgent(Agent):
    """
    Agent that takes two inputs (prompt & response) plus an optional
    `context` list.  The response is always converted to a string before scoring.
    Metrics are printed, and the original response is returned.
    """

    def __init__(self, agent: dict) -> None:
        super().__init__(agent)
        self.name = agent.get("name", "scoring-agent")
        raw_model = agent["spec"]["model"]
        if raw_model.startswith("ollama/") or raw_model.startswith("openai/"):
            self._litellm_model = raw_model
        else:
            self._litellm_model = f"ollama/{raw_model}"

    async def run(
        self, prompt: str, response: str, context: list[str] | None = None
    ) -> any:
        """
        Args:
          prompt:   the original prompt
          response: the agent's output
          context:  optional list of strings to use as gold/context

        Note: The response only supports strings for now because Opik's evaluation passes in this as a json object.
        Currently anything else is unsupported, so we can avoid python crash but the Opik backend itself will fail.

        Returns:
          The original response (unchanged).  Metrics are printed to stdout.
        """
        assert isinstance(response, str), (
            f"ScoringAgent only supports string responses, got {type(response).__name__}"
        )
        response_text = response
        ctx = context or [prompt]

        # Temporarily disable Opik tracing so metric calls don't create traces
        original_disable = os.environ.get("OPIK_TRACK_DISABLE", "false")
        os.environ["OPIK_TRACK_DISABLE"] = "true"

        try:
            answer_relevance = AnswerRelevance(model=self._litellm_model)
            hallucination = Hallucination(model=self._litellm_model)
            rel = answer_relevance.score(prompt, response_text, context=ctx).value
            hall = hallucination.score(prompt, response_text, context=ctx).value
        finally:
            if original_disable == "false":
                os.environ.pop("OPIK_TRACK_DISABLE", None)
            else:
                os.environ["OPIK_TRACK_DISABLE"] = original_disable
        try:
            opik_context.update_current_trace(
                feedback_scores=[
                    {"name": "answer_relevance", "value": rel},
                    {"name": "hallucination", "value": hall},
                ],
                metadata={
                    "relevance": rel,
                    "hallucination": hall,
                    "model": self._litellm_model,
                    "agent": self.name,
                    "provider": "ollama",
                },
            )
        except Exception:
            pass

        metrics_line = f"relevance: {rel:.2f}, hallucination: {hall:.2f}"
        self.print(f"{response_text}\n[{metrics_line}]")

        return {
            "prompt": response_text,
            "scoring_metrics": {
                "relevance": rel,
                "hallucination": hall,
                "model": self._litellm_model,
                "agent": self.name,
                "provider": "ollama",
            },
        }
