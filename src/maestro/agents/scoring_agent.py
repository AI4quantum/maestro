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
            answer_relevance = AnswerRelevance(model="ollama/qwen3")
            hallucination = Hallucination(model="ollama/qwen3")

            rel_eval = answer_relevance.score(prompt, response_text, context=ctx)
            hall_eval = hallucination.score(prompt, response_text, context=ctx)

            rel_value = rel_eval.value
            hall_value = hall_eval.value
            rel_reason_raw = rel_eval.reason
            hall_reason_raw = hall_eval.reason
            rel_reason = (
                ", ".join(rel_reason_raw)
                if isinstance(rel_reason_raw, (list, tuple))
                else rel_reason_raw or ""
            )
            hall_reason = (
                ", ".join(hall_reason_raw)
                if isinstance(hall_reason_raw, (list, tuple))
                else hall_reason_raw or ""
            )
        finally:
            if original_disable == "false":
                os.environ.pop("OPIK_TRACK_DISABLE", None)
            else:
                os.environ["OPIK_TRACK_DISABLE"] = original_disable

        # Log the metrics to the current trace instead of creating new traces
        try:
            opik_context.update_current_trace(
                feedback_scores=[
                    {"name": "answer_relevance", "value": rel_value},
                    {"name": "hallucination", "value": hall_value},
                ],
                metadata={
                    "relevance": rel_value,
                    "relevance_reason": rel_reason,
                    "hallucination": hall_value,
                    "hallucination_reason": hall_reason,
                    "model": self._litellm_model,
                    "agent": self.name,
                    "provider": "ollama",
                },
            )
        except Exception:
            pass

        faithfulness_score = 1.0 - hall_value
        metrics_line = f"relevance: {rel_value:.2f}, hallucination: {hall_value:.2f} (faithfulness: {faithfulness_score:.2f})"
        self.print(f"{response_text}\n[{metrics_line}]")

        return {
            "prompt": response_text,
            "scoring_metrics": {
                "relevance": rel_value,
                "hallucination": hall_value,
                "faithfulness": faithfulness_score,
                "relevance_reason": rel_reason,
                "hallucination_reason": hall_reason,
                "model": self._litellm_model,
                "agent": self.name,
                "provider": "ollama",
            },
        }
