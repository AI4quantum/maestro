#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from maestro.agents.agent import Agent
from opik.evaluation.metrics import AnswerRelevance, Hallucination

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

        try:
            rel_res = AnswerRelevance(model=self._litellm_model).score(
                input=prompt, output=response_text, context=ctx
            )
            hall_res = Hallucination(model=self._litellm_model).score(
                input=prompt, output=response_text, context=ctx
            )

            rel = getattr(rel_res, "value", rel_res)
            hall = getattr(hall_res, "value", hall_res)

            metrics_line = f"relevance: {rel:.2f}, hallucination: {hall:.2f}"
            self.print(f"{response_text}\n[{metrics_line}]")
        except Exception as e:
            self.print(f"[ScoringAgent] Warning: could not calculate metrics: {e}")

        return response
