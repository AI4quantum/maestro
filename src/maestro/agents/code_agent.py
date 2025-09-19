#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
import tempfile
from dotenv import load_dotenv

from maestro.agents.agent import Agent

load_dotenv()


class CodeAgent(Agent):
    """
    CodeAgent extends the Agent class that executes an arbitrary python code specifed in the code section of the agent definition.
    """

    def __init__(self, agent: dict) -> None:
        """
        Initializes the agent with agent definitions.
        """
        super().__init__(agent)
        self.agent = agent  # Store the agent dictionary for accessing metadata

    def _install_dependencies(self) -> None:
        """
        Check if the agent has dependencies in its metadata and install them if they exist.
        """
        dependencies = self.agent.get("metadata", {}).get("dependencies")
        if not dependencies or dependencies.strip() == "":
            return

        self.print(f"Installing dependencies for {self.agent_name}...")

        temp_file_path = None
        try:
            # Create a temporary requirements.txt file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt"
            ) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(dependencies)

            # Install dependencies using pip with the current Python interpreter
            self.print(f"Running pip install with requirements file: {temp_file_path}")
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    temp_file_path,
                    "--verbose",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.print("Dependencies installed successfully.")
            if process.stdout:
                self.print(f"Installation output: {process.stdout}")
        except FileNotFoundError:
            error_msg = "Error: pip command not found. Please ensure pip is installed and in your PATH."
            self.print(error_msg)
            raise RuntimeError(error_msg)
        except PermissionError:
            error_msg = "Error: Permission denied when installing packages. Try running with appropriate permissions."
            self.print(error_msg)
            raise RuntimeError(error_msg)
        except subprocess.CalledProcessError as e:
            error_msg = f"Error installing dependencies: {e.stderr}"
            self.print(error_msg)

            # Provide more helpful error messages for common issues
            if "No matching distribution found" in e.stderr:
                self.print(
                    "Suggestion: Check if the package names and versions are correct."
                )
            elif "Could not find a version that satisfies the requirement" in e.stderr:
                self.print(
                    "Suggestion: The specified package version might not be available. Try using a different version."
                )
            elif "HTTP error" in e.stderr or "Connection error" in e.stderr:
                self.print(
                    "Suggestion: Check your internet connection or try again later."
                )

            raise RuntimeError(f"Failed to install dependencies: {e.stderr}")
        except Exception as e:
            error_msg = f"Unexpected error during dependency installation: {str(e)}"
            self.print(error_msg)
            raise RuntimeError(error_msg)
        finally:
            # Clean up the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    self.print(f"Temporary requirements file removed: {temp_file_path}")
                except Exception as e:
                    self.print(
                        f"Warning: Failed to remove temporary file {temp_file_path}: {str(e)}"
                    )

    async def run(self, *args, context=None, step_index=None) -> str:
        """
        Execute the given code in the agent definition with the given prompt.
        Args:
            args: Argument list for the execution.
        """

        self.print(f"Running {self.agent_name} with {args}...\n")

        # Install dependencies before executing code
        self._install_dependencies()

        local = {"input": args, "output": {}}
        try:
            exec(self.agent_code, local)
        except Exception as e:
            self.print(f"Exception executing code: {e}\n")
            raise e
        answer = str(local["output"])
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return str(local["output"])

    async def run_streaming(self, *args, context=None, step_index=None) -> str:
        """
        Runs the agent with the given prompt in streaming mode.
        Args:
            prompt (str): The prompt to run the agent with.
        """

        self.print(f"Running {self.agent_name} with {args}...\n")

        # Install dependencies before executing code
        self._install_dependencies()

        local = {"input": args, "output": {}}
        try:
            exec(self.agent_code, local)
        except Exception as e:
            self.print(f"Exception executing code: {e}\n")
            raise e
        answer = str(local["output"])
        self.print(f"Response from {self.agent_name}: {answer}\n")
        return str(local["output"])
