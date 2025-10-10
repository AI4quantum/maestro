#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import time
import pycron
from typing import Dict, Any
from dotenv import load_dotenv
from opik import Opik

from maestro.mermaid import Mermaid
from maestro.step import Step
from maestro.utils import eval_expression, aggregate_token_usage_from_agents

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
            "framework", AgentFramework.OPENAI
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
        self.workflow_start_time = None
        self.workflow_end_time = None
        self.agent_execution_times = {}
        self._timing_started = False

    def __del__(self):
        """Ensure timing is ended when workflow is destroyed."""
        if hasattr(self, "_timing_started") and self._timing_started:
            self._end_workflow_timing()

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
        self._start_workflow_timing()

        try:
            if template.get("event"):
                result = await self._condition()
                self._end_workflow_timing()
                return await self.process_event(result)
            else:
                result = await self._condition()
                self._end_workflow_timing()
                return result
        except Exception as err:
            self._end_workflow_timing()
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
        self._start_workflow_timing()

        try:
            if template.get("event"):
                async for step_result in self._condition_streaming():
                    yield step_result
                result = await self.process_event(step_result)
                self._end_workflow_timing()
                yield {"final_result": result}
            else:
                async for step_result in self._condition_streaming():
                    yield step_result
                self._end_workflow_timing()
        except Exception as err:
            self._end_workflow_timing()
            exc_def = template.get("exception")
            if exc_def:
                agent_name = exc_def.get("agent")
                handler = self.agents.get(agent_name)
                if handler:
                    await handler.run(err, step_index=-1)
                    yield {"error": str(err)}
            else:
                yield {"error": str(err)}

    def get_context_state(self) -> dict:
        """Get the current context state for debugging purposes."""
        return getattr(self, "_context", {})

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
                    agent_def["spec"]["framework"], agent_def["spec"].get("mode")
                )
                agent_instance = cls(agent_def)

                agent_name = agent_def["metadata"]["name"]
                agent_model = agent_def["spec"].get("model", f"code:{agent_name}")
                agent_instance.agent_name = agent_name
                agent_instance.agent_model = agent_model
                agent_instance._workflow_instance = self
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
                agent_instance._workflow_instance = self
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
        context = {}
        current = steps[0]["name"]
        prompt = initial_prompt
        step_index = 0

        while True:
            definition = step_defs[current]

            # Handle selective context routing with 'from' field
            if definition.get("from"):
                # Build context from specified previous steps or agents
                from_sources = definition["from"]
                if isinstance(from_sources, str):
                    from_sources = [from_sources]

                # Collect outputs from specified sources
                context_inputs = []
                for source in from_sources:
                    if source == "prompt":
                        context_inputs.append(initial_prompt)
                    elif source in step_results:
                        # Source is a step name
                        context_inputs.append(step_results[source])
                    else:
                        # Source might be an agent name - find the step that uses this agent
                        agent_step_name = None
                        for step_name, step_def in step_defs.items():
                            if (
                                step_def.get("agent")
                                and hasattr(step_def["agent"], "agent_name")
                                and step_def["agent"].agent_name == source
                            ):
                                agent_step_name = step_name
                                break
                            elif step_def.get("agent") == source:
                                # Direct agent reference
                                agent_step_name = step_name
                                break

                        if agent_step_name and agent_step_name in step_results:
                            context_inputs.append(step_results[agent_step_name])
                        else:
                            context_inputs.append(source)

                # Join multiple inputs with newlines if multiple sources
                if len(context_inputs) == 1:
                    prompt = context_inputs[0]
                else:
                    prompt = "\n\n".join([str(inp) for inp in context_inputs if inp])

                print(f"\n🔍 [CONTEXT ROUTING] Step '{current}' using 'from' field:")
                print(f"   Sources: {from_sources}")
                print(
                    f"   Final prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}"
                )

                result = await self.steps[current].run(
                    prompt, context=context, step_index=step_index
                )
            else:
                # Default behavior: use output from previous step
                print(
                    f"\n🔍 [DEFAULT ROUTING] Step '{current}' using previous step output:"
                )
                prompt_str = str(prompt)
                print(
                    f"   Prompt: {prompt_str[:200]}{'...' if len(prompt_str) > 200 else ''}"
                )

                result = await self.steps[current].run(
                    prompt, context=context, step_index=step_index
                )

            prompt = result.get("prompt")
            step_results[current] = prompt
            context[current] = prompt
            self._context = context
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
            if definition.get("from"):
                from_sources = definition["from"]
                if isinstance(from_sources, str):
                    from_sources = [from_sources]
                context_inputs = []
                for source in from_sources:
                    if source == "prompt":
                        context_inputs.append(prompt)
                    elif source in step_results:
                        context_inputs.append(step_results[source])
                    else:
                        context_inputs.append(source)

                if len(context_inputs) == 1:
                    step_prompt = context_inputs[0]
                else:
                    step_prompt = "\n\n".join(
                        [str(inp) for inp in context_inputs if inp]
                    )
            else:
                step_prompt = prompt

            result = await self.steps[current].run(step_prompt, step_index=step_index)

            prompt = result.get("prompt")
            step_results[current] = prompt
            step_index += 1
            agent_obj = definition.get("agent")
            token_data = {}
            if agent_obj and hasattr(agent_obj, "prompt_tokens"):
                token_data = {
                    "prompt_tokens": getattr(agent_obj, "prompt_tokens", 0),
                    "response_tokens": getattr(agent_obj, "response_tokens", 0),
                    "total_tokens": getattr(agent_obj, "total_tokens", 0),
                }

            yield {
                "step_name": current,
                "step_result": prompt,
                "step_index": step_index - 1,
                "agent_name": agent_obj.agent_name if agent_obj else None,
                **token_data,
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
                        new_prompt = await agent.run(
                            result["final_prompt"], context=None, step_index=None
                        )
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

            # Handle selective context routing with 'from' field
            if definition.get("from"):
                # Build context from specified previous steps or agents
                from_sources = definition["from"]
                if isinstance(from_sources, str):
                    from_sources = [from_sources]

                # Collect outputs from specified sources
                context_inputs = []
                for source in from_sources:
                    if source == "prompt":
                        context_inputs.append(prompt)
                    elif source in step_results:
                        # Source is a step name
                        context_inputs.append(step_results[source])
                    else:
                        # Source might be an agent name - find the step that uses this agent
                        agent_step_name = None
                        for step_name, step_def in step_defs.items():
                            if (
                                step_def.get("agent")
                                and hasattr(step_def["agent"], "agent_name")
                                and step_def["agent"].agent_name == source
                            ):
                                agent_step_name = step_name
                                break
                            elif step_def.get("agent") == source:
                                # Direct agent reference
                                agent_step_name = step_name
                                break

                        if agent_step_name and agent_step_name in step_results:
                            context_inputs.append(step_results[agent_step_name])
                        else:
                            context_inputs.append(source)

                # Join multiple inputs with newlines if multiple sources
                if len(context_inputs) == 1:
                    step_prompt = context_inputs[0]
                else:
                    step_prompt = "\n\n".join(
                        [str(inp) for inp in context_inputs if inp]
                    )

                result = await self.steps[current].run(
                    step_prompt, step_index=step_index
                )
            else:
                # Default behavior: use output from previous step
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

    def _start_workflow_timing(self) -> None:
        """Start timing the workflow execution."""
        self.workflow_start_time = time.time()
        self._timing_started = True

    def _end_workflow_timing(self) -> None:
        """End timing the workflow execution."""
        if self._timing_started and self.workflow_end_time is None:
            self.workflow_end_time = time.time()
            self._timing_started = False

    def force_end_timing(self) -> None:
        """Force end timing if it's still running."""
        if self._timing_started:
            self._end_workflow_timing()

    def _get_workflow_execution_time(self) -> float:
        """Get the total workflow execution time in seconds."""
        if self.workflow_start_time and self.workflow_end_time:
            return self.workflow_end_time - self.workflow_start_time
        return 0.0

    def _track_agent_execution_time(
        self, agent_name: str, execution_time: float
    ) -> None:
        """Track execution time for a specific agent."""
        self.agent_execution_times[agent_name] = execution_time

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution time metrics for the workflow and all agents."""
        if self._timing_started:
            self.force_end_timing()

        return {
            "workflow_execution_time_seconds": self._get_workflow_execution_time(),
            "agent_execution_times": self.agent_execution_times.copy(),
            "total_agent_time_seconds": sum(self.agent_execution_times.values()),
            "workflow_start_time": self.workflow_start_time,
            "workflow_end_time": self.workflow_end_time,
            "timing_status": "completed" if self.workflow_end_time else "running",
        }

    def get_token_usage_summary(self) -> Dict[str, Any]:
        """Get token usage summary for all agents."""
        return aggregate_token_usage_from_agents(self.agents)

    def _build_trace_metadata(self, step_results: dict) -> dict:
        """Build metadata for the Opik trace."""
        metadata = {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow.get("metadata", {}).get("name", "unknown"),
            "steps_executed": list(step_results.keys()),
            "total_steps": len(step_results),
        }

        execution_metrics = self.get_execution_metrics()
        metadata.update(execution_metrics)

        total_token_usage = aggregate_token_usage_from_agents(self.agents)
        metadata.update(total_token_usage)

        if execution_metrics["workflow_execution_time_seconds"] > 0:
            metadata["tokens_per_second"] = (
                total_token_usage["total_tokens"]
                / execution_metrics["workflow_execution_time_seconds"]
            )
            metadata["cost_efficiency"] = {
                "tokens_per_second": metadata["tokens_per_second"],
                "seconds_per_token": execution_metrics[
                    "workflow_execution_time_seconds"
                ]
                / total_token_usage["total_tokens"]
                if total_token_usage["total_tokens"] > 0
                else 0,
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
