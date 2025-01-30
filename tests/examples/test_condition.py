#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys

import dotenv
from openai import OpenAI
import yaml
from bee_hive.workflow import Workflow

dotenv.load_dotenv()


def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data



if __name__ == "__main__":
    agents_yaml = parse_yaml("condition_agents.yaml")
    workflow_yaml = parse_yaml("condition_workflow.yaml")
    try:
        workflow = Workflow(agents_yaml, workflow_yaml[0])
    except Exception as excep:
        raise RuntimeError("Unable to create agents") from excep
    workflow.run()
