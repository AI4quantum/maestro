#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from typing import Dict, Any


def eval_expression(expression, prompt):
    """
    Evaluate an expression with a given prompt.

    Args:
        expression (str): The expression to evaluate.
        prompt: The value bound to `input` when evaluating.
    Returns:
        The result of evaluating the expression.
    """
    local = {"input": prompt}
    return eval(expression, local)


def convert_to_list(s):
    if s[0] != "[" or s[-1] != "]":
        raise ValueError("parallel or loop prompt is not a list string")
    result = s[1:-1].split(",")
    return result


def aggregate_token_usage_from_agents(agents: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate token usage from all agents in a workflow.

    Args:
        agents: Dictionary of agent_name -> agent_instance

    Returns:
        Dictionary containing aggregated token usage:
        - total_prompt_tokens: Sum of all prompt tokens
        - total_response_tokens: Sum of all response tokens
        - total_tokens: Sum of all total tokens
        - agent_token_usage: Individual token usage per agent
    """
    total_token_usage = {
        "total_prompt_tokens": 0,
        "total_response_tokens": 0,
        "total_tokens": 0,
        "agent_token_usage": {},
    }

    for agent_name, agent in agents.items():
        if hasattr(agent, "get_token_usage"):
            token_usage = agent.get_token_usage()
            total_token_usage["agent_token_usage"][agent_name] = token_usage
            if "prompt_tokens" in token_usage:
                total_token_usage["total_prompt_tokens"] += token_usage.get(
                    "prompt_tokens", 0
                )
                total_token_usage["total_response_tokens"] += token_usage.get(
                    "response_tokens", 0
                )
                total_token_usage["total_tokens"] += token_usage.get("total_tokens", 0)

    return total_token_usage
