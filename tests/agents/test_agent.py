#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import unittest
from maestro.agents.agent import Agent


class TestAgentEmojis(unittest.TestCase):
    def _create_agent(self, framework: str) -> Agent:
        agent_dict = {
            "metadata": {"name": f"{framework}_test_agent"},
            "spec": {
                "framework": framework,
                "model": "test_model",  # Placeholder value
                "description": "test desc",  # Placeholder value
                "instructions": "test instr",  # Placeholder value
            },
        }
        return Agent(agent_dict)

    def test_emoji_outputs(self):
        test_cases = {
            # Known frameworks from Agent.EMOJIS
            "beeai": "🐝",
            "crewai": "👥",
            "openai": "🔓",
            "mock": "🤖",
            "remote": "💸",
            # Unknown framework should return the default
            "some_new_framework": "⚙️",
            "another_unknown": "⚙️",
            # Edge case: empty string framework name
            "": "⚙️",
        }

        for framework, expected_emoji in test_cases.items():
            with self.subTest(framework=framework):
                agent = self._create_agent(framework)
                actual_emoji = agent.emoji()

                self.assertEqual(
                    actual_emoji,
                    expected_emoji,
                    f"Emoji for framework '{framework}' should be '{expected_emoji}' but got '{actual_emoji}'",
                )


if __name__ == "__main__":
    unittest.main()
