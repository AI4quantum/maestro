#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
import os
import pickle
import json
from typing import Dict, Final


class Agent:
    """
    Abstract base class for running agents.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the AgentRunner with the given agent configuration.
        Args:
            agent_name (str): The name of the agent.
        """
        # TODO: Review which attributes belong in base class vs subclasses
        self.agent_name = agent["metadata"]["name"]
        self.agent_framework = agent["spec"]["framework"]
        self.agent_model = agent["spec"].get("model")

        self.agent_tools = agent["spec"].get("tools", [])

        self.agent_desc = agent["spec"].get("description")
        self.agent_instr = agent["spec"].get("instructions")

        self.agent_input = agent["spec"].get("input")
        self.agent_output = agent["spec"].get("output")

        self.agent_code = agent["spec"].get("code")

        self.instructions = (
            f"{self.agent_instr} Input is expected in format: {self.agent_input}"
            if self.agent_input
            else self.agent_instr
        )
        self.instructions = (
            f"{self.instructions} Output must be in format: {self.agent_output}"
            if self.agent_output
            else self.instructions
        )

    EMOJIS: Final[Dict[str, str]] = {
        "beeai": "🐝",
        "crewai": "👥",
        "openai": "🔓",
        "mock": "🤖",
        "remote": "💸",
        # Not yet supported
        # 'langflow': '⛓',
    }

    def emoji(self) -> str:
        """Provides an Emoji for agent type"""
        return self.EMOJIS.get(self.agent_framework, "⚙️")

    def print(self, message) -> str:
        print(f"{self.emoji()} {message}")

    @abstractmethod
    async def run(self, prompt: str) -> str:
        """
        Runs the agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """

    @abstractmethod
    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """


def _load_agent_db():
    """
    Load agents from database.

    Parameters:
    None

    Returns:
    agents (dict): A dictionary containing the loaded agents.
    """
    agents = {}
    if os.path.exists("agents.db"):
        with open("agents.db", "rb") as f:
            agents = pickle.load(f)
    return agents


def _save_agent_db(db):
    """
    Save the agent database to a file.

    Args:
        db (dict): The agent database to be saved.

    Returns:
        None
    """
    with open("agents.db", "wb") as f:
        pickle.dump(db, f)


def save_agent(agent, agent_def):
    """
    Save agent in storage.
    """
    agents = _load_agent_db()
    try:
        agent_data = pickle.dumps(agent)
    except Exception:
        agent_data = json.dumps(agent_def)
    agents[agent.agent_name] = agent_data
    _save_agent_db(agents)


def restore_agent(agent_name: str):
    """
    Restore agent from storage.
    """
    agents = _load_agent_db()
    agent_data = agents[agent_name]
    try:
        if "maestro/v1alpha1" in agent_data:
            return json.loads(agent_data), False
        else:
            return pickle.loads(agent_data), True
    except Exception:
        return pickle.loads(agent_data), True


def remove_agent(agent_name: str):
    """
    Remove agent from storage.
    """
    agents = _load_agent_db()
    agents.pop(agent_name)
    _save_agent_db(agents)
