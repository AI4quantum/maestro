#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import unittest

from typing import Callable

from unittest import TestCase

from maestro.agents.agent_factory import AgentFramework, AgentFactory


class TestAgentFramework(TestCase):
    def test_frameworks(self):
        self.assertTrue(AgentFramework.BEEAI is not None)
        self.assertTrue(AgentFramework.CREWAI is not None)
        self.assertTrue(AgentFramework.OPENAI is not None)
        self.assertTrue(AgentFramework.MOCK is not None)
        self.assertTrue(AgentFramework.REMOTE is not None)


class TestAgentFactory(TestCase):
    def test_create_agents(self):
        self.assertTrue(
            isinstance(AgentFactory.create_agent(AgentFramework.BEEAI), Callable)
        )
        self.assertTrue(
            isinstance(AgentFactory.create_agent(AgentFramework.CREWAI), Callable)
        )
        self.assertTrue(
            isinstance(AgentFactory.create_agent(AgentFramework.OPENAI), Callable)
        )
        self.assertTrue(
            isinstance(AgentFactory.create_agent(AgentFramework.MOCK), Callable)
        )
        self.assertTrue(
            isinstance(AgentFactory.create_agent(AgentFramework.REMOTE), Callable)
        )

    def test_get_factory(self):
        self.assertTrue(AgentFactory.get_factory(AgentFramework.BEEAI) is not None)
        self.assertTrue(AgentFactory.get_factory(AgentFramework.CREWAI) is not None)
        self.assertTrue(AgentFactory.get_factory(AgentFramework.OPENAI) is not None)
        self.assertTrue(AgentFactory.get_factory(AgentFramework.MOCK) is not None)
        self.assertTrue(AgentFactory.get_factory(AgentFramework.REMOTE) is not None)


if __name__ == "__main__":
    unittest.main()
