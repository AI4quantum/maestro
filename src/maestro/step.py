#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from dotenv import load_dotenv
import asyncio
from maestro.utils import eval_expression, convert_to_list

load_dotenv()


class Step:
    """
    A class representing a step in a workflow.

    Attributes:
        step_name (str): The name of the step.
        step_agent: The Agent instance for this step, if any.
        step_input (dict): The input/template config for this step.
        step_condition (list): The conditional branches for this step.
        step_parallel (list): List of Agents to run in parallel.
        step_loop (dict): Loop configuration for this step.
    """

    def __init__(self, step):
        self.step_name = step["name"]
        self.step_agent = step.get("agent")
        self.step_input = step.get("input")
        self.step_condition = step.get("condition")
        self.step_parallel = step.get("parallel")
        self.step_loop = step.get("loop")

    async def run(self, *args, context=None):
        """
        Runs the step, passing along any number of positional arguments
        (from the workflow's `inputs:`), plus an optional `context=`.

        Returns always a dict with at least {"prompt": ...} so downstream logic stays the same.
        """

        if self.step_agent:
            if context is None:
                res = await self.step_agent.run(*args)
            else:
                res = await self.step_agent.run(*args, context=context)
        else:
            res = args[-1] if args else ""

        if isinstance(res, dict):
            output = res.copy()
            prompt = output.get("prompt", "")
        else:
            prompt = res
            output = {"prompt": prompt}

        if self.step_input:
            prompt = self.input(prompt)
            output["prompt"] = prompt

        if self.step_condition:
            output["next"] = self.evaluate_condition(prompt)

        if self.step_parallel:
            prompt = await self.parallel(prompt)
            output["prompt"] = prompt

        if self.step_loop:
            prompt = await self.loop(prompt)
            output["prompt"] = prompt

        return output

    def evaluate_condition(self, prompt):
        if self.step_condition[0].get("if"):
            return self.process_if(prompt)
        else:
            return self.process_case(prompt)

    def process_if(self, prompt):
        expr = self.step_condition[0]["if"]
        return (
            self.step_condition[0]["then"]
            if eval_expression(expr, prompt)
            else self.step_condition[0]["else"]
        )

    def process_case(self, prompt):
        default = ""
        for cond in self.step_condition:
            expr = cond.get("case")
            if expr and eval_expression(expr, prompt):
                return cond.get("do")
            default = cond.get("do", default)
        return default

    def input(self, prompt):
        user_prompt = self.step_input["prompt"].replace("{prompt}", str(prompt))
        template = self.step_input["template"]
        # special connector handling
        if "{CONNECTOR}" in template:
            return prompt
        response = input(user_prompt)
        return template.replace("{prompt}", prompt).replace("{response}", response)

    async def parallel(self, prompt):
        """
        This function runs multiple agents in parallel and returns the results as a string.

        Args:
            prompt (str): The input prompt for the agents to run.

        Returns:
            str: The results of running the agents in parallel as a string.
        """

        tasks = []
        if prompt.find("[") != -1:
            args = convert_to_list(prompt)
            tasks = [
                asyncio.create_task(agent.run(args[index]))
                for index, agent in enumerate(self.step_parallel)
            ]
        else:
            tasks = [
                asyncio.create_task(agent.run(prompt)) for agent in self.step_parallel
            ]
        results = await asyncio.gather(*tasks)
        print(results)
        return str(results)

    async def loop(self, prompt):
        """
        This function is a loop that runs an agent on a given prompt until a certain condition is met.

        Parameters:
            prompt (str): The initial prompt for the agent to run.

        Returns:
            str: The final prompt after the loop has completed.
        """
        until = self.step_loop.get("until")
        agent = self.step_loop["agent"]
        prompt = str(prompt)
        if prompt.find("[") != -1:
            args = convert_to_list(prompt)
            results = []
            for arg in args:
                prompt = await agent.run(arg)
                results.append(prompt)
            return str(results)
        while True:
            prompt = await agent.run(prompt)
            if eval_expression(until, prompt):
                return prompt
