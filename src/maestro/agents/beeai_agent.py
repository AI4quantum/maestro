#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import dotenv
import requests
import json

from openai import AssistantEventHandler, OpenAI
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads.runs import RunStep, RunStepDelta, ToolCall

from typing import Any
from pydantic import BaseModel

from beeai_framework.adapters.ollama import OllamaChatModel
from beeai_framework.agents import AgentExecutionConfig
from beeai_framework.agents.react import ReActAgent
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

        url = f"{os.getenv('BEE_API')}/v1/assistants"
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
            base_url=f"{os.getenv('BEE_API')}/v1", api_key=os.getenv("BEE_API_KEY")
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
            base_url=f"{os.getenv('BEE_API')}/v1", api_key=os.getenv("BEE_API_KEY")
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


def system_template_func(
    template: PromptTemplateInput[Any], instructions: str
) -> PromptTemplateInput[Any]:
    return template.update(defaults={"instructions": instructions.strip()})


def tool_no_result_error_template_func(
    template: PromptTemplateInput[Any],
) -> PromptTemplateInput[Any]:
    return template.fork(customizer=no_result_customizer)


def tool_not_found_error_template_func(
    template: PromptTemplateInput[Any],
) -> PromptTemplateInput[Any]:
    return template.fork(customizer=not_found_customizer)


def process_agent_events(data: Any, event: EventMeta) -> None:
    """Process agent events and log appropriately"""

    if event.name == "error":
        print("Agent 🤖 : ", FrameworkError.ensure(data.error).explain())
    elif event.name == "success":
        print("Agent 🤖 : ", "success")


def observer(emitter: Emitter) -> None:
    """Observer"""
    emitter.on("*", process_agent_events, EmitterOptions(match_nested=False))


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

        llm = OllamaChatModel(self.agent_model)

        templates: dict[str, Any] = {
            "user": lambda template: template.fork(customizer=user_customizer),
            "system": lambda template: template.update(
                defaults={
                    "instructions": "You are a helpful assistant that uses tools to answer questions."
                }
            ),
            "tool_no_result_error": lambda template: template.fork(
                customizer=no_result_customizer
            ),
            "tool_not_found_error": lambda template: template.fork(
                customizer=not_found_customizer
            ),
        }

        tools: list[AnyTool] = [
            # WikipediaTool(),
            OpenMeteoTool(),
            DuckDuckGoSearchTool(),
        ]

        self.agent = ReActAgent(
            llm=llm, templates=templates, tools=tools, memory=UnconstrainedMemory()
        )

    async def run(self, prompt: str) -> str:
        """
        Runs the BeeAI agent with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """

        self.print(f"Running {self.agent_name}...\n")
        response = await self.agent.run(
            prompt=prompt,
            execution=AgentExecutionConfig(
                max_retries_per_step=3, total_max_retries=10, max_iterations=20
            ),
            signal=AbortSignal.timeout(2 * 60 * 1000),
        ).observe(observer)
        answer = response.result.text
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer

    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode with the given prompt.
        Args:
            prompt (str): The prompt to run the agent with.
        """
        self.print(f"Running {self.agent_name}...\n")
        response = await self.agent.run(
            prompt=prompt,
            execution=AgentExecutionConfig(
                max_retries_per_step=3, total_max_retries=10, max_iterations=20
            ),
            signal=AbortSignal.timeout(2 * 60 * 1000),
        ).observe(observer)
        answer = response.result.text
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return answer
