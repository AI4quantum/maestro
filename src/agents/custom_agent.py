#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import sys
from typing import Any

from src.agents.agent import Agent
from src.agents.slack_agent import SlackAgent
from src.agents.metrics_agent import MetricsAgent

# adding a custom agent
# 1. add necessary import for the agent
# 2. add the custom agent name and class in the custom_agent map

# using a custom agent
# 1. set "custom" to "framework"
# 2  set the custom agent name to "metadata.labels.custom_agent"

custom_agent = { "slack_agent": SlackAgent, "metrics_agent": MetricsAgent}

class CustomAgent(Agent):
    """
    SlackAgent extends the Agent class to post messages to a slack channel.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified BeeAI agent.

        Args:
            agent_name (str): The name of the agent.
        """
        super().__init__(agent)
        
        self.custom_agent = agent["metadata"]["labels"].get("custom_agent")
        self.agent = (custom_agent[self.custom_agent])(agent)

    async def run(self, prompt: str) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        return await self.agent.run(prompt)

    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """

        return await self.agent.run_streaming(prompt)
