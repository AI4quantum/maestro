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

        scoring_metrics = self._calculate_metrics(prompt, response_text, ctx)
        if scoring_metrics is None:
            return {"prompt": response_text, "scoring_metrics": None}

        self._log_metrics_to_trace(scoring_metrics)
        self._print_metrics(response_text, scoring_metrics)
        return self._format_response(response_text, scoring_metrics)

    def _calculate_metrics(
        self, prompt: str, response_text: str, context: list[str]
    ) -> dict | None:
        """Calculate relevance and hallucination metrics for the response."""
        os.environ["OPIK_TRACK_DISABLE"] = "true"

        try:
            answer_relevance = AnswerRelevance(model=self._litellm_model)
            hallucination = Hallucination(model=self._litellm_model)

            rel_eval = answer_relevance.score(prompt, response_text, context=context)
            hall_eval = hallucination.score(prompt, response_text, context=context)

            rel_value = rel_eval.value
            hall_value = hall_eval.value
            rel_reason = self._normalize_reason(rel_eval.reason)
            hall_reason = self._normalize_reason(hall_eval.reason)

            return {
                "relevance": rel_value,
                "hallucination": hall_value,
                "relevance_reason": rel_reason,
                "hallucination_reason": hall_reason,
            }
        except Exception as e:
            self.print(f"[ScoringAgent] Warning: could not calculate metrics: {e}")
            return None

    def _normalize_reason(self, reason_raw) -> str:
        """Normalize the reason field from Opik metrics into a string."""
        if isinstance(reason_raw, (list, tuple)):
            return ", ".join(reason_raw)
        return reason_raw or ""

    def _log_metrics_to_trace(self, scoring_metrics: dict) -> None:
        """Log scoring metrics to the current Opik trace."""
        try:
            opik_context.update_current_trace(
                feedback_scores=[
                    {"name": "answer_relevance", "value": scoring_metrics["relevance"]},
                    {
                        "name": "hallucination",
                        "value": scoring_metrics["hallucination"],
                    },
                ],
                metadata={
                    "relevance": scoring_metrics["relevance"],
                    "relevance_reason": scoring_metrics["relevance_reason"],
                    "hallucination": scoring_metrics["hallucination"],
                    "hallucination_reason": scoring_metrics["hallucination_reason"],
                    "model": self._litellm_model,
                    "agent": self.name,
                    "provider": "ollama",
                },
            )
        except Exception:
            pass

    def _print_metrics(self, response_text: str, scoring_metrics: dict) -> None:
        """Print the scoring metrics to stdout."""
        metrics_line = f"relevance: {scoring_metrics['relevance']:.2f}, hallucination: {scoring_metrics['hallucination']:.2f}"
        self.print(f"{response_text}\n[{metrics_line}]")

    def _format_response(self, response_text: str, scoring_metrics: dict) -> dict:
        """Format the final response with scoring metrics."""
        return {
            "prompt": response_text,
            "scoring_metrics": {
                **scoring_metrics,
                "model": self._litellm_model,
                "agent": self.name,
                "provider": "ollama",
            },
        }
