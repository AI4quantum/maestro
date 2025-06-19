#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import sys
import yaml
from maestro.workflow import Workflow
from dotenv import load_dotenv

load_dotenv()

# TODO: dd crewai agent path to path explicitly - this should be found on path, but may require base change
sys.path.append("agents/crewai/activity_planner")

def test_agent_runs() -> None:
    """
    Verify the test agent runs correctly
    """
    def parse_yaml(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            yaml_data = list(yaml.safe_load_all(file))
        return yaml_data

    agents_yaml = parse_yaml("demos/activity-planner.ai/src/agents.yaml")
    workflow_yaml = parse_yaml("demos/activity-planner.ai/src/workflow-tmp.yaml")
    try:
        workflow = Workflow(agents_yaml, workflow_yaml[0])
    except Exception as excep:
        raise RuntimeError("Unable to create agents") from excep
    result = workflow.run()
    print(result)
        
if __name__ == "__main__":
    test_agent_runs()


