#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import dotenv
import tempfile

from beeai_framework.adapters.ollama import OllamaChatModel
from beeai_framework.agents.tool_calling import ToolCallingAgent
from beeai_framework.backend import ChatModel, ChatModelParameters
from beeai_framework.backend.utils import find_provider_def
from beeai_framework.tools.code import PythonTool, LocalPythonStorage, SandboxTool

from typing import Any, Callable
from pydantic import BaseModel

from beeai_framework.agents import AgentExecutionConfig, AgentMeta
from beeai_framework.emitter import Emitter, EmitterOptions, EventMeta
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.template import PromptTemplateInput
from beeai_framework.tools import AnyTool
from beeai_framework.tools.mcp import MCPTool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.weather import OpenMeteoTool
from beeai_framework.utils import AbortSignal

from maestro.agents.agent import Agent
from maestro.tool_utils import get_mcp_tools
from contextlib import AsyncExitStack

dotenv.load_dotenv()


def user_customizer(config: PromptTemplateInput[Any]) -> PromptTemplateInput[Any]:
    """user_customizer"""

    class UserSchema(BaseModel):
        """user schema"""

        input: str

    new_config = config.model_copy()
    new_config.input_schema = UserSchema
    new_config.template = """User: {{input}}"""
    return new_config


def no_result_customizer(config: PromptTemplateInput[Any]) -> PromptTemplateInput[Any]:
    """no_result_customizer"""
    new_config = config.model_copy()
    config.template += """\nPlease reformat your input."""
    return new_config


def not_found_customizer(config: PromptTemplateInput[Any]) -> PromptTemplateInput[Any]:
    """not_found_customizer"""

    class ToolSchema(BaseModel):
        """Tool Schema"""

        name: str

    class NotFoundSchema(BaseModel):
        """Not found schema"""

        tools: list[ToolSchema]

    new_config = config.model_copy()
    new_config.input_schema = NotFoundSchema
    new_config.template = """Tool does not exist!
{{#tools.length}}
Use one of the following tools: {{#trim}}{{#tools}}{{name}},{{/tools}}{{/trim}}
{{/tools.length}}"""
    return new_config


def user_template_func(template: PromptTemplateInput[Any]) -> PromptTemplateInput[Any]:
    return template.fork(customizer=user_customizer)


def get_system_template_func(
    instructions: str | None,
) -> Callable[[PromptTemplateInput], PromptTemplateInput[Any]]:
    def system_template_func(
        template: PromptTemplateInput[Any],
    ) -> PromptTemplateInput[Any]:
        return template.update(
            defaults={
                "instructions": instructions
                or "You are a helpful assistant that uses tools to answer questions."
            }
        )

    return system_template_func


def tool_no_result_error_template_func(
    template: PromptTemplateInput[Any],
) -> PromptTemplateInput[Any]:
    return template.fork(customizer=no_result_customizer)


def tool_not_found_error_template_func(
    template: PromptTemplateInput[Any],
) -> PromptTemplateInput[Any]:
    return template.fork(customizer=not_found_customizer)


class BeeAILocalAgent(Agent):
    """
    BeeAILocalAgent extends the Agent class to load and run a specific agent.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified BeeAI agent.

        Args:
            agent_name (str): The name of the agent.
        """
        super().__init__(agent)
        self.mcp_stack = AsyncExitStack()
        self.agent = None

        # Initialize model parameters from spec
        spec_dict = agent.get("spec", {})
        self.model_params = self._initialize_model_parameters(spec_dict)

    def _initialize_model_parameters(self, agent_spec: dict) -> ChatModelParameters:
        """
        Initialize model parameters from agent spec.

        Args:
            agent_spec (dict): The agent spec dictionary from YAML.

        Returns:
            ChatModelParameters: ChatModelParameters object with configured values.
        """
        spec_params = agent_spec.get("model_parameters", {})
        params_dict = {}

        # temperature
        temperature = spec_params.get("temperature")
        if temperature is not None:
            if 0.0 <= temperature <= 2.0:
                params_dict["temperature"] = temperature
                self.print(
                    f"INFO [BeeAIAgent {self.agent_name}]: Using temperature: {temperature}"
                )
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: temperature must be between 0.0 and 2.0, got {temperature}. Ignoring."
                )

        # max_tokens
        max_tokens = spec_params.get("max_tokens")
        if max_tokens is not None:
            if max_tokens > 0:
                params_dict["max_tokens"] = max_tokens
                self.print(
                    f"INFO [BeeAIAgent {self.agent_name}]: Using max_tokens: {max_tokens}"
                )
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: max_tokens must be positive, got {max_tokens}. Ignoring."
                )

        # top_p
        top_p = spec_params.get("top_p")
        if top_p is not None:
            if 0.0 <= top_p <= 1.0:
                params_dict["top_p"] = top_p
                self.print(f"INFO [BeeAIAgent {self.agent_name}]: Using top_p: {top_p}")
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: top_p must be between 0.0 and 1.0, got {top_p}. Ignoring."
                )

        # top_k
        top_k = spec_params.get("top_k")
        if top_k is not None:
            if top_k > 0:
                params_dict["top_k"] = top_k
                self.print(f"INFO [BeeAIAgent {self.agent_name}]: Using top_k: {top_k}")
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: top_k must be positive, got {top_k}. Ignoring."
                )

        # frequency_penalty
        frequency_penalty = spec_params.get("frequency_penalty")
        if frequency_penalty is not None:
            if -2.0 <= frequency_penalty <= 2.0:
                params_dict["frequency_penalty"] = frequency_penalty
                self.print(
                    f"INFO [BeeAIAgent {self.agent_name}]: Using frequency_penalty: {frequency_penalty}"
                )
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: frequency_penalty must be between -2.0 and 2.0, got {frequency_penalty}. Ignoring."
                )

        # presence_penalty
        presence_penalty = spec_params.get("presence_penalty")
        if presence_penalty is not None:
            if -2.0 <= presence_penalty <= 2.0:
                params_dict["presence_penalty"] = presence_penalty
                self.print(
                    f"INFO [BeeAIAgent {self.agent_name}]: Using presence_penalty: {presence_penalty}"
                )
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: presence_penalty must be between -2.0 and 2.0, got {presence_penalty}. Ignoring."
                )

        # stop_sequences (BeeAI uses 'stop' parameter)
        stop_sequences = spec_params.get("stop_sequences")
        if stop_sequences is not None:
            if isinstance(stop_sequences, list) and all(
                isinstance(s, str) for s in stop_sequences
            ):
                params_dict["stop"] = stop_sequences
                self.print(
                    f"INFO [BeeAIAgent {self.agent_name}]: Using stop_sequences: {stop_sequences}"
                )
            else:
                self.print(
                    f"WARN [BeeAIAgent {self.agent_name}]: stop_sequences must be a list of strings. Ignoring."
                )

        return ChatModelParameters(**params_dict)

    async def _create_agent(self):
        if find_provider_def(self.agent_model.split(":")[0]) is not None:
            llm = ChatModel.from_name(
                self.agent_model, base_url=self.agent_url, parameters=self.model_params
            )
        else:
            llm = OllamaChatModel(
                self.agent_model, base_url=self.agent_url, parameters=self.model_params
            )

        templates: dict[str, Any] = {
            "user": user_template_func,
            "system": get_system_template_func(self.agent_instr),
            "tool_no_result_error": tool_no_result_error_template_func,
            "tool_not_found_error": tool_not_found_error_template_func,
        }

        tools: list[AnyTool] = []
        embedded_tools = []

        weather_tools = ["weather", "openmeteo", "openmeteotool"]
        if any(tool in weather_tools for tool in [x.lower() for x in self.agent_tools]):
            tools.append(OpenMeteoTool())
        embedded_tools.extend(weather_tools)

        search_tools = ["web_search", "search", "duckduckgo", "duckduckgosearchtool"]
        if any(tool in search_tools for tool in [x.lower() for x in self.agent_tools]):
            tools.append(DuckDuckGoSearchTool())
        embedded_tools.extend(search_tools)

        code_tools = ["code_interpreter", "code", "pythontool"]
        if any(tool in code_tools for tool in [x.lower() for x in self.agent_tools]):
            tools.append(
                PythonTool(
                    os.getenv("CODE_INTERPRETER_URL", "http://localhost:50081"),
                    LocalPythonStorage(
                        local_working_dir=tempfile.mkdtemp("code_interpreter_source"),
                        interpreter_working_dir=os.getenv(
                            "CODE_INTERPRETER_TMPDIR", "./tmp/code_interpreter_target"
                        ),
                    ),
                )
            )
        embedded_tools.extend(code_tools)

        if self.agent_code:
            sandbox_tool = await SandboxTool.from_source_code(
                url=os.getenv("CODE_INTERPRETER_URL", "http://localhost:50081"),
                source_code=self.agent_code,
            )
            tools.append(sandbox_tool)
            self.print(sandbox_tool.name)

        for tool in self.agent_tools:
            if tool.lower() not in embedded_tools:
                mcp_tools = await get_mcp_tools(tool.lower(), MCPTool, self.mcp_stack)
                tools.extend(mcp_tools)

        self.agent = ToolCallingAgent(
            llm=llm,
            templates=templates,
            tools=tools,
            memory=UnconstrainedMemory(),
            meta=AgentMeta(
                name=self.agent_name, description=self.agent_desc, tools=tools
            ),
        )

    def _process_agent_events(self, data: Any, event: EventMeta) -> None:
        """Process agent events and log appropriately"""

        if event.name == "error":
            self.print(f"Agent 🤖 : {FrameworkError.ensure(data.error).explain()}")
        elif event.name == "retry":
            self.print("Agent 🤖 : retrying the action...")
        elif event.name == "update":
            self.print(f"Agent({data.update.key}) 🤖 : {data.update.parsed_value}")
        elif event.name == "start":
            self.print("Agent 🤖 : starting new iteration")
        elif event.name == "success":
            self.print("Agent 🤖 : success")

    def _observer(self, emitter: Emitter) -> None:
        """Observer"""
        emitter.on("*", self._process_agent_events, EmitterOptions(match_nested=False))

    async def run(self, prompt: str, context=None, step_index=None) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
            context (dict, optional): Context dictionary containing outputs from previous steps.
            step_index (int, optional): Index of the current step in the workflow.
        """
        await self._create_agent() if not self.agent else None

        self.print(f"Running {self.agent_name}...\n")
        response = await self.agent.run(
            prompt=prompt,
            execution=AgentExecutionConfig(
                max_retries_per_step=3, total_max_retries=10, max_iterations=20
            ),
            signal=AbortSignal.timeout(2 * 60 * 1000),
        ).observe(self._observer)
        answer = response.result.text
        await self.mcp_stack.aclose()
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer

    async def run_streaming(self, prompt: str, context=None, step_index=None) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
            context (dict, optional): Context dictionary containing outputs from previous steps.
            step_index (int, optional): Index of the current step in the workflow.
        """
        await self._create_agent() if not self.agent else None

        self.print(f"Running {self.agent_name}...\n")
        response = await self.agent.run(
            prompt=prompt,
            execution=AgentExecutionConfig(
                max_retries_per_step=3, total_max_retries=10, max_iterations=20
            ),
            signal=AbortSignal.timeout(2 * 60 * 1000),
        ).observe(self._observer)
        answer = response.result.text
        await self.mcp_stack.aclose()
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer
