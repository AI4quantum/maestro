# SPDX-License-Identifier: Apache-2.0

import dspy
from .agent import Agent as BaseAgent  # Import BaseAgent first


class DspyAgent(BaseAgent):
    """
    DspyAgent extends the Agent class to load and run a specific Dspy ReAct agent.
    Requires the 'dspy' library to be installed.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified agent.
        The executable code must be within $PYTHONPATH.

        Args:
            agent (dict): Agent Configuration

        Raises:
            RuntimeError: If the 'dspy' library is not installed or failed to import.
            Exception: If the agent configuration is invalid.
        """
        super().__init__(agent)  # Initialize BaseAgent part

        try:
            self.provider_url = agent["spec"].get(
                "url"
            )  # Assuming LLM provider URL is here
            self.agent_model = agent["spec"].get("model")  # Assuming model name is here
        except KeyError as e:
            self.print(
                f"Failed to load agent {self.agent_name}: Missing configuration key - {e}"
            )
            raise ValueError(
                f"Invalid configuration for agent {self.agent_name}: Missing key {e}"
            ) from e
        except Exception as e:
            self.print(f"Failed to load agent {self.agent_name}: {e}")
            raise e  # Re-raise other unexpected errors

        class BaseDSPySignature(dspy.Signature):
            """You are a good agent that helps user answer questions and carries out tasks.

            You are given a list of tools to handle user request, and you should decide the right tool to use in order to
            fullfil users' request."""

            user_request: str = dspy.InputField()
            process_result: str = dspy.OutputField(
                desc=(
                    "Message that summarizes the process result, and the final answer to the user questions and requests."
                )
            )

        self.dspy_signature = BaseDSPySignature.with_instructions(
            f"You are {self.agent_desc}\nYou are expected to do {self.instructions}"
        )

        # os.environ["OPENAI_API_KEY"] = "{your openai key}"
        dspy.configure(lm=dspy.LM(self.agent_model, api_base=self.provider_url))

        self.dspy_agent = dspy.ReAct(self.dspy_signature, tools=[])

    async def run(self, prompt: str) -> str:
        """
        Executes the Dspy agent with the given prompt. The agent's `kickoff` method is called with the input.

        Args:
            prompt (str): The input to be processed by the agent.
        Returns:
            str: The raw output from the agent's `kickoff` method.
        Raises:
            RuntimeError: If the 'dspy' library is not installed or failed to import.
            Exception: If there is an error in retrieving or executing the agent's method.
        """

        self.print(f"Running Dspy agent: {self.agent_name} with prompt: {prompt}\n")

        try:
            result = self.dspy_agent(user_request=prompt)
            self.print(f"Response from {self.agent_name}: {result.process_result}\n")
            return result.process_result

        except Exception as e:
            self.print(f"Failed to execute dspy agent: {self.agent_name}: {e}\n")
            raise RuntimeError(f"Error executing Dspy agent {self.agent_name}") from e

    async def run_streaming(self, prompt: str) -> str:
        """
        Streams the execution of the Dspy agent with the given prompt.
        THIS IS NOT YET IMPLEMENTED for Dspy agents.

        Args:
            prompt (str): The input prompt to be processed by the Dspy agent.
        Raises:
            RuntimeError: If the 'dspy' library is not installed or failed to import.
            NotImplementedError: Indicates that the streaming logic for Dspy is not yet implemented.
        """

        self.print(
            f"Running Dspy agent (streaming): {self.agent_name} with prompt: {prompt}\n"
        )

        # If enabled, raise NotImplementedError as before
        raise NotImplementedError(
            f"Streaming execution for Dspy agent '{self.agent_name}' is not implemented yet."
        )
