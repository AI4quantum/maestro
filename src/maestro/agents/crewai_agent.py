# SPDX-License-Identifier: Apache-2.0

import importlib
from .agent import Agent as BeeAgent  # Import BeeAgent first

try:
    # Only import crewai types if the library is present
    from crewai import Agent as CrewAI_Agent, Crew, Task, Process
    from crewai import LLM

    enabled = True
    CREWAI_IMPORT_ERROR = None
except ImportError as e:
    enabled = False
    CREWAI_IMPORT_ERROR = e  # Store the original error

    # Define dummy types to prevent NameErrors later if needed for type hints (though avoided below)
    class CrewAI_Agent:
        pass

    class Crew:
        pass

    class Task:
        pass

    class Process:
        pass

    class LLM:
        pass


class CrewAIAgent(BeeAgent):
    """
    CrewAIAgent extends the Agent class to load and run a specific CrewAI agent.
    Requires the 'crewai' library to be installed.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the workflow for the specified agent.
        The executable code must be within $PYTHONPATH.

        Args:
            agent (dict): Agent Configuration

        Raises:
            RuntimeError: If the 'crewai' library is not installed or failed to import.
            Exception: If the agent configuration is invalid.
        """
        if not enabled:
            raise RuntimeError(
                f"Cannot initialize CrewAIAgent '{agent.get('metadata', {}).get('name', 'Unknown')}': "
                f"CrewAI support is disabled because the 'crewai' library could not be imported. "
                "To enable, run `pip install maestro[crewai]`"
                f"Original error: {CREWAI_IMPORT_ERROR}"
            )

        super().__init__(agent)  # Initialize BeeAgent part

        # TODO: Add additional properties later. for now using naming:
        #   <directory>.<filename>.<class>.<method> ie
        #   test.crewai_test.ColdWeatherCrew.activity_crew

        try:
            # These properties are needed regardless of whether crewai is used via module or direct config
            self.module_name = agent["metadata"]["labels"].get("module")
            if self.module_name:
                self.class_name = agent["metadata"]["labels"]["class"]
                self.factory_name = agent["metadata"]["labels"]["factory"]
                # Clear other properties if module is specified, as they won't be used (for clarity)
                self.provider_url = None
                self.crew_role = None
                self.crew_goal = None
                self.crew_backstory = None
                self.crew_description = None
                self.crew_expected_output = None
                self.agent_model = (
                    None  # Model likely defined within the imported module
                )
            else:
                # Properties for direct Crew definition
                self.provider_url = agent["spec"].get(
                    "url"
                )  # Assuming LLM provider URL is here
                self.agent_model = agent["spec"].get(
                    "model"
                )  # Assuming model name is here
                self.crew_role = agent["metadata"]["labels"].get("crew_role")
                self.crew_goal = agent["metadata"]["labels"].get("crew_goal")
                self.crew_backstory = agent["metadata"]["labels"].get("crew_backstory")
                self.crew_description = agent["metadata"]["labels"].get(
                    "crew_description"
                )
                self.crew_expected_output = agent["metadata"]["labels"].get(
                    "crew_expected_output"
                )
                # Validate required fields for direct definition
                if not all(
                    [
                        self.provider_url,
                        self.agent_model,
                        self.crew_role,
                        self.crew_goal,
                        self.crew_description,
                        self.crew_expected_output,
                    ]
                ):
                    raise ValueError(
                        "Missing required configuration for direct CrewAI agent definition (url, model, crew_role, crew_goal, crew_description, crew_expected_output)."
                    )
                # Clear module properties
                self.class_name = None
                self.factory_name = None

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

    async def run(self, prompt: str) -> str:
        """
        Executes the CrewAI agent with the given prompt. The agent's `kickoff` method is called with the input.

        Args:
            prompt (str): The input to be processed by the agent.
        Returns:
            str: The raw output from the agent's `kickoff` method.
        Raises:
            RuntimeError: If the 'crewai' library is not installed or failed to import.
            Exception: If there is an error in retrieving or executing the agent's method.
        """

        self.print(f"Running CrewAI agent: {self.agent_name} with prompt: {prompt}\n")

        try:
            if self.module_name:
                my_module = importlib.import_module(self.module_name)
                self.crew_agent_class = getattr(my_module, self.class_name)
                self.instance = self.crew_agent_class()
                factory = getattr(self.instance, self.factory_name)
                # Assuming factory returns an object with kickoff
                # Note: The imported module itself might fail if crewai is missing,
                # but the initial check prevents calling this code path anyway.
                output = factory().kickoff({"prompt": prompt})
            else:
                # Directly use the configured crew
                output = self.crew().kickoff({"prompt": prompt})

            # Ensure output is string (CrewAI kickoff often returns structured data)
            raw_output = getattr(output, "raw", str(output))
            self.print(f"Response from {self.agent_name}: {raw_output}\n")
            return raw_output

        except Exception as e:
            self.print(f"Failed to kickoff crew agent: {self.agent_name}: {e}\n")
            # Consider more specific error handling if needed
            raise RuntimeError(f"Error executing CrewAI agent {self.agent_name}") from e

    async def run_streaming(self, prompt: str) -> str:
        """
        Streams the execution of the CrewAI agent with the given prompt.
        THIS IS NOT YET IMPLEMENTED for CrewAI agents.

        Args:
            prompt (str): The input prompt to be processed by the CrewAI agent.
        Raises:
            RuntimeError: If the 'crewai' library is not installed or failed to import.
            NotImplementedError: Indicates that the streaming logic for CrewAI is not yet implemented.
        """

        self.print(
            f"Running CrewAI agent (streaming): {self.agent_name} with prompt: {prompt}\n"
        )

        # If enabled, raise NotImplementedError as before
        raise NotImplementedError(
            f"Streaming execution for CrewAI agent '{self.agent_name}' is not implemented yet."
        )

    def agent(self) -> CrewAI_Agent:
        """Creates a CrewAI Agent instance based on configuration."""

        # Ensure required fields for direct definition are present (checked in init, but good practice)
        if not all(
            [
                self.provider_url,
                self.agent_model,
                self.crew_role,
                self.crew_goal,
                self.crew_backstory,
            ]
        ):
            raise ValueError(
                "Cannot create agent: Missing required configuration (url, model, role, goal, backstory)."
            )

        # Use the imported LLM and Agent types
        llm = LLM(
            model=self.agent_model,
            base_url=self.provider_url,
            # TODO: Add API key handling if needed by the LLM provider
            # api_key=os.getenv("SPECIFIC_API_KEY_FOR_PROVIDER")
        )
        return CrewAI_Agent(
            role=self.crew_role,
            goal=self.crew_goal,
            backstory=self.crew_backstory,
            llm=llm,
            verbose=False,  # Keep verbose off unless needed for debugging
            allow_delegation=False,  # Typically false for single-agent crews
        )

    def task(self) -> Task:
        """Creates a CrewAI Task instance based on configuration."""
        if not all([self.crew_description, self.crew_expected_output]):
            raise ValueError(
                "Cannot create task: Missing required configuration (description, expected_output)."
            )

        # Use the imported Task type
        return Task(
            description=self.crew_description,
            expected_output=self.crew_expected_output,
            agent=self.agent(),
        )

    def crew(self) -> Crew:
        """Creates a CrewAI Crew instance based on configuration."""

        return Crew(
            agents=[self.agent()],  # Calls agent() method
            tasks=[self.task()],  # Calls task() method
            process=Process.sequential,  # Default to sequential for single agent/task
            verbose=False,  # Keep verbose off
            # TODO: Add memory, cache, etc. configuration if needed
        )
