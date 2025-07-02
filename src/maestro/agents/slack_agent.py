#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from maestro.agents.agent import Agent

load_dotenv()


def post_message_to_slack(channel_id, message):
    """
    Posts a message to a specified Slack channel.

    Args:
        channel_id: The ID of the Slack channel to post to.
        message: The message text to send.
    """
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        print("Error: SLACK_BOT_TOKEN environment variable not set.")
        return

    client = WebClient(token=slack_token)

    try:
        result = client.chat_postMessage(channel=channel_id, text=message)
        print(f"Message posted to channel {channel_id}: {result['ts']}")
    except SlackApiError as e:
        print(f"Error posting message: {e}")


class SlackAgent(Agent):
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
        self.channel = os.getenv("SLACK_TEAM_ID", default="")

    async def run(self, prompt: str) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """

        self.print(f"Running {self.agent_name}...\n")
        answer = post_message_to_slack(self.channel, prompt)
        self.print(f"Response from {self.agent_name}: {answer}\n")

    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """

        self.print(f"Running {self.agent_name}...\n")
        answer = post_message_to_slack(self.channel, prompt)
        self.print(f"Response from {self.agent_name}: {answer}\n")
