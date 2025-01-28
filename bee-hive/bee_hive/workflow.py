#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys
from time import clock_settime
from typing import Callable

import yaml
import dotenv
from bee_hive import Step
from bee_hive import Agent
from agent_factory import AgentFactory, AgentFramework

dotenv.load_dotenv()

# TODO: Refactor later to factory or similar
from crewai_agent import CrewAIAgent
from bee_agent import BeeAgent

@staticmethod
def get_agent_class(framework: str) -> type:
    if framework == 'crewai':
        return CrewAIAgent
    else:
        return BeeAgent
    
    

class Workflow:
    agents = {}
    steps = {}
    workflow = {}
    def __init__(self, agent_defs, workflow):
        """Execute sequential workflow.
        input:
            agents: array of agent definitions
            workflow: workflow definition
        """
        for agent_def in agent_defs:
            # Use 'bee' if this value isn't set
            # 
            agent_def["spec"]["framework"] = agent_def["spec"].get("framework", AgentFramework.BEE)
            self.agents[agent_def["metadata"]["name"]] = get_agent_class(agent_def["spec"]["framework"])(agent_def)
        self.workflow = workflow


    def run(self):
        """Execute workflow."""

        if (self.workflow["spec"]["strategy"]["type"]  == "sequence"):
            return self._sequence()
        elif (self.workflow["spec"]["strategy"]["type"]  == "condition"):
            return self._condition()
        else:
            print("not supported yet")   

    def _sequence(self):
        prompt = self.workflow["spec"]["template"]["prompt"]
        for agent in self.agents.values():
            if (
                self.workflow["spec"]["strategy"]["output"]
                and self.workflow["spec"]["strategy"]["output"] == "verbose"
            ):
                prompt = agent.run_streaming(prompt)
            else:
                prompt = agent.run(prompt)
        return prompt

    def _condition(self):
        prompt = self.workflow["spec"]["template"]["prompt"]
        steps = self.workflow["spec"]["template"]["steps"]
        for step in steps:
            if step["agent"]:
                step["agent"] = self.agents.get(step["agent"])
            self.steps[step["name"]] = Step(step)
        current_step = self.workflow["spec"]["template"]["start"]
        while current_step != "end":
            response = self.steps[current_step].run(prompt)
            prompt = response["prompt"]
            current_step = response["next"]
        return prompt
