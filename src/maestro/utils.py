#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0


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
