#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys

from dotenv import load_dotenv

from maestro.agents.agent import Agent

load_dotenv()


class CodeAgent(Agent):
    """
    CodeAgent extends the Agent class that executes an arbitrary python code specifed in the code section of the agent definition.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the agent with agent definitions.
        """
        super().__init__(agent)
        
        """
        Also install optional dependencies
        """
        if(self.agent_dependencies is not None and self.agent_dependencies != ""):
            self.print(f"Installing dependencies...\n")
            try:
                subprocess.check_call(["uv",  "pip", "install", "-r", self.agent_dependencies])
            except Exception as e:
                self.print(f"Exception executing code: {e}\n")
                raise e
        else:
            self.print(f"No dependencies found to install...\n")

    async def run(self, *args, context=None) -> str:
        """
        Execute the given code in the agent definition with the given prompt.
        Args:
            args: Argument list for the execution.
        """

        self.print(f"Running {self.agent_name} with {args}...\n")
        local = {"input": args, "output": {}}
        try:
            exec(self.agent_code, local)
        except Exception as e:
            self.print(f"Exception executing code: {e}\n")
            raise e
        answer = str(local["output"])
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return str(local["output"])

    async def run_streaming(self, *args, context=None) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """

        self.print(f"Running {self.agent_name} with {args}...\n")
        local = {"input": args, "output": {}}
        try:
            exec(self.agent_code, local)
        except Exception as e:
            self.print(f"Exception executing code: {e}\n")
            raise e
        answer = str(local["output"])
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return str(local["output"])
