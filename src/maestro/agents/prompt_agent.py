#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from maestro.agents.agent import Agent

from dotenv import load_dotenv

load_dotenv()


class PromptAgent(Agent):
    """
    Custom 'prompt_agent' that ignores the input response and instead
    returns the content of its own `spec.instructions` field as the output.
    """

    def __init__(self, agent_def: dict) -> None:
        # 1) Initialize the base class first so it can set up everything
        super().__init__(agent_def)

        # 2) Now safely pull out the instructions block from your YAML spec
        spec = agent_def.get("spec", {})
        raw_instr = spec.get("instructions", "")

        # 3) Normalize list vs string into a single string attribute
        if isinstance(raw_instr, list):
            self.instructions = "\n".join(raw_instr)
        else:
            self.instructions = raw_instr or ""

    async def run(self, response: str) -> str:
        """
        Args:
          response: the output string from the previous workflow step (ignored)

        Returns:
          The content of spec.instructions, exactly as defined in the agent YAML.
        """
        print(self.instructions)
        return self.instructions
