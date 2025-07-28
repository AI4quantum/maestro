#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import dotenv
import tempfile
import requests
import json

from beeai_framework.adapters.ollama import OllamaChatModel
from beeai_framework.agents.tool_calling import ToolCallingAgent
from beeai_framework.backend import ChatModel
from beeai_framework.tools.code import PythonTool, LocalPythonStorage, SandboxTool
from openai import AssistantEventHandler, OpenAI
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads.runs import RunStep, RunStepDelta, ToolCall

from typing import Any, Callable
from pydantic import BaseModel

from beeai_framework.agents import AgentExecutionConfig, AgentMeta
from beeai_framework.emitter import Emitter, EmitterOptions, EventMeta
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.template import PromptTemplateInput
from beeai_framework.tools import AnyTool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.weather import OpenMeteoTool
from beeai_framework.utils import AbortSignal

from maestro.agents.agent import Agent

dotenv.load_dotenv()


class BeeAIAgent(Agent):
    """
    BeeAIAgent extends the Agent class to load and run a specific agent.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified BeeAI agent.

        Args:
            agent_name (str): The name of the agent.
        """
        super().__init__(agent)

        self.base_url = f"{agent['spec'].get('url', os.getenv('BEE_API'))}/v1"

        url = f"{self.base_url}/assistants"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer sk-proj-testkey",
            "Content-Type": "application/json",
        }
        response = requests.request("GET", url, headers=headers).json()
        for agent in response["data"]:
            if agent["name"] == self.agent_name and agent["model"] == self.agent_model:
                self.agent_id = agent["id"]
                return

        payload_dict = {
            "tools": [
                {"type": "code_interpreter"},
                {"type": "system", "system": {"id": "web_search"}},
                {"type": "system", "system": {"id": "weather"}},
            ],
            "name": self.agent_name,
            "description": self.agent_desc,
            "instructions": self.instructions.strip(),
            "metadata": {},
            "model": self.agent_model,
            "agent": "bee",
            "top_p": 0.8,
            "temperature": 0.1,
        }
        payload = json.dumps(payload_dict)
        response = requests.request("POST", url, headers=headers, data=payload).json()
        self.agent_id = response["id"]

    async def run(self, prompt: str) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        self.print(f"Running {self.agent_name}...\n")
        client = OpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=os.getenv("BEE_API_KEY", "dummy_key"),
        )
        # TODO: Unused currently
        # assistant = client.beta.assistants.retrieve(self.agent_id)
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": str(prompt)}]
        )
        client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=self.agent_id
        )
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        answer = messages.data[0].content[0].text.value
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer

    def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        self.print(f"Running {self.agent_name}...\n")
        client = OpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=os.getenv("BEE_API_KEY", "dummy_key"),
        )
        # TODO: Unused currently
        # assistant = client.beta.assistants.retrieve(self.agent_id)
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": str(prompt)}]
        )

        class EventHandler(AssistantEventHandler):
            """NOTE: Streaming is work in progress, not all methods are implemented"""

            def on_event(self, event: AssistantStreamEvent) -> None:
                self.print(f"event > {event.event}")

            def on_text_delta(self, delta, snapshot):
                self.print(delta.value, end="", flush=True)

            def on_run_step_delta(self, delta: RunStepDelta, snapshot: RunStep) -> None:
                if delta.step_details.type != "tool_calls":
                    self.print(
                        f"{delta.step_details.type} > {getattr(delta.step_details, delta.step_details.type)}"
                    )

            def on_tool_call_created(self, tool_call: ToolCall) -> None:
                """Not implemented yet"""

            def on_tool_call_done(self, tool_call: ToolCall) -> None:
                """Not implemented yet"""

        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=self.agent_id,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        answer = messages.data[0].content[0].text.value
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer


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
        self.agent = None

    async def _create_agent(self):
        if len(self.agent_model.split("/")) < 2:
            llm = OllamaChatModel(self.agent_model, base_url=self.agent_url)
        else:
            llm = ChatModel.from_name(self.agent_model, base_url=self.agent_url)

        templates: dict[str, Any] = {
            "user": user_template_func,
            "system": get_system_template_func(self.agent_instr),
            "tool_no_result_error": tool_no_result_error_template_func,
            "tool_not_found_error": tool_not_found_error_template_func,
        }

        tools: list[AnyTool] = []

        if any(
            tool in ["weather", "openmeteo", "openmeteotool"]
            for tool in [x.lower() for x in self.agent_tools]
        ):
            tools.append(OpenMeteoTool())

        if any(
            tool in ["web_search", "search", "duckduckgo", "duckduckgosearchtool"]
            for tool in [x.lower() for x in self.agent_tools]
        ):
            tools.append(DuckDuckGoSearchTool())

        if any(
            tool in ["code_interpreter", "code", "pythontool"]
            for tool in [x.lower() for x in self.agent_tools]
        ):
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

        if self.agent_code:
            sandbox_tool = await SandboxTool.from_source_code(
                url=os.getenv("CODE_INTERPRETER_URL", "http://localhost:50081"),
                source_code=self.agent_code,
            )
            tools.append(sandbox_tool)
            self.print(sandbox_tool.name)

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

    async def run(self, prompt: str) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
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
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer

    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
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
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer
