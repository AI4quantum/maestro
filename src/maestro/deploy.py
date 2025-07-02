#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import dotenv
import shutil
import subprocess
import yaml
import tempfile

dotenv.load_dotenv()


def env_array_docker(str_envs):
    """
    Convert a string of environment variables into an array of arguments for Docker.

    Parameters:
    str_envs (str): A string of environment variables separated by spaces.

    Returns:
    list: A list of arguments for Docker, where each environment variable is represented by two elements in the list: -e and the environment variable name and value.
    """
    env_array = str_envs.split()
    env_args = []
    for env in env_array:
        env_args.append("-e")
        env_args.append(env)
    return env_args


def flag_array_build(str_flags):
    """
    Build an array of flags from a string of flags.

    Args:
        str_flags (str): A string of flags in the format "key1=value1 key2=value2".

    Returns:
        list: A list of flags in the format ["key1", "value1", "key2", "value2"].
    """
    flag_array = str_flags.split()
    flags = []
    for flag in flag_array:
        key, value = flag.split("=")
        flags.append(key)
        flags.append(value)
    return flags


def create_docker_args(cmd, target, env):
    """
    Creates docker arguments for running a container.

    Args:
        cmd (str): The command to run.
        target (int): The target port.
        env (dict): The environment variables.

    Returns:
        list: The docker arguments.
    """
    arg = [f"{cmd}", "run", "-d", "-p", f"{target}:5000"]
    arg.extend(env_array_docker(env))
    arg.append("maestro")
    return arg


def create_build_args(cmd, flags):
    """
    Creates the build arguments for the given command and flags.

    Args:
        cmd (str): The command to be executed.
        flags (list): A list of flags to be included in the build arguments.

    Returns:
        list: A list of build arguments.
    """
    arg = [f"{cmd}", "build"]
    if flags:
        arg.extend(flag_array_build(flags))
    arg.extend(["-t", "maestro", "-f", "Dockerfile", ".."])
    return arg


def update_yaml(yaml_file, str_envs):
    """
    Update the yaml file with the given environment variables.

    Args:
        yaml_file (str): The path to the yaml file.
        str_envs (str): A string of environment variables in the format of "key1=value1 key2=value2".

    Returns:
        None
    """
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)
    pairs = str_envs.split()
    for pair in pairs:
        key, value = pair.split("=")
        data["spec"]["template"]["spec"]["containers"][0]["env"].append(
            {"name": key, "value": value}
        )
    with open(yaml_file, "w") as f:
        yaml.safe_dump(data, f)


class Deploy:
    """
    Deploy class for deploying agents and workflows to different environments.

    Attributes:
        agent (str): Path to the agent definitions file.
        workflow (str): Path to the workflow definitions file.
        env (str): Environment to deploy to.
        target (str): Target environment to deploy to.
        cmd (str): Command to use for building the image.
        flags (str): Flags to use for building the image.
        tmp_dir (str): Temporary directory for building the image.

    Methods:
        build_image(agent, workflow): Builds the image for the specified agent and workflow.
        deploy_to_docker(): Deploys the image to Docker.
        deploy_to_kubernetes(): Deploys the image to Kubernetes.
    """

    def __init__(self, agent_defs, workflow_defs, env="", target=None):
        """
        Initializes the Code Assistant.

        Parameters:
        agent_defs (dict): Agent definitions.
        workflow_defs (dict): Workflow definitions.
        env (str, optional): Environment name. Defaults to "".
        target (str, optional): Target address. Defaults to "127.0.0.1:5000".

        Returns:
        None
        """
        self.agent = agent_defs
        self.workflow = workflow_defs
        self.env = env
        self.target = target or "127.0.0.1:5000"
        self.cmd = os.getenv("CONTAINER_CMD", "docker")
        self.flags = os.getenv("BUILD_FLAGS")

    def build_image(self, agent, workflow):
        """
        Build an image for the Maestro application.

        Args:
            agent (str): Path to the agent YAML file.
            workflow (str): Path to the workflow YAML file.

        Returns:
            None
        """
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.tmp_dir = os.path.join(tempfile.gettempdir(), "maestro")
        shutil.copytree(
            os.path.join(module_dir, "../../deployments"),
            os.path.join(self.tmp_dir, "tmp"),
            dirs_exist_ok=True,
        )
        shutil.copy(agent, os.path.join(self.tmp_dir, "tmp/agents.yaml"))
        shutil.copy(workflow, os.path.join(self.tmp_dir, "tmp/workflow.yaml"))

        cwd = os.getcwd()
        os.chdir(os.path.join(self.tmp_dir, "tmp"))
        subprocess.run(create_build_args(self.cmd, self.flags))
        os.chdir(cwd)

    def deploy_to_docker(self):
        """
        Deploys the agent to a Docker container.

         Args:
             self (object): The instance of the class.
             agent (str): The name of the agent.
             workflow (str): The name of the workflow.

         Returns:
             None
        """
        self.build_image(self.agent, self.workflow)
        subprocess.run(create_docker_args(self.cmd, self.target, self.env))
        shutil.rmtree(self.tmp_dir)

    def deploy_to_kubernetes(self):
        """
        Deploys the trained model to Kubernetes.

        Args:
            self (object): The instance of the class.

        Returns:
            None
        """
        # module_path = os.path.abspath(inspect.getsourcefile(lambda: 0))
        # module_dir = os.path.dirname(module_path)

        self.build_image(self.agent, self.workflow)
        update_yaml(os.path.join(self.tmp_dir, "tmp/deployment.yaml"), self.env)
        image_tag_command = os.getenv("IMAGE_TAG_CMD")
        if image_tag_command:
            subprocess.run(image_tag_command.split())
        image_push_command = os.getenv("IMAGE_PUSH_CMD")
        if image_push_command:
            subprocess.run(image_push_command.split())
        subprocess.run(
            [
                "kubectl",
                "apply",
                "-f",
                os.path.join(self.tmp_dir, "tmp/deployment.yaml"),
            ]
        )
        subprocess.run(
            ["kubectl", "apply", "-f", os.path.join(self.tmp_dir, "tmp/service.yaml")]
        )
        shutil.rmtree(self.tmp_dir)
