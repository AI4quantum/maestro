#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
import os
import pickle
import json
from datetime import datetime
from typing import Dict, Final, Any

from maestro.agents.utils import (
    TokenUsageExtractor,
    count_tokens as utils_count_tokens,
    track_token_usage as utils_track_token_usage,
)

from maestro.agents.utils import get_content


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
        self.agent_url = agent["spec"].get("url")

        self.agent_tools = agent["spec"].get("tools", [])

        self.agent_desc = agent["spec"].get("description") or ""
        self.agent_instr = get_content(
            agent["spec"].get("instructions"), agent.get("source_file", "")
        )

        self.agent_input = agent["spec"].get("input")
        self.agent_output = agent["spec"].get("output")

        self.agent_code = get_content(
            agent["spec"].get("code"), agent.get("source_file", "")
        )

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

        # Base token counters for LLM-style agents. Custom/scoring agents override get_token_usage.
        self.prompt_tokens: int = 0
        self.response_tokens: int = 0
        self.total_tokens: int = 0

    EMOJIS: Final[Dict[str, str]] = {
        "beeai": "🐝",
        "crewai": "👥",
        "dspy": "💭",
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
        now = datetime.now()
        formatted_time = now.strftime("%m-%d-%Y %H:%M:%S")
        print(f"{self.emoji()} {formatted_time}: {message}")

    @abstractmethod
    async def run(self, prompt: str, context=None, step_index=None) -> str:
        """
        Runs the agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
            context (dict, optional): Context dictionary containing outputs from previous steps.
            step_index (int, optional): Index of the current step in the workflow.
        """

    @abstractmethod
    async def run_streaming(self, prompt: str, context=None, step_index=None) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
            context (dict, optional): Context dictionary containing outputs from previous steps.
            step_index (int, optional): Index of the current step in the workflow.
        """

    def get_token_usage(self) -> Dict[str, Any]:
        """
        Get token usage statistics for the agent.
        - For custom agents (including scoring agents), return a descriptive structure.
        - For LLM-style agents, return the current counters.
        """
        if self.agent_framework == "custom":
            if hasattr(self, "agent_name") and "score" in self.agent_name.lower():
                return {
                    "agent_type": "scoring_agent",
                    "description": "Uses Opik evaluation metrics (relevance, hallucination)",
                }
            return {
                "agent_type": "custom_agent",
                "description": "Custom agent - no traditional token usage",
            }

        return {
            "prompt_tokens": self.prompt_tokens,
            "response_tokens": self.response_tokens,
            "total_tokens": self.total_tokens,
        }

    def reset_token_usage(self) -> None:
        """Reset token usage counters to zero."""
        self.prompt_tokens = 0
        self.response_tokens = 0
        self.total_tokens = 0

    def count_tokens(self, text: str) -> int:
        """Count tokens for text using shared utility with sensible logging."""
        agent_label = f"{self.__class__.__name__} {self.agent_name}"
        return utils_count_tokens(text, agent_label, self.print)

    def track_tokens(self, prompt: str, response: str) -> Dict[str, int]:
        """Compute and store token usage for a prompt/response pair."""
        agent_label = f"{self.__class__.__name__} {self.agent_name}"
        token_usage = utils_track_token_usage(prompt, response, agent_label, self.print)
        self.prompt_tokens = token_usage["prompt_tokens"]
        self.response_tokens = token_usage["response_tokens"]
        self.total_tokens = token_usage["total_tokens"]
        return token_usage

    def extract_and_set_token_usage_from_result(self, result: Any) -> Dict[str, int]:
        """Extract token usage from a provider-specific result object and store it."""
        agent_label = f"{self.__class__.__name__} {self.agent_name}"
        token_usage = TokenUsageExtractor.extract_from_result(
            result, agent_label, self.print
        )
        self.prompt_tokens = token_usage["prompt_tokens"]
        self.response_tokens = token_usage["response_tokens"]
        self.total_tokens = token_usage["total_tokens"]
        return token_usage


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
    if agent_name not in agents:
        return agent_name, False
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
