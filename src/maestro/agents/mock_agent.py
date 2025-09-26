#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0


from dotenv import load_dotenv

from .agent import Agent
from .evaluation_middleware import auto_evaluate_response

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

    async def run(self, prompt: str, context=None, step_index=None) -> str:
        """
        Runs the bee agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        print(f"🤖 Running {self.agent_name}...")
        answer = f"Mock agent: answer for {prompt}"
        if self.instructions:
            answer = eval_expression(self.instructions, prompt)

        # Automatic evaluation middleware
        # For POC: provide mock context if none exists to test faithfulness evaluation
        test_context = (
            context
            or "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. It uses algorithms to identify patterns in data and make predictions or classifications."
        )

        await auto_evaluate_response(
            agent_name=self.agent_name,
            prompt=prompt,
            response=answer,
            context=test_context,
            step_index=step_index,
        )

        print(f"🤖 Response from {self.agent_name}: {answer}")
        return answer

    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        print(f"🤖 Running {self.agent_name}...")
        answer = f"Mock agent: answer for {prompt}"

        # Automatic evaluation middleware (same as run method)
        await auto_evaluate_response(
            agent_name=self.agent_name, prompt=prompt, response=answer
        )

        print(f"🤖 Response from {self.agent_name}: {answer}")
        return answer
