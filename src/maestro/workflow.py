#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
from dotenv import load_dotenv
import time
import pycron

from maestro.mermaid import Mermaid
from maestro.step import Step
from maestro.utils import eval_expression

from maestro.agents.agent_factory import AgentFramework, AgentFactory
from maestro.agents.agent import save_agent, restore_agent
from maestro.agents.mock_agent import MockAgent

load_dotenv()


def get_agent_class(framework: str, mode="local") -> type:
    if os.getenv("DRY_RUN"):
        return MockAgent
    return AgentFactory.create_agent(framework, mode)


def create_agents(agent_defs):
    for agent_def in agent_defs:
        agent_def["spec"]["framework"] = agent_def["spec"].get(
            "framework", AgentFramework.BEEAI
        )
        cls = get_agent_class(
            agent_def["spec"]["framework"],
            agent_def["spec"].get("mode")
        )
        instance = cls(agent_def)
        save_agent(instance, agent_def)

class Workflow:
    def __init__(self, agent_defs=None, workflow=None):
        self.agents = {}
        self.steps = {}
        self.agent_defs = agent_defs or []
        self.workflow = workflow or {}

    def to_mermaid(self, kind="sequenceDiagram", orientation="TD") -> str:
        wf = self.workflow
        if isinstance(wf, list):
            wf = wf[0]
        return Mermaid(wf, kind, orientation).to_markdown()

    async def run(self, prompt=''):
        if prompt:
            self.workflow['spec']['template']['prompt'] = prompt
        self._create_or_restore_agents()

        template = self.workflow['spec']['template']
        try:
            if template.get('event'):
                result = await self._condition()
                return await self.process_event(result)
            else:
                return await self._condition()
        except Exception as err:
            exc_def = template.get('exception')
            if exc_def:
                agent_name = exc_def.get('agent')
                handler = self.agents.get(agent_name)
                if handler:
                    await handler.run(err)
                    return None
            raise err

    def _create_or_restore_agents(self):
        if self.agent_defs:
            for agent_def in self.agent_defs:
                if isinstance(agent_def, str):
                    instance, restored = restore_agent(agent_def)
                    if restored:
                        self.agents[agent_def] = instance
                        continue
                    else:
                        agent_def = instance

                agent_def["spec"]["framework"] = agent_def["spec"].get(
                    "framework", AgentFramework.BEEAI
                )
                cls = get_agent_class(
                    agent_def["spec"]["framework"],
                    agent_def["spec"].get("mode")
                )
                self.agents[agent_def["metadata"]["name"]] = cls(agent_def)
        else:
            for name in self.workflow["spec"]["template"]["agents"]:
                instance, restored = restore_agent(name)
                if restored:
                    self.agents[name] = instance
                else:
                    agent_def = instance
                    agent_def["spec"]["framework"] = agent_def["spec"].get(
                        "framework", AgentFramework.BEEAI
                    )
                    cls = get_agent_class(
                        agent_def["spec"]["framework"],
                        agent_def["spec"].get("mode")
                    )
                    self.agents[agent_def["metadata"]["name"]] = cls(agent_def)

    def find_index(self, steps, name):
        for idx, step in enumerate(steps):
            if step.get("name") == name:
                return idx
        return None

    async def _condition(self):
        template = self.workflow["spec"]["template"]
        initial_prompt = template["prompt"]
        steps = template["steps"]
        step_defs = {step["name"]: step for step in steps}

        for step in steps:
            if step.get("agent"):
                if isinstance(step["agent"], str):
                    step["agent"] = self.agents.get(step["agent"])
                if not step["agent"]:
                    raise RuntimeError("Agent doesn't exist")
            if step.get("parallel"):
                step["parallel"] = [
                    self.agents.get(name) for name in step["parallel"]
                ]
            if step.get("loop"):
                loop_def = step["loop"]
                loop_def["agent"] = self.agents.get(loop_def.get("agent"))
            self.steps[step["name"]] = Step(step)

        step_results = {}
        current = steps[0]["name"]
        prompt = initial_prompt

        while True:
            definition = step_defs[current]
            if definition.get("inputs"):
                args = []
                for inp in definition["inputs"]:
                    src = inp["from"]
                    if src == "prompt":
                        args.append(initial_prompt)
                    elif "instructions:" in src:
                        args.append(step_defs[src.split(":")[-1]]["agent"].agent_instr)
                    elif src in step_results:
                        args.append(step_results[src])
                    else:
                        args.append(src)
                result = await self.steps[current].run(*args)
            else:
                result = await self.steps[current].run(prompt)

            prompt = result.get("prompt")
            step_results[current] = prompt

            if "next" in result:
                current = result["next"]
            else:
                last = steps[-1]["name"]
                if current == last:
                    break
                idx = self.find_index(steps, current)
                current = steps[idx + 1]["name"]

        return {"final_prompt": prompt, **step_results}

    async def process_event(self, result):
        ev         = self.workflow['spec']['template']['event']
        cron       = ev.get('cron')
        agent_name = ev.get('agent')
        step_names = ev.get('steps', [])
        exit_expr  = ev.get('exit')

        run_once = True
        while True:
            if pycron.is_now(cron):
                if run_once:
                    if agent_name:
                        agent = self.agents.get(agent_name)
                        if not agent:
                            raise RuntimeError(f"Agent '{agent_name}' not found for event")
                        new_prompt = await agent.run(result["final_prompt"])
                        result[agent_name]     = new_prompt
                        result["final_prompt"] = new_prompt
                    if step_names:
                        raw_steps = self.workflow['spec']['template']['steps']
                        sub_defs  = [s for s in raw_steps if s['name'] in step_names]
                        out = await self._condition_subflow(
                            sub_defs,
                            step_names[0],
                            result["final_prompt"]
                        )
                        result.update(out)
                    run_once = False

                if exit_expr and eval_expression(exit_expr, result):
                    break
            time.sleep(30)

        return result

    async def _condition_subflow(self, steps, start, prompt):
        step_defs = {step["name"]: step for step in steps}
        for step in steps:
            if step.get("loop"):
                loop_def = step["loop"]
                loop_def["agent"] = self.agents.get(loop_def.get("agent"))
            self.steps[step["name"]] = Step(step)

        step_results = {}
        current = start

        while True:
            definition = step_defs[current]
            if definition.get("inputs"):
                args = []
                for inp in definition["inputs"]:
                    src = inp["from"]
                    if src == "prompt":
                        args.append(prompt)
                    elif src in step_results:
                        args.append(step_results[src])
                    else:
                        args.append(src)
                result = await self.steps[current].run(*args)
            else:
                result = await self.steps[current].run(prompt)

            prompt = result.get("prompt")
            step_results[current] = prompt

            if "next" in result:
                current = result["next"]
            else:
                if current == steps[-1]["name"]:
                    break
                idx = self.find_index(steps, current)
                current = steps[idx + 1]["name"]

        return {"final_prompt": prompt, **step_results}

    def get_step(self, step_name):
        for s in self.workflow["spec"]["template"]["steps"]:
            if s.get("name") == step_name:
                return s
        return None
