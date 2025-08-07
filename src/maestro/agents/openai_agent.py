#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import json
import traceback
from typing import Final, List, Optional, Any, Dict

import logfire
import tiktoken

# raw responses for streaming
from openai.types.responses import ResponseTextDeltaEvent

from agents import (
    Agent as UnderlyingAgent,
    Runner as UnderlyingRunner,
    AsyncOpenAI as UnderlyingClient,
    set_tracing_disabled,
    set_default_openai_client,
    set_default_openai_api,
    Tool,
    ModelSettings,
    WebSearchTool,
)
from agents.extensions.models.litellm_model import LitellmModel

from maestro.agents.agent import Agent as MaestroAgent
from maestro.agents.openai_mcp import (
    setup_mcp_servers,
    MCPServerInstance,
    get_mcp_servers,
)

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_TOOL_NAME: Final[str] = "web_search"
TOOL_REQUIRES_RESPONSES_API: Final[bool] = True
OPENAI_DEFAULT_URL: Final[str] = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL: Final[str] = "gpt-4o-mini"


class OpenAIAgent(MaestroAgent):
    """
    Maestro Agent implementation for OpenAI and compatible APIs.
    Supports observability, MCP, streaming.
    """

    def __init__(self, agent_definition: dict) -> None:
        """
        Initializes the OpenAI agent, configures tracing, client, and tools.

        Args:
            agent_definition (dict): The agent definition dictionary from YAML.
        """
        super().__init__(agent_definition)
        self.agent_id = self.agent_name

        spec_dict = agent_definition.get("spec", {})
        self.model_name: str = spec_dict.get("model", OPENAI_DEFAULT_MODEL)
        self.base_url: str = spec_dict.get(
            "url", os.getenv("OPENAI_BASE_URL", OPENAI_DEFAULT_URL)
        )
        self.api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "dummy_key")
        self.tools: str = spec_dict.get("tools", [])

        self.uses_chat_completions: bool = self.base_url != OPENAI_DEFAULT_URL
        self.use_litellm: bool = (
            os.getenv("MAESTRO_OPENAI_USE_LITELLM", "false").lower() == "true"
        )
        self.endpoint_has_tracing: bool = self.base_url == OPENAI_DEFAULT_URL
        self.print(
            f"DEBUG [OpenAIAgent {self.agent_name}]: Using Base URL: {self.base_url}"
        )
        self.print(
            f"INFO [OpenAIAgent {self.agent_name}]: Using Model: {self.model_name}"
        )
        self.client: UnderlyingClient = UnderlyingClient(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        self.static_tools: List[Tool] = self._initialize_static_tools(spec_dict)
        self.max_tokens: Optional[int] = self._initialize_max_tokens()
        self.extra_headers: Optional[Dict[str, str]] = self._initialize_extra_headers()
        self._configure_agents_library()

        self.prompt_tokens = 0
        self.response_tokens = 0
        self.total_tokens = 0

    def _configure_agents_library(self) -> None:
        set_default_openai_client(client=self.client, use_for_tracing=True)

        # Only use OpenAPI tracing for official endpoint
        set_tracing_disabled(not self.endpoint_has_tracing)

        # Logfire instruments OpenAPI calls with OpenTelemetry (logfire SAAS disabled)
        # Set OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
        logfire.configure(
            service_name=self.agent_name,
            send_to_logfire=False,
            distributed_tracing=True,
        )
        logfire.instrument_openai(self.client)
        logfire.instrument_openai_agents()

        if self.use_litellm:
            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: LiteLLM enabled. API selection handled by LiteLLM."
            )
        else:
            # responses API is new api - assume compatible endpoints don't yet support
            if self.uses_chat_completions:
                set_default_openai_api("chat_completions")
                self.print(
                    f"INFO [OpenAIAgent {self.agent_name}]: Using 'chat_completions' API (via OpenAI client)."
                )
            else:
                self.print(
                    f"INFO [OpenAIAgent {self.agent_name}]: Assuming 'Responses' API (via OpenAI client)."
                )

    # websearch they have other dependencies - so restrict to websearch initially.
    def _initialize_static_tools(self, agent_spec: dict) -> List[Tool]:
        agent_tool_names: Optional[List[str]] = agent_spec.get("tools")
        openai_tools: List[Tool] = []
        tool_requested = agent_tool_names and SUPPORTED_TOOL_NAME in agent_tool_names

        if not tool_requested:
            if agent_tool_names:
                self.print(
                    f"WARN [OpenAIAgent {self.agent_name}]: Tools {agent_tool_names} ignore unsupported tool: '{SUPPORTED_TOOL_NAME}'."
                )
            else:
                self.print(
                    f"DEBUG [OpenAIAgent {self.agent_name}]: No static tools requested."
                )
            return openai_tools

        self.print(
            f"DEBUG [OpenAIAgent {self.agent_name}]: Tool '{SUPPORTED_TOOL_NAME}' requested."
        )

        if TOOL_REQUIRES_RESPONSES_API and self.uses_chat_completions:
            self.print(
                f"WARN [OpenAIAgent {self.agent_name}]: Skipping tool '{SUPPORTED_TOOL_NAME}' due to API incompatibility."
            )
            return openai_tools

        try:
            tool_instance = WebSearchTool()
            openai_tools.append(tool_instance)
            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: Added static tool: {SUPPORTED_TOOL_NAME}"
            )
        except Exception as e:
            self.print(
                f"ERROR [OpenAIAgent {self.agent_name}]: Failed to instantiate tool '{SUPPORTED_TOOL_NAME}': {e}"
            )
            return []

        return openai_tools

    # TODO: Large context windows need checking. Including with LitelLM enabled
    def _initialize_max_tokens(self) -> Optional[int]:
        """Reads and validates MAESTRO_OPENAI_MAX_TOKENS environment variable."""
        max_tokens_str = os.getenv("MAESTRO_OPENAI_MAX_TOKENS")
        if max_tokens_str:
            try:
                max_tokens_int = int(max_tokens_str)
                if max_tokens_int > 0:
                    self.print(
                        f"INFO [OpenAIAgent {self.agent_name}]: Using max_tokens: {max_tokens_int}"
                    )
                    # Even if set, trace shows openai ignoring, also set OLLAMA_CONTEXT_LENGTH
                    # https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-specify-the-context-window-size
                    os.environ["OLLAMA_CONTEXT_LENGTH"] = str(max_tokens_int)
                    self.print(
                        f"DEBUG [OpenAIAgent {self.agent_name}]: Set OLLAMA_CONTEXT_LENGTH to {max_tokens_int}"
                    )
                    return max_tokens_int
                else:
                    self.print(
                        f"WARN [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_MAX_TOKENS must be a positive integer, but got '{max_tokens_str}'. Ignoring."
                    )
            except ValueError:
                self.print(
                    f"WARN [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_MAX_TOKENS is not a valid integer: '{max_tokens_str}'. Ignoring."
                )

        return None

    def _initialize_extra_headers(self) -> Optional[Dict[str, str]]:
        """Reads and parses MAESTRO_OPENAI_EXTRA_HEADERS environment variable.
        Value should be in JSON format, for example:
        MAESTRO_OPENAI_EXTRA_HEADERS={"MY_API_KEY": "TEST1234567890NOTAKEY"}
        """
        headers_str = os.getenv("MAESTRO_OPENAI_EXTRA_HEADERS")
        if headers_str:
            try:
                headers_dict = json.loads(headers_str)
                if isinstance(headers_dict, dict):
                    valid_headers = {str(k): str(v) for k, v in headers_dict.items()}
                    # don't log: may contain API key (secret)
                    obfuscated_headers = {k: "*****" for k in valid_headers}
                    self.print(
                        f"INFO [OpenAIAgent {self.agent_name}]: Using extra headers: {obfuscated_headers} (values redacted in log)"
                    )
                    return valid_headers
                else:
                    self.print(
                        f"WARN [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_EXTRA_HEADERS is not a valid JSON dictionary: '{headers_str}'. Ignoring."
                    )
            except json.JSONDecodeError:
                self.print(
                    f"WARN [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_EXTRA_HEADERS contains invalid JSON: '{headers_str}'. Ignoring."
                )
            except Exception as e:
                self.print(
                    f"WARN [OpenAIAgent {self.agent_name}]: Error processing MAESTRO_OPENAI_EXTRA_HEADERS='{headers_str}': {e}. Ignoring."
                )
        return None

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            self.print(
                f"WARN [OpenAIAgent {self.agent_name}]: Could not count tokens with tiktoken: {e}"
            )
            words = len(text.split())
            return int(words * 0.75)

    def _track_tokens(self, prompt: str, response: str) -> Dict[str, int]:
        """Track token usage for prompt and response."""
        prompt_tokens = self._count_tokens(prompt)
        response_tokens = self._count_tokens(response)
        total_tokens = prompt_tokens + response_tokens

        self.prompt_tokens = prompt_tokens
        self.response_tokens = response_tokens
        self.total_tokens = total_tokens

        self.print(
            f"INFO [OpenAIAgent {self.agent_name}]: Tokens - Prompt: {prompt_tokens}, Response: {response_tokens}, Total: {total_tokens}"
        )

        return {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
        }

    def get_token_usage(self) -> Dict[str, int]:
        """Get current token usage statistics."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "response_tokens": self.response_tokens,
            "total_tokens": self.total_tokens,
        }

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self.prompt_tokens = 0
        self.response_tokens = 0
        self.total_tokens = 0

    async def _get_actual_token_usage(
        self, prompt: str, response: str
    ) -> Dict[str, int]:
        """Get actual token usage by making a direct API call."""
        try:
            if self.base_url == OPENAI_DEFAULT_URL or "openai" in self.base_url.lower():
                # Make a simple chat completion call to get token usage
                messages = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                ]
                completion = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=1,
                    temperature=0,
                )

                if hasattr(completion, "usage") and completion.usage:
                    return {
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "response_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens,
                    }

        except Exception as e:
            self.print(
                f"DEBUG [OpenAIAgent {self.agent_name}]: Could not get actual token usage from API: {e}"
            )

        return {
            "prompt_tokens": self._count_tokens(prompt),
            "response_tokens": self._count_tokens(response),
            "total_tokens": self._count_tokens(prompt) + self._count_tokens(response),
        }

    def _process_agent_result(self, result: Optional[Any]) -> str:
        if result is None:
            self.print(
                f"ERROR [OpenAIAgent {self.agent_name}]: Agent run did not produce a result object."
            )
            return "Error: Agent run failed to produce a result."

        self._extract_token_usage_from_result(result)
        final_output = getattr(result, "final_output", None)
        if final_output is not None:
            final_output_str = str(final_output)
            return final_output_str
        else:
            self.print(
                f"WARN [OpenAIAgent {self.agent_name}]: Agent run completed but no 'final_output' found."
            )
            messages = getattr(result, "messages", [])
            last_message_content = (
                messages[-1].content
                if messages and hasattr(messages[-1], "content")
                else "No message content available."
            )
            fallback_str = f"Agent run finished without explicit final output. Last message: {last_message_content}"
            self.print(f"DEBUG [OpenAIAgent {self.agent_name}]: {fallback_str}")
            return fallback_str

    def _extract_token_usage_from_result(self, result: Any) -> None:
        """Try to extract token usage from the result object."""
        try:
            if hasattr(result, "usage"):
                usage = result.usage
                if hasattr(usage, "prompt_tokens"):
                    self.prompt_tokens = usage.prompt_tokens
                if hasattr(usage, "completion_tokens"):
                    self.response_tokens = usage.completion_tokens
                if hasattr(usage, "total_tokens"):
                    self.total_tokens = usage.total_tokens
                self.print(
                    f"INFO [OpenAIAgent {self.agent_name}]: Extracted token usage from result - Prompt: {self.prompt_tokens}, Response: {self.response_tokens}, Total: {self.total_tokens}"
                )
                return

            if hasattr(result, "messages"):
                for message in result.messages:
                    if hasattr(message, "usage"):
                        usage = message.usage
                        if hasattr(usage, "prompt_tokens"):
                            self.prompt_tokens = usage.prompt_tokens
                        if hasattr(usage, "completion_tokens"):
                            self.response_tokens = usage.completion_tokens
                        if hasattr(usage, "total_tokens"):
                            self.total_tokens = usage.total_tokens
                        self.print(
                            f"INFO [OpenAIAgent {self.agent_name}]: Extracted token usage from message - Prompt: {self.prompt_tokens}, Response: {self.response_tokens}, Total: {self.total_tokens}"
                        )
                        return

            for attr in ["prompt_tokens", "completion_tokens", "total_tokens", "usage"]:
                if hasattr(result, attr):
                    value = getattr(result, attr)
                    if attr == "prompt_tokens":
                        self.prompt_tokens = value
                    elif attr == "completion_tokens":
                        self.response_tokens = value
                    elif attr == "total_tokens":
                        self.total_tokens = value
                    elif attr == "usage" and hasattr(value, "total_tokens"):
                        self.total_tokens = value.total_tokens
                        if hasattr(value, "prompt_tokens"):
                            self.prompt_tokens = value.prompt_tokens
                        if hasattr(value, "completion_tokens"):
                            self.response_tokens = value.completion_tokens

            if self.total_tokens > 0:
                self.print(
                    f"INFO [OpenAIAgent {self.agent_name}]: Found token usage in result - Prompt: {self.prompt_tokens}, Response: {self.response_tokens}, Total: {self.total_tokens}"
                )

        except Exception as e:
            self.print(
                f"DEBUG [OpenAIAgent {self.agent_name}]: Could not extract token usage from result: {e}"
            )
            pass

    # TODO: Cleanup streaming vs non-streaming
    # Maestro doesn't yet have support to specify streaming vs non-streaming, so these
    # 4 methods allow overriding via environment settings.
    # Can be removed once supported in framework
    async def _run_internal(self, prompt: str) -> str:
        """Internal implementation for non-streaming run."""
        result: Optional[Any] = None

        try:
            active_mcp_servers: List[MCPServerInstance]
            active_mcp_servers, mcp_stack = await setup_mcp_servers(
                print_func=self.print, agent_name=self.agent_name
            )
            maestro_mcp_servers = await get_mcp_servers(self.tools, mcp_stack)
            active_mcp_servers.extend(maestro_mcp_servers)

            async with mcp_stack:
                model_to_use: Any  # Type hint for clarity
                # LiteLLM needs more than the model name in Agents SDK
                if self.use_litellm:
                    self.print(
                        f"INFO [OpenAIAgent {self.agent_name}]: Using LiteLLM backend for model: {self.model_name}"
                    )
                    litellm_base_url = (
                        self.base_url if self.base_url != OPENAI_DEFAULT_URL else None
                    )
                    model_to_use = LitellmModel(
                        model=self.model_name,
                        api_key=self.api_key,
                        base_url=litellm_base_url,
                    )
                else:
                    model_to_use = (
                        self.model_name
                    )  # Use the string name for standard OpenAI client
                # TODO: Extend or make generic for more settings
                model_settings_dict: Dict[str, Any] = {}
                if self.max_tokens is not None:
                    model_settings_dict["max_tokens"] = self.max_tokens
                if self.extra_headers is not None:
                    model_settings_dict["extra_headers"] = self.extra_headers
                model_settings_obj = ModelSettings(**model_settings_dict)

                agent_kwargs: Dict[str, Any] = {
                    "name": self.agent_name,
                    "instructions": self.instructions,
                    "model": model_to_use,
                    "tools": self.static_tools,
                    "mcp_servers": active_mcp_servers,
                    "model_settings": model_settings_obj,
                }

                underlying_agent = UnderlyingAgent(**agent_kwargs)

                self.print(f"Running {self.agent_name} with prompt...")
                result = await UnderlyingRunner.run(underlying_agent, prompt)
                self.print(
                    f"DEBUG [OpenAIAgent {self.agent_name}]: Agent run completed."
                )
                for maestro_mcp_server in maestro_mcp_servers:
                    await maestro_mcp_server.cleanup()

        except Exception as e:
            error_msg = f"ERROR [OpenAIAgent {self.agent_name}]: Agent run failed: {e}"
            self.print(error_msg)
            self.print(traceback.format_exc())
            return f"Error during agent execution: {e}"

        # Process result and print final output once
        final_str = self._process_agent_result(result)

        if self.total_tokens == 0:
            actual_usage = await self._get_actual_token_usage(prompt, final_str)
            self.prompt_tokens = actual_usage["prompt_tokens"]
            self.response_tokens = actual_usage["response_tokens"]
            self.total_tokens = actual_usage["total_tokens"]

            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: Actual API tokens - Prompt: {self.prompt_tokens}, Response: {self.response_tokens}, Total: {self.total_tokens}"
            )

        self.print(f"Response from {self.agent_name}: {final_str}")

        return final_str

    async def _run_streaming_internal(self, prompt: str) -> str:
        final_output_chunks: List[str] = []
        last_event_was_delta = False

        self.print(f"Running {self.agent_name} with prompt (streaming)...")
        try:
            active_mcp_servers: List[MCPServerInstance]
            active_mcp_servers, mcp_stack = await setup_mcp_servers(
                print_func=self.print, agent_name=self.agent_name
            )

            async with mcp_stack:
                model_to_use: Any
                if self.use_litellm:
                    self.print(
                        f"INFO [OpenAIAgent {self.agent_name}]: Using LiteLLM backend for model: {self.model_name} (streaming)"
                    )
                    litellm_base_url = (
                        self.base_url if self.base_url != OPENAI_DEFAULT_URL else None
                    )
                    model_to_use = LitellmModel(
                        model=self.model_name,
                        api_key=self.api_key,
                        base_url=litellm_base_url,
                    )
                else:
                    model_to_use = self.model_name

                model_settings_dict: Dict[str, Any] = {}
                if self.max_tokens is not None:
                    model_settings_dict["max_tokens"] = self.max_tokens
                if self.extra_headers is not None:
                    model_settings_dict["extra_headers"] = self.extra_headers
                model_settings_obj = ModelSettings(**model_settings_dict)

                agent_kwargs: Dict[str, Any] = {
                    "name": self.agent_name,
                    "instructions": self.instructions,
                    "model": model_to_use,
                    "tools": self.static_tools,
                    "mcp_servers": active_mcp_servers,
                    "model_settings": model_settings_obj,
                }
                # Create the *OpenAI* Agent (renamed to avoid clash)
                underlying_agent = UnderlyingAgent(**agent_kwargs)

                run_result_streaming = UnderlyingRunner.run_streamed(
                    underlying_agent, prompt
                )
                stream = run_result_streaming.stream_events()
                event = None

                # TODO: Refactor some stream handling into common routine across backends? Code verbose
                async for event in stream:
                    if event.type == "raw_response_event":
                        if isinstance(event.data, ResponseTextDeltaEvent):
                            delta_value = event.data.delta
                            print(delta_value, end="", flush=True)
                            final_output_chunks.append(delta_value)
                            last_event_was_delta = True
                    elif event.type == "run_item_stream_event":
                        if last_event_was_delta:
                            print("")
                            last_event_was_delta = False

                        if event.name == "tool_called":
                            tool_call_info = getattr(event.item, "tool_call", None)
                            if tool_call_info:
                                self.print(
                                    f"DEBUG [OpenAIAgent {self.agent_name}]: Starting tool call: {getattr(tool_call_info, 'name', 'N/A')} with args: {getattr(tool_call_info, 'arguments', '{}')}"
                                )
                            else:
                                self.print(
                                    f"DEBUG [OpenAIAgent {self.agent_name}]: Starting tool call (details unavailable in event.item)"
                                )
                        elif event.name == "tool_output":
                            tool_output = getattr(event.item, "output", "N/A")
                            self.print(
                                f"DEBUG [OpenAIAgent {self.agent_name}]: Finished tool call. Output: {str(tool_output)[:100]}..."
                            )
                        elif event.name == "message_output_created":
                            # message_text = ItemHelpers.text_message_output(event.item) # Can be verbose
                            self.print(
                                f"DEBUG [OpenAIAgent {self.agent_name}]: Message output item created."
                            )
                            pass
                        elif event.name == "run_completed":
                            self.print(
                                f"DEBUG [OpenAIAgent {self.agent_name}]: Agent stream processing finished (run_item_stream_event: {event.name})."
                            )
                        else:
                            self.print(
                                f"DEBUG [OpenAIAgent {self.agent_name}]: Received run item event: {event.name}"
                            )

                    elif event.type == "agent_updated_stream_event":
                        if last_event_was_delta:
                            print("")
                            last_event_was_delta = False
                        self.print(
                            f"DEBUG [OpenAIAgent {self.agent_name}]: Agent updated to: {event.new_agent.name}"
                        )
                    else:
                        if last_event_was_delta:
                            print("")
                            last_event_was_delta = False
                        self.print(
                            f"DEBUG [OpenAIAgent {self.agent_name}]: Received unknown event type: {event.type}"
                        )

                if last_event_was_delta:
                    print("")

        except Exception as e:
            if last_event_was_delta:
                print("")
            error_msg = (
                f"ERROR [OpenAIAgent {self.agent_name}]: Agent stream failed: {e}"
            )
            self.print(error_msg)
            self.print(traceback.format_exc())
            return f"Error during agent streaming execution: {e}"

        # Create the final output from all the bits we've received
        final_output_str = "".join(final_output_chunks)

        if self.total_tokens == 0:
            actual_usage = await self._get_actual_token_usage(prompt, final_output_str)
            self.prompt_tokens = actual_usage["prompt_tokens"]
            self.response_tokens = actual_usage["response_tokens"]
            self.total_tokens = actual_usage["total_tokens"]

            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: Actual API tokens - Prompt: {self.prompt_tokens}, Response: {self.response_tokens}, Total: {self.total_tokens}"
            )

        self.print(
            f"Final Response from {self.agent_name} (streaming collected): {final_output_str}"
        )

        return final_output_str

    async def run(self, prompt: str) -> str:
        """
        Runs the agent with the given prompt, potentially overriding to streaming
        based on MAESTRO_OPENAI_STREAMING environment variable.

        Args:
            prompt (str): The prompt to run the agent with.
        """
        streaming_override = os.getenv("MAESTRO_OPENAI_STREAMING", "auto").lower()

        if streaming_override == "true":
            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_STREAMING=true, overriding run() to use streaming."
            )
            return await self._run_streaming_internal(prompt)
        elif streaming_override == "false":
            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_STREAMING=false, forcing non-streaming."
            )
            return await self._run_internal(prompt)
        else:  # auto or unset
            return await self._run_internal(prompt)

    async def run_streaming(self, prompt: str) -> str:
        """
        Runs the agent in streaming mode, potentially overriding to non-streaming
        based on MAESTRO_OPENAI_STREAMING environment variable.

        Args:
            prompt (str): The prompt to run the agent with.
        """
        streaming_override = os.getenv("MAESTRO_OPENAI_STREAMING", "auto").lower()

        if streaming_override == "true":
            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_STREAMING=true, forcing streaming."
            )
            return await self._run_streaming_internal(prompt)
        elif streaming_override == "false":
            self.print(
                f"INFO [OpenAIAgent {self.agent_name}]: MAESTRO_OPENAI_STREAMING=false, overriding run_streaming() to use non-streaming."
            )
            return await self._run_internal(prompt)
        else:  # auto or unset
            return await self._run_streaming_internal(prompt)
