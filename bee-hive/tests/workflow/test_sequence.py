#!/usr/bin/env python3

import yaml
import dotenv
from unittest import TestCase
from pytest_mock import mocker

from bee_hive.workflow import Workflow
from bee_hive.bee_agent import BeeAgent

dotenv.load_dotenv()


class MockAgent:
    def __init__(self, name):
        self.name = name
        
    def run(self, prompt: str) -> str:
        return {"prompt": f"{prompt} processed by {self.name}"}

def test_sequence_method(mocker):
    def parse_yaml(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            yaml_data = list(yaml.safe_load_all(file))
        return yaml_data

    # Setup mock agents
    mock_agent1 = MockAgent("agent1")
    mock_agent2 = MockAgent("agent2")
    mock_agents = {"agent1": mock_agent1, "agent2": mock_agent2}

    mocker.patch.object(BeeAgent, "__new__", side_effect=lambda name: mock_agents[name])

    # Load workflow YAML
    workflow_yaml = parse_yaml("tests/workflow/workflow.yaml")

    try:
        workflow = Workflow(agent_defs=[], workflow=workflow_yaml[0])
        workflow.agents = mock_agents  # Manually inject mocked agents
    except Exception as excep:
        raise RuntimeError("Unable to create workflow") from excep

    prompt = workflow._sequence()
    # debugging
    print(prompt)
    assert prompt 