#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import yaml
import unittest
from unittest import TestCase
from maestro.workflow import create_agents, get_agent_class
from maestro.agents.agent import restore_agent


def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data


class TestSaveRestoreBeeAgent(TestCase):
    def setUp(self):
        self.agents_yaml = parse_yaml(
            os.path.join(os.path.dirname(__file__), "../yamls/agents/beeai_agent.yaml")
        )
        try:
            os.environ["BEE_API"] = "http://127.0.0.1:4000"
            os.environ["BEE_API_KEY"] = "sk-proj-testkey"
            create_agents(self.agents_yaml)
            self.no_agent = False
        except Exception:
            self.no_agent = True

    def tearDown(self):
        self.agent = None

    def test_restore(self):
        if self.no_agent:
            print("No agent saved")
        else:
            saved_agent, instance = restore_agent(
                self.agents_yaml[0]["metadata"]["name"]
            )
            cls = get_agent_class(
                self.agents_yaml[0]["spec"]["framework"],
                self.agents_yaml[0]["spec"].get("mode"),
            )
            agent = cls(self.agents_yaml[0])
            assert instance
            assert saved_agent.agent_id == agent.agent_id


class TestSaveRestoreOpenAIAgent(TestCase):
    def setUp(self):
        self.agents_yaml = parse_yaml(
            os.path.join(os.path.dirname(__file__), "../yamls/agents/openai_agent.yaml")
        )
        try:
            create_agents(self.agents_yaml)
            self.no_agent = False
        except Exception:
            self.no_agent = True

    def tearDown(self):
        self.agent = None

    def test_restore(self):
        if self.no_agent:
            print("No agent saved")
        else:
            saved_agent, instance = restore_agent(
                self.agents_yaml[0]["metadata"]["name"]
            )
            assert (
                saved_agent["spec"]["instructions"]
                == self.agents_yaml[0]["spec"]["instructions"]
            )


if __name__ == "__main__":
    unittest.main()
