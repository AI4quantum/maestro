# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Common utility functions for agents."""

import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
from typing import Any, Dict

try:
    import tiktoken
except ImportError:
    tiktoken = None


def is_url(text):
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_filepath(text, yaml_file):
    if os.path.isabs(text) and os.path.exists(text):
        return text
    base_path = os.path.dirname(yaml_file)
    path = os.path.join(base_path, text)
    if os.path.exists(path):
        return path
    return None


def get_content(text, yaml_file):
    if text is None:
        return None
    if isinstance(text, list):
        return text
    if is_url(text):
        if "gist.github" in text:
            text += "/raw"
        elif "github" in text:
            text += "?raw=true"
        with urlopen(text) as response:
            return response.read().decode("utf-8")
    path = get_filepath(text, yaml_file)
    if path is not None:
        return Path(path).read_text()
    return text


def count_tokens(text: str, agent_name: str = "Unknown", print_func=None) -> int:
    """
    Count tokens in text using tiktoken with fallback to word-based estimation.

    Args:
        text: The text to count tokens in
        agent_name: Name of the agent for logging purposes
        print_func: Optional print function for logging

    Returns:
        Number of tokens in the text
    """
    try:
        if tiktoken is None:
            if print_func:
                print_func(
                    f"WARN [{agent_name}]: tiktoken not available, using word-based estimation"
                )
            words = len(text.split())
            return int(words * 0.75)

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        if print_func:
            print_func(
                f"WARN [{agent_name}]: Could not count tokens with tiktoken: {e}"
            )
        words = len(text.split())
        return int(words * 0.75)


def track_token_usage(
    prompt: str, response: str, agent_name: str = "Unknown", print_func=None
) -> Dict[str, int]:
    """
    Track token usage for prompt and response.

    Args:
        prompt: The prompt text
        response: The response text
        agent_name: Name of the agent for logging purposes
        print_func: Optional print function for logging

    Returns:
        Dictionary containing prompt_tokens, response_tokens, and total_tokens
    """
    prompt_tokens = count_tokens(prompt, agent_name, print_func)
    response_tokens = count_tokens(response, agent_name, print_func)
    total_tokens = prompt_tokens + response_tokens

    if print_func:
        print_func(
            f"INFO [{agent_name}]: Tokens - Prompt: {prompt_tokens}, Response: {response_tokens}, Total: {total_tokens}"
        )

    return {
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "total_tokens": total_tokens,
    }


class TokenUsageExtractor:
    """
    Utility class for extracting token usage information from various result objects.
    Handles different formats and structures that may contain token usage data.
    """

    @staticmethod
    def extract_from_result(
        result: Any, agent_name: str = "Unknown", print_func=None
    ) -> Dict[str, int]:
        """
        Extract token usage from a result object.

        Args:
            result: The result object to extract token usage from
            agent_name: Name of the agent for logging purposes
            print_func: Optional print function for logging

        Returns:
            Dictionary containing prompt_tokens, response_tokens, and total_tokens
        """
        token_usage = {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}

        try:
            if TokenUsageExtractor._extract_from_usage_object(
                result, token_usage, agent_name, print_func
            ):
                return token_usage

            if TokenUsageExtractor._extract_from_messages(
                result, token_usage, agent_name, print_func
            ):
                return token_usage

            if TokenUsageExtractor._extract_from_direct_attributes(
                result, token_usage, agent_name, print_func
            ):
                return token_usage

        except Exception as e:
            if print_func:
                print_func(
                    f"DEBUG [{agent_name}]: Could not extract token usage from result: {e}"
                )

        return token_usage

    @staticmethod
    def _extract_from_usage_object(
        result: Any, token_usage: Dict[str, int], agent_name: str, print_func=None
    ) -> bool:
        """Extract token usage from result.usage object."""
        if not hasattr(result, "usage"):
            return False

        usage = result.usage
        if not usage:
            return False

        extracted = False
        if hasattr(usage, "prompt_tokens"):
            token_usage["prompt_tokens"] = usage.prompt_tokens
            extracted = True
        if hasattr(usage, "completion_tokens"):
            token_usage["response_tokens"] = usage.completion_tokens
            extracted = True
        if hasattr(usage, "total_tokens"):
            token_usage["total_tokens"] = usage.total_tokens
            extracted = True

        if extracted and print_func:
            print_func(
                f"INFO [{agent_name}]: Extracted token usage from result - "
                f"Prompt: {token_usage['prompt_tokens']}, "
                f"Response: {token_usage['response_tokens']}, "
                f"Total: {token_usage['total_tokens']}"
            )

        return extracted

    @staticmethod
    def _extract_from_messages(
        result: Any, token_usage: Dict[str, int], agent_name: str, print_func=None
    ) -> bool:
        """Extract token usage from result.messages."""
        if not hasattr(result, "messages"):
            return False

        for message in result.messages:
            if hasattr(message, "usage") and message.usage:
                usage = message.usage
                extracted = False

                if hasattr(usage, "prompt_tokens"):
                    token_usage["prompt_tokens"] = usage.prompt_tokens
                    extracted = True
                if hasattr(usage, "completion_tokens"):
                    token_usage["response_tokens"] = usage.completion_tokens
                    extracted = True
                if hasattr(usage, "total_tokens"):
                    token_usage["total_tokens"] = usage.total_tokens
                    extracted = True

                if extracted and print_func:
                    print_func(
                        f"INFO [{agent_name}]: Extracted token usage from message - "
                        f"Prompt: {token_usage['prompt_tokens']}, "
                        f"Response: {token_usage['response_tokens']}, "
                        f"Total: {token_usage['total_tokens']}"
                    )
                return True

        return False

    @staticmethod
    def _extract_from_direct_attributes(
        result: Any, token_usage: Dict[str, int], agent_name: str, print_func=None
    ) -> bool:
        """Extract token usage from direct attributes on the result object."""
        extracted = False

        for attr in ["prompt_tokens", "completion_tokens", "total_tokens"]:
            if hasattr(result, attr):
                value = getattr(result, attr)
                if attr == "prompt_tokens":
                    token_usage["prompt_tokens"] = value
                    extracted = True
                elif attr == "completion_tokens":
                    token_usage["response_tokens"] = value
                    extracted = True
                elif attr == "total_tokens":
                    token_usage["total_tokens"] = value
                    extracted = True

        if hasattr(result, "usage"):
            usage_value = getattr(result, "usage")
            if hasattr(usage_value, "total_tokens"):
                token_usage["total_tokens"] = usage_value.total_tokens
                extracted = True
                if hasattr(usage_value, "prompt_tokens"):
                    token_usage["prompt_tokens"] = usage_value.prompt_tokens
                if hasattr(usage_value, "completion_tokens"):
                    token_usage["response_tokens"] = usage_value.completion_tokens

        if extracted and token_usage["total_tokens"] > 0 and print_func:
            print_func(
                f"INFO [{agent_name}]: Found token usage in result - "
                f"Prompt: {token_usage['prompt_tokens']}, "
                f"Response: {token_usage['response_tokens']}, "
                f"Total: {token_usage['total_tokens']}"
            )

        return extracted
