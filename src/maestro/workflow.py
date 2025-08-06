#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import time
import pycron
from dotenv import load_dotenv
from opik import Opik

from maestro.mermaid import Mermaid
from maestro.step import Step
from maestro.utils import eval_expression

from maestro.agents.agent_factory import AgentFramework, AgentFactory
from maestro.agents.agent import save_agent, restore_agent
from maestro.agents.mock_agent import MockAgent
from maestro.logging_hooks import log_agent_run  # <-- logging decorator

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
            agent_def["spec"]["framework"], agent_def["spec"].get("mode")
        )
        instance = cls(agent_def)
        save_agent(instance, agent_def)


class Workflow:
    def __init__(self, agent_defs=None, workflow=None, workflow_id=None, logger=None):
        self.agents = {}
        self.steps = {}
        self.agent_defs = agent_defs or []
        self.workflow = workflow or {}
        self.workflow_id = workflow_id
        self.logger = logger
        self._opik = None
        self.scoring_metrics = None
        self.workflow_models = {}

    def to_mermaid(self, kind="sequenceDiagram", orientation="TD") -> str:
        wf = self.workflow
        if isinstance(wf, list):
            wf = wf[0]
        return Mermaid(wf, kind, orientation).to_markdown()

    async def run(self, prompt=""):
        if prompt:
            self.workflow["spec"]["template"]["prompt"] = prompt
        self._create_or_restore_agents()

        template = self.workflow["spec"]["template"]
        initial_prompt = template["prompt"]

        try:
            if template.get("event"):
                result = await self._condition()
                return await self.process_event(result)
            else:
                return await self._condition()
        except Exception as err:
            self._create_workflow_trace(initial_prompt, f"ERROR: {str(err)}", {})

            exc_def = template.get("exception")
            if exc_def:
                agent_name = exc_def.get("agent")
                handler = self.agents.get(agent_name)
                if handler:
                    await handler.run(err, step_index=-1)
                    return None
            raise err

    async def run_streaming(self, prompt=""):
        """Run workflow with step-by-step streaming."""
        if prompt:
            self.workflow["spec"]["template"]["prompt"] = prompt
        self._create_or_restore_agents()

        template = self.workflow["spec"]["template"]
        try:
            if template.get("event"):
                async for step_result in self._condition_streaming():
                    yield step_result
                result = await self.process_event(step_result)
                yield {"final_result": result}
            else:
                async for step_result in self._condition_streaming():
                    yield step_result
        except Exception as err:
            exc_def = template.get("exception")
            if exc_def:
                agent_name = exc_def.get("agent")
                handler = self.agents.get(agent_name)
                if handler:
                    await handler.run(err, step_index=-1)
                    yield {"error": str(err)}
            else:
                yield {"error": str(err)}

    def _create_or_restore_agents(self):
        """Create or restore agents for the workflow."""
        if self.agent_defs:
            for agent_def in self.agent_defs:
                name = agent_def["metadata"]["name"]
                instance, restored = restore_agent(name)
                if restored:
                    agent_instance = instance
                else:
                    agent_def["spec"]["framework"] = agent_def["spec"].get(
                        "framework", AgentFramework.BEEAI
                    )
                    cls = get_agent_class(
                        agent_def["spec"]["framework"], agent_def["spec"].get("mode")
                    )
                    agent_instance = cls(agent_def)

                agent_name = name
                agent_model = agent_def["spec"].get("model", f"code:{name}")
                agent_instance.agent_name = agent_name
                agent_instance.agent_model = agent_model
                bound_method = agent_instance.run.__get__(agent_instance)
                agent_instance.run = log_agent_run(
                    self.workflow_id, agent_name, agent_model
                )(bound_method)

                self.agents[agent_name] = agent_instance
                if not self._is_scoring_agent(agent_def):
                    self.workflow_models[agent_name] = agent_model

        else:
            for name in self.workflow["spec"]["template"]["agents"]:
                instance, restored = restore_agent(name)
                if restored:
                    agent_instance = instance
                else:
                    agent_def = instance
                    agent_def["spec"]["framework"] = agent_def["spec"].get(
                        "framework", AgentFramework.BEEAI
                    )
                    cls = get_agent_class(
                        agent_def["spec"]["framework"], agent_def["spec"].get("mode")
                    )
                    agent_instance = cls(agent_def)

                agent_name = name
                agent_model = f"code:{name}"
                agent_instance.agent_name = agent_name
                agent_instance.agent_model = agent_model
                bound_method = agent_instance.run.__get__(agent_instance)
                agent_instance.run = log_agent_run(
                    self.workflow_id, agent_name, agent_model
                )(bound_method)

                self.agents[agent_name] = agent_instance

        if self._has_scoring_agent():
            self._initialize_opik()

    def find_index(self, steps, name):
        for idx, step in enumerate(steps):
            if step.get("name") == name:
                return idx
        return None

    async def _condition(self):
        template = self.workflow["spec"]["template"]
        initial_prompt = template["prompt"]
        steps = template["steps"]
        workflows = template.get("workflows")
        step_defs = {step["name"]: step for step in steps}

        for step in steps:
            if step.get("agent"):
                if isinstance(step["agent"], str):
                    step_name = step["agent"]
                    step["agent"] = self.agents.get(step_name)
                    if step["agent"] is None:
                        raise ValueError(f"Could not find agent named '{step_name}'")
            if step.get("workflow"):
                if isinstance(step["workflow"], str):
                    found = False
                    for workflow in workflows:
                        if workflow["name"] == step["workflow"]:
                            step["workflow"] = workflow["url"]
                            found = True
                if not found:
                    raise RuntimeError("Workflow doesn't exist")
            if step.get("parallel"):
                step["parallel"] = [self.agents.get(name) for name in step["parallel"]]
            if step.get("loop"):
                loop_def = step["loop"]
                loop_def["agent"] = self.agents.get(loop_def.get("agent"))
            self.steps[step["name"]] = Step(step)

        step_results = {}
        current = steps[0]["name"]
        prompt = initial_prompt
        step_index = 0

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
                result = await self.steps[current].run(*args, step_index=step_index)
            else:
                result = await self.steps[current].run(prompt, step_index=step_index)

            prompt = result.get("prompt")
            step_results[current] = prompt
            if isinstance(result, dict) and "scoring_metrics" in result:
                self.scoring_metrics = result["scoring_metrics"]

            step_index += 1

            if "next" in result:
                current = result["next"]
            else:
                last = steps[-1]["name"]
                if current == last:
                    break
                idx = self.find_index(steps, current)
                current = steps[idx + 1]["name"]

        self._create_workflow_trace(initial_prompt, prompt, step_results)

        return {"final_prompt": prompt, **step_results}

    async def _condition_streaming(self):
        """Run workflow steps with streaming output."""
        template = self.workflow["spec"]["template"]
        initial_prompt = template["prompt"]
        steps = template["steps"]
        workflows = template.get("workflows")
        step_defs = {step["name"]: step for step in steps}

        for step in steps:
            if step.get("agent"):
                if isinstance(step["agent"], str):
                    step_name = step["agent"]
                    step["agent"] = self.agents.get(step_name)
                    if step["agent"] is None:
                        raise ValueError(f"Could not find agent named '{step_name}'")
            if step.get("workflow"):
                if isinstance(step["workflow"], str):
                    found = False
                    for workflow in workflows:
                        if workflow["name"] == step["workflow"]:
                            step["workflow"] = workflow["url"]
                            found = True
                    if not found:
                        raise RuntimeError("Workflow doesn't exist")
            if step.get("parallel"):
                step["parallel"] = [self.agents.get(name) for name in step["parallel"]]
            if step.get("loop"):
                loop_def = step["loop"]
                loop_def["agent"] = self.agents.get(loop_def.get("agent"))
            self.steps[step["name"]] = Step(step)

        step_results = {}
        current = steps[0]["name"]
        prompt = initial_prompt
        step_index = 0

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
                result = await self.steps[current].run(*args, step_index=step_index)
            else:
                result = await self.steps[current].run(prompt, step_index=step_index)

            prompt = result.get("prompt")
            step_results[current] = prompt
            step_index += 1

            yield {
                "step_name": current,
                "step_result": prompt,
                "step_index": step_index - 1,
                "agent_name": definition.get("agent", {}).agent_name
                if definition.get("agent")
                else None,
            }

            if "next" in result:
                current = result["next"]
            else:
                last = steps[-1]["name"]
                if current == last:
                    break
                idx = self.find_index(steps, current)
                current = steps[idx + 1]["name"]

        yield {"final_result": {"final_prompt": prompt, **step_results}}

    def _create_workflow_trace(self, initial_prompt, final_prompt, step_results):
        """
        Create a single trace for the entire workflow run with scoring metrics as metadata.
        Only creates traces if Opik is initialized (i.e., when there's a scoring agent).
        """
        if self._opik is None:
            return
        try:
            metadata = self._build_trace_metadata(step_results)
            self._create_opik_trace(initial_prompt, final_prompt, metadata)
        except Exception as e:
            print(f"[Workflow] Warning: could not create trace: {e}")

    async def process_event(self, result):
        ev = self.workflow["spec"]["template"]["event"]
        cron = ev.get("cron")
        agent_name = ev.get("agent")
        step_names = ev.get("steps", [])
        exit_expr = ev.get("exit")

        run_once = True
        while True:
            if pycron.is_now(cron):
                if run_once:
                    if agent_name:
                        agent = self.agents.get(agent_name)
                        if not agent:
                            raise RuntimeError(
                                f"Agent '{agent_name}' not found for event"
                            )
                        new_prompt = await agent.run(result["final_prompt"])
                        result[agent_name] = new_prompt
                        result["final_prompt"] = new_prompt
                    if step_names:
                        raw_steps = self.workflow["spec"]["template"]["steps"]
                        sub_defs = [s for s in raw_steps if s["name"] in step_names]
                        out = await self._condition_subflow(
                            sub_defs, step_names[0], result["final_prompt"]
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
        step_index = 0

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
                result = await self.steps[current].run(*args, step_index=step_index)
            else:
                result = await self.steps[current].run(prompt, step_index=step_index)

            prompt = result.get("prompt")
            step_results[current] = prompt
            step_index += 1

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

    def _has_scoring_agent(self) -> bool:
        """Check if there's a scoring agent in the workflow."""
        for agent_def in self.agent_defs or []:
            if isinstance(agent_def, dict):
                if (
                    agent_def.get("metadata", {}).get("labels", {}).get("custom_agent")
                    == "scoring_agent"
                ):
                    return True
                if agent_def.get("spec", {}).get("framework") == "custom":
                    return True

        if self.workflow:
            template_agents = (
                self.workflow.get("spec", {}).get("template", {}).get("agents", [])
            )
            for agent_name in template_agents:
                if agent_name in self.agents:
                    agent_instance = self.agents[agent_name]
                    if (
                        hasattr(agent_instance, "__class__")
                        and agent_instance.__class__.__name__ == "ScoringAgent"
                    ):
                        return True
        return False

    def _is_scoring_agent(self, agent_def: dict) -> bool:
        """Check if an agent definition is a scoring agent."""
        if isinstance(agent_def, dict):
            if (
                agent_def.get("metadata", {}).get("labels", {}).get("custom_agent")
                == "scoring_agent"
            ):
                return True
            if agent_def.get("spec", {}).get("framework") == "custom":
                agent_name = agent_def.get("metadata", {}).get("name", "").lower()
                if "score" in agent_name or "evaluate" in agent_name:
                    return True
        return False

    def _initialize_opik(self) -> None:
        """Initialize Opik for tracing if not already initialized."""
        if self._opik is None:
            self._opik = Opik()

    def _build_trace_metadata(self, step_results: dict) -> dict:
        """Build metadata for the Opik trace."""
        metadata = {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow.get("metadata", {}).get("name", "unknown"),
            "steps_executed": list(step_results.keys()),
            "total_steps": len(step_results),
        }

        if self.workflow_models:
            metadata["workflow_models"] = self.workflow_models
        if self.scoring_metrics:
            scoring_metadata = self.scoring_metrics.copy()
            if "model" in scoring_metadata:
                scoring_metadata["scoring_model"] = scoring_metadata.pop("model")
            if "provider" in scoring_metadata:
                scoring_metadata["framework_provider"] = scoring_metadata.pop(
                    "provider"
                )
            scoring_metadata.pop("agent", None)
            metadata.update(scoring_metadata)
        return metadata

    def _create_opik_trace(
        self, initial_prompt: str, final_prompt: str, metadata: dict
    ) -> None:
        """Create an Opik trace with the given parameters."""
        trace = self._opik.trace()
        trace.end(
            input={"input": initial_prompt},
            output={"output": final_prompt},
            metadata=metadata,
        )
