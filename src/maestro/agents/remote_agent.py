#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json
from string import Template

import dotenv
import requests
from requests import RequestException

from maestro.agents.agent import Agent

dotenv.load_dotenv()


class RemoteAgent(Agent):
    """
    RemoteAgent extends the Agent class to load and run a specific agent.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified agent.

        Args:
            agent_name (str): The name of the agent.
        """
        super().__init__(agent)
        self.url = agent["spec"]["url"]
        self.request_template = agent["spec"]["request_template"]
        self.response_template = agent["spec"]["response_template"]

    async def run(self, prompt: str) -> str:
        """
        Runs the agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        print(f"👩🏻‍💻 Running {self.agent_name}...\n")
        try:
            if self.request_template is not None:
                json_str = Template(self.request_template).safe_substitute(
                    prompt=prompt
                )
                data = json.loads(json_str)
            else:
                data = {"prompt": prompt}
            print("❓ ", prompt)
            response = requests.post(self.url, json=data)
            response.raise_for_status()
            result = Template(self.response_template).safe_substitute(
                response="response.json()"
            )
            answer = eval(result)
            print("🤖 ", answer)
            return answer or json.dumps(response.json())
        except RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        pass
