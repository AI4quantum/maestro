#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0


from dotenv import load_dotenv

from .agent import Agent

load_dotenv()


def eval_expression(expression, prompt):
    local = {}
    local["input"] = prompt
    try:
        exec(expression, local)
    except Exception:
        print("mock exception")
    return local["input"]


class MockAgent(Agent):
    """
    MockAgent extends the Agent class to load and run a specific agent.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified mock agent.

        Args:
            agent_name (str): The name of the agent.
        """
        super().__init__(agent)
        self.agent_tools = []

        tools = agent["spec"].get("tools")
        if tools:
            for tool in tools:
                print(f"Mock agent:Loading {tool}")

        print(
            f"🤖 Mock agent: name={self.agent_name}, model={self.agent_model}, description={self.agent_desc}, tools={self.agent_tools}, instructions={self.instructions}"
        )
        self.agent_id = self.agent_name

    async def run(self, prompt: str) -> str:
        """
        Runs the bee agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        print(f"🤖 Running {self.agent_name}...")
        answer = f"Mock agent: answer for {prompt}"
        if self.instructions:
            answer = eval_expression(self.instructions, prompt)
        print(f"🤖 Response from {self.agent_name}: {answer}")
        return answer

    def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        print(f"🤖 Running {self.agent_name}...")
        answer = f"Mock agent: answer for {prompt}"
        print(f"🤖 Response from {self.agent_name}: {answer}")
        return answer
