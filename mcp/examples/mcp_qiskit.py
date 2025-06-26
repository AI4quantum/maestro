#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import asyncio
import logging
import os
import sys
import traceback
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from beeai_framework.agents import AgentExecutionConfig
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend import ChatModel, ChatModelParameters
from beeai_framework.emitter import Emitter, EventMeta
from beeai_framework.errors import FrameworkError
from beeai_framework.logger import Logger
from beeai_framework.memory import TokenMemory
from beeai_framework.tools import AnyTool
from beeai_framework.tools.mcp import MCPTool
from beeai_framework.tools.code import SandboxTool

import sys

from pydantic import BaseModel
from termcolor import colored

from beeai_framework.utils.models import ModelLike, to_model_optional

# Load environment variables
load_dotenv()

class ReaderOptions(BaseModel):
    fallback: str = ""
    input: str = "User 👤 : "
    allow_empty: bool = False

class ConsoleReader:
    def __init__(self, options: ModelLike[ReaderOptions] | None = None) -> None:
        options = to_model_optional(ReaderOptions, options) or ReaderOptions()
        self.fallback = options.fallback
        self.input = options.input
        self.allow_empty = options.allow_empty

    def __iter__(self) -> "ConsoleReader":
        print("Interactive session has started. To escape, input 'q' and submit.")
        return self

    def __next__(self) -> str:
        try:
            while True:
                prompt = input(colored(self.input, "cyan", attrs=["bold"])).strip()
                if not sys.stdin.isatty():
                    print(prompt)

                if prompt == "q":
                    raise StopIteration

                prompt = prompt if prompt else self.fallback

                if not prompt and not self.allow_empty:
                    print("Error: Empty prompt is not allowed. Please try again.")
                    continue

                return prompt
        except (EOFError, KeyboardInterrupt):
            print()
            exit()

    def write(self, role: str, data: str) -> None:
        print(colored(role, "red", attrs=["bold"]), data)

    def prompt(self) -> str | None:
        for prompt in self:
            return prompt
        exit()

    def ask_single_question(self, query_message: str) -> str:
        answer = input(colored(query_message, "cyan", attrs=["bold"]))
        return answer.strip()

reader = ConsoleReader()

# Configure logging - using DEBUG instead of trace
logger = Logger("app", level=logging.DEBUG)

# local MCP runtime
token = os.getenv("IQP_TOKEN", "None")
channel = os.getenv("IQP_CHANNEL", "None")
instance = os.getenv("IQP_INSTANCE", "None")
server_params = StdioServerParameters(
    command="python",
    args=[os.path.dirname(os.path.abspath(__file__))+"/../mcptools/qiskit_mcp.py"],
    env={"IQP_TOKEN": token, "IQP_CHANNEL": channel, "IQP_INSTANCE": instance }
)

async def create_agent(session: ClientSession) -> ReActAgent:
    """Create and configure the agent with tools and LLM"""

    # Other models to try:
    # "llama3.1"
    # "granite3.1-dense"
    # "deepseek-r1"
    # ensure the model is pulled before running
    llm = ChatModel.from_name(
        "ollama:llama3.1",
        ChatModelParameters(temperature=0),
    )

    # Configure tools
    alltools = await MCPTool.from_client(session)
    tools: list[AnyTool] = list(filter(lambda tool: True , alltools))
    for tool in tools:
        reader.write("tools", tool.name)

    # Create agent with memory and tools
    agent = ReActAgent(llm=llm, tools=tools, memory=TokenMemory(llm))
    return agent


def process_agent_events(data: Any, event: EventMeta) -> None:
    """Process agent events and log appropriately"""

    if event.name == "error":
        reader.write("Agent 🤖 : ", data)
    elif event.name == "retry":
        reader.write("Agent 🤖 : ", "retrying the action...")
    elif event.name == "update":
        reader.write(f"Agent({data.update.key}) 🤖 : ", data.update.parsed_value)
    elif event.name == "start":
        reader.write("Agent 🤖 : ", "starting new iteration")
    elif event.name == "success":
        reader.write("Agent 🤖 : ", "success")


def observer(emitter: Emitter) -> None:
    emitter.on("*.*", process_agent_events)


async def main() -> None:
    """Main application loop"""

    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        # Create agent
        agent = await create_agent(session)

        # Main interaction loop with user input
        for prompt in reader:
            # Run agent with the prompt
            response = await agent.run(
                prompt=prompt,
                execution=AgentExecutionConfig(max_retries_per_step=3, total_max_retries=10, max_iterations=20),
            ).observe(observer)

            reader.write("Agent 🤖 : ", response.result.text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except FrameworkError as e:
        traceback.print_exc()
        sys.exit(e.explain())


