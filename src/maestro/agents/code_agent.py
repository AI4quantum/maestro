#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
import tempfile
import shutil
import json
from dotenv import load_dotenv

from maestro.agents.agent import Agent
from maestro.agents.utils import get_content

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
        self.venv_path = None  # Path to virtual environment

    def _create_virtual_env(self) -> None:
        """
        Create a virtual environment for installing dependencies.
        """
        # Create a virtual environment
        self.venv_path = os.path.join(
            tempfile.gettempdir(), f"venv-{self.agent_name}-{os.getpid()}"
        )
        self.print(f"Creating virtual environment at {self.venv_path}")

        try:
            venv_cmd = [sys.executable, "-m", "venv", self.venv_path]
            subprocess.run(
                venv_cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            self.print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            error_msg = f"Error creating virtual environment: {e.stderr}"
            self.print(error_msg)
            self.venv_path = None
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = (
                f"Unexpected error during virtual environment creation: {str(e)}"
            )
            self.print(error_msg)
            self.venv_path = None
            raise RuntimeError(error_msg)

    def _remove_virtual_env(self) -> None:
        """
        Remove the virtual environment if it exists.
        """
        if self.venv_path and os.path.exists(self.venv_path):
            try:
                self.print(f"Removing virtual environment at {self.venv_path}")
                shutil.rmtree(self.venv_path)
                self.print("Virtual environment removed successfully.")
                self.venv_path = None
            except Exception as e:
                self.venv_path = None
                self.print(
                    f"Warning: Failed to remove virtual environment {self.venv_path}: {str(e)}"
                )

    def _install_dependencies(self) -> None:
        """
        Check if the agent has dependencies in its metadata and install them if they exist.
        """
        self._create_virtual_env()
        dependencies = self.agent.get("metadata", {}).get("dependencies")
        self.print(dependencies)
        if not dependencies or dependencies.strip() == "":
            self.print("No dependencies found")
            return

        self.print(f"Installing dependencies for {self.agent_name}...")

        temp_file_path = None
        try:
            # Create a temporary requirements.txt file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt"
            ) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(
                    get_content(dependencies, self.agent.get("source_file", ""))
                )

            # Determine the pip path in the virtual environment
            if self.venv_path is None:
                raise RuntimeError("Virtual environment path is not set")

            if os.name == "nt":  # Windows
                pip_path = os.path.join(self.venv_path, "Scripts", "pip")
            else:  # Unix/Linux/Mac
                pip_path = os.path.join(self.venv_path, "bin", "pip")

            # Install dependencies using pip from the virtual environment
            self.print(f"Running pip install with requirements file: {temp_file_path}")
            process = subprocess.run(
                [
                    pip_path,
                    "install",
                    "-r",
                    temp_file_path,
                    "--verbose",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.print("Dependencies installed successfully in virtual environment.")
            if process.stdout:
                self.print(f"Installation output: {process.stdout}")
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
            elif "FileNotFoundError" in e.stderr:
                self.print(
                    "Error: uv command not found. Please ensure uv is installed and in your PATH."
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

        try:
            # Determine the Python interpreter path in the virtual environment
            if os.name == "nt":  # Windows
                python_path = os.path.join(self.venv_path, "Scripts", "python.exe")
            else:  # Unix/Linux/Mac
                python_path = os.path.join(self.venv_path, "bin", "python")

            # Escape the agent code for safe inclusion in a string
            escaped_code = (
                self.agent_code.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("'", "\\'")
            )

            # Create the Python command
            python_command = f"""
import json, sys
input = {json.dumps(args)}
output = {{}}
exec('''{escaped_code}''')
print(json.dumps(output))
"""

            # Execute the command using the Python interpreter from the virtual environment
            self.print(
                f"Executing agent code in virtual environment at {self.venv_path}"
            )
            process = subprocess.run(
                [python_path, "-c", python_command],
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse the output from stdout
            try:
                output_data = json.loads(process.stdout.strip())
                local = {"output": output_data}
                answer = str(local["output"])
            except json.JSONDecodeError as je:
                self.print(f"JSON decode error: {je}. Raw output: {process.stdout}")
                local = {"output": process.stdout.strip()}
                answer = str(local["output"])

            # Log any stderr from the process
            if process.stderr:
                self.print(f"Script stderr: {process.stderr}")

            # Clean up virtual environment after successful execution
            self._remove_virtual_env()

        except subprocess.CalledProcessError as e:
            self.print(f"Exception executing code in virtual environment: {e}\n")
            if e.stdout:
                self.print(f"Process stdout: {e.stdout}")
            if e.stderr:
                self.print(f"Process stderr: {e.stderr}")
            # Clean up virtual environment even if execution fails
            self._remove_virtual_env()

            # Check if the error is related to missing modules/imports
            if (
                "ModuleNotFoundError" in e.stderr
                or "ImportError" in e.stderr
                or "No module named" in e.stderr
            ):
                # Preserve the original import error message
                raise RuntimeError(
                    f"Failed to execute agent code in virtual environment: {e.stderr}"
                )
            else:
                raise RuntimeError(
                    f"Failed to execute agent code in virtual environment: {str(e)}"
                )
        except Exception as e:
            self.print(f"Exception executing code: {e}\n")
            # Clean up virtual environment even if execution fails
            self._remove_virtual_env()
            raise e

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

        try:
            # Determine the Python interpreter path in the virtual environment
            if os.name == "nt":  # Windows
                python_path = os.path.join(self.venv_path, "Scripts", "python.exe")
            else:  # Unix/Linux/Mac
                python_path = os.path.join(self.venv_path, "bin", "python")

            # Escape the agent code for safe inclusion in a string
            escaped_code = (
                self.agent_code.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("'", "\\'")
            )

            # Create the Python command
            python_command = f"""
import json, sys
input = {json.dumps(args)}
output = {{}}
exec('''{escaped_code}''')
print(json.dumps(output))
"""

            # Execute the command using the Python interpreter from the virtual environment
            self.print(
                f"Executing agent code in virtual environment at {self.venv_path}"
            )
            process = subprocess.run(
                [python_path, "-c", python_command],
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse the output from stdout
            try:
                output_data = json.loads(process.stdout.strip())
                local = {"output": output_data}
                answer = str(local["output"])
            except json.JSONDecodeError as je:
                self.print(f"JSON decode error: {je}. Raw output: {process.stdout}")
                local = {"output": process.stdout.strip()}
                answer = str(local["output"])

            # Log any stderr from the process
            if process.stderr:
                self.print(f"Script stderr: {process.stderr}")

            # Clean up virtual environment after successful execution
            self._remove_virtual_env()

        except subprocess.CalledProcessError as e:
            self.print(f"Exception executing code in virtual environment: {e}\n")
            if e.stdout:
                self.print(f"Process stdout: {e.stdout}")
            if e.stderr:
                self.print(f"Process stderr: {e.stderr}")
            # Clean up virtual environment even if execution fails
            self._remove_virtual_env()

            # Check if the error is related to missing modules/imports
            if (
                "ModuleNotFoundError" in e.stderr
                or "ImportError" in e.stderr
                or "No module named" in e.stderr
            ):
                # Preserve the original import error message
                raise RuntimeError(
                    f"Failed to execute agent code in virtual environment: {e.stderr}"
                )
            else:
                raise RuntimeError(
                    f"Failed to execute agent code in virtual environment: {str(e)}"
                )
        except Exception as e:
            self.print(f"Exception executing code: {e}\n")
            # Clean up virtual environment even if execution fails
            self._remove_virtual_env()
            raise e

        self.print(f"Response from {self.agent_name}: {answer}\n")
        return str(local["output"])
