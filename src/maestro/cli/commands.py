# Copyright © 2025 IBM
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CLI command implementations for Maestro workflow management."""
import os
import re
import signal
import sys
import json
import traceback
import asyncio
import subprocess

import yaml
import jsonschema
import psutil

from jsonschema.exceptions import ValidationError, SchemaError

from maestro.deploy import Deploy
from maestro.workflow import Workflow, create_agents
from maestro.cli.common import Console, parse_yaml

# Root CLI class
class CLI:
    """Root CLI class that handles command routing and initialization."""
    
    def __init__(self, args):
        self.args = args
        VERBOSE, DRY_RUN, SILENT = False, False, False
        if self.args['--verbose']:
            VERBOSE = True
        if self.args['--dry-run']:
            DRY_RUN = True
        if self.args['--silent']:
            SILENT = True

    def command(self):
        """Route to the appropriate command handler based on command line arguments.
        
        Returns:
            Command: An instance of the appropriate command handler class.
        """
        if self.args.get('validate') and self.args['validate']:
            return ValidateCmd(self.args)
        elif self.args.get('create') and self.args['create']:
            return CreateCmd(self.args)
        elif self.args.get('run') and self.args['run']:
            return RunCmd(self.args)
        elif self.args.get('deploy') and self.args['deploy']:
            return DeployCmd(self.args)
        elif self.args.get('mermaid') and self.args['mermaid']:
            return MermaidCmd(self.args)
        elif self.args.get('meta-agents') and self.args['meta-agents']:
            return MetaAgentsCmd(self.args)
        elif self.args.get('clean') and self.args['clean']:
            return CleanCmd(self.args)
        elif self.args.get('create-cr') and self.args['create-cr']:
            return CreateCrCmd(self.args)
        else:
            raise Exception("Invalid command")

# Base class for all commands
class Command:
    """Base class that provides common functionality for all command implementations."""
    
    def __init__(self, args):
        self.args = args
        self.__init_dry_run()
        
    def __init_dry_run(self):
        if self.args.get('--dry-run') and self.args['--dry-run']:
            self.__dry_run = True
            os.environ["DRY_RUN"] = "True"        
    
    def _check_verbose(self):
        if self.verbose():
            print(traceback.format_exc())

    def println(self, msg):
        self.print(msg + "\n")

    def print(self, msg):
        Console.print(msg)

    def warn(self, msg):
        Console.warn(msg)

    def verbose(self):
        return self.args['--verbose']
    
    def silent(self):
        return self.args['--silent']

    def dry_run(self):
        return self.__dry_run

    def execute(self):
        func = self.dispatch()
        rc = func()
        if rc == None:
            return 0
        else:
            if isinstance(rc, int):
                return rc
            else:
                return 1

    def dispatch(self):
        """Route to the appropriate command handler method based on command line arguments.
        
        Returns:
            function: The command handler method to execute.
        """
        if self.args['validate']:
            return self.validate
        elif self.args['create']:
            return self.create
        elif self.args['run']:
            return self.run
        elif self.args['deploy']:
            return self.deploy
        elif self.args['mermaid']:
            return self.mermaid
        elif self.args['meta-agents']:
            return self.meta_agents
        elif self.args['clean']:
            return self.clean
        elif self.args['create-cr']:
            return self.create_cr
        else:
            raise Exception("Invalid subcommand")

# validate command group
#  maestro validate SCHEMA_FILE YAML_FILE [options]
class ValidateCmd(Command):
    """Command handler for validating YAML files against JSON schemas."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    # private

    def __discover_schema_file(self, yaml_file):
        yaml_data = parse_yaml(yaml_file)
        if isinstance(yaml_data, list) and len(yaml_data) > 0:
            yaml_data = yaml_data[0]
        kind = yaml_data.get('kind')
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
        if kind == 'Agent':
            return os.path.join(project_root, 'schemas/agent_schema.json')
        elif kind == 'Tool':
            return os.path.join(project_root, 'schemas/tool_schema.json')
        elif kind == 'Workflow':
            return os.path.join(project_root, 'schemas/workflow_schema.json')
        elif kind == 'WorkflowRun':
            Console.ok("WorkflowRun is not supported")
            return None
        elif kind == 'CustomResourceDefinition':
            Console.ok("CustomResourceDefinition is not supported")
            return None
        else:
            raise ValueError(f"Unknown kind: {kind}")

    def __validate(self, schema_file, yaml_file):
        Console.print(f"validating {yaml_file} with schema {schema_file}")
        if schema_file is None:
            # Try to discover the schema file based on the yaml file
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
            if "agents.yaml" in yaml_file:
                schema_file = os.path.join(project_root, "schemas/agent_schema.json")
            elif "workflow.yaml" in yaml_file:
                schema_file = os.path.join(project_root, "schemas/workflow_schema.json")
            else:
                raise RuntimeError("Could not determine schema file from yaml file name")
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        with open(yaml_file, 'r', encoding='utf-8') as f:
            yamls = yaml.safe_load_all(f)
            for yaml_data in yamls:
                try:
                    if self.verbose():
                        Console.print(f"Validating YAML data: {json.dumps(yaml_data, indent=2)}")
                        Console.print(f"Against schema: {json.dumps(schema, indent=2)}")
                    jsonschema.validate(yaml_data, schema)
                    if not self.silent():
                        Console.ok("YAML file is valid.")
                except ValidationError as ve:
                    self._check_verbose()
                    Console.error(f"YAML file is NOT valid:\n {str(ve.message)}")
                    return 1
                except SchemaError as se:
                    self._check_verbose()
                    Console.error(f"Schema file is NOT valid:\n {str(se.message)}")
                    return 1
        return 0

    # public

    def SCHEMA_FILE(self):
        return self.args['SCHEMA_FILE']

    def YAML_FILE(self):
        return self.args['YAML_FILE']

    def name(self):
      return "validate"

    def validate(self):
        """Validate YAML files against JSON schemas.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        if self.SCHEMA_FILE() is None or self.SCHEMA_FILE() == '':
            discovered_schema_file = ''
            try:
                discovered_schema_file = self.__discover_schema_file(self.YAML_FILE())
                if not discovered_schema_file:
                    return 0
            except Exception as e:
                Console.error(f"Invalid YAML file: {self.YAML_FILE()}: {str(e)}")
                return 1
            return self.__validate(discovered_schema_file, self.YAML_FILE())
        return self.__validate(self.SCHEMA_FILE(), self.YAML_FILE())

# Create command group
#  maestro create AGENTS_FILE [options]
class CreateCmd(Command):
    """Command handler for creating agents from a configuration file."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    def __create_agents(self, agents_yaml):
        try:
            create_agents(agents_yaml)
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"{str(e)}") from e

    def AGENTS_FILE(self):
        return self.args['AGENTS_FILE']

    def name(self):
      return "create"

    def create(self):
        """Create agents from the specified configuration file.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        agents_yaml = parse_yaml(self.AGENTS_FILE())
        try:
            self.__create_agents(agents_yaml)
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to create agents: {str(e)}")
        return 0

# Run command group
#  maestro run AGENTS_FILE WORKFLOW_FILE [options]
class RunCmd(Command):
    """Command handler for running a workflow with specified agents and workflow files."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    # private

    def __run_agents_workflow(self, agents_yaml, workflow_yaml):
        try:
            workflow = Workflow(agents_yaml, workflow_yaml[0])
            asyncio.run(workflow.run())
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"{str(e)}") from e
        return 0

    def __read_prompt(self):
        return Console.read('Enter your prompt: ')

    # public

    def AGENTS_FILE(self):
        return self.args['AGENTS_FILE']

    def WORKFLOW_FILE(self):
        return self.args['WORKFLOW_FILE']

    def prompt(self):
        return self.args.get('--prompt')

    def name(self):
      return "run"

    def run(self):
        """Run a workflow with specified agents and workflow files.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        agents_yaml, workflow_yaml = None, None
        if self.AGENTS_FILE() != None and self.AGENTS_FILE() != 'None':
            agents_yaml = parse_yaml(self.AGENTS_FILE())
        workflow_yaml = parse_yaml(self.WORKFLOW_FILE())

        if self.prompt():
            prompt = self.__read_prompt()
            workflow_yaml[0]['spec']['template']['prompt'] = prompt

        try:
            self.__run_agents_workflow(agents_yaml, workflow_yaml)
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to run workflow: {str(e)}")
            return 1
        return 0
        
# Deploy command group
#  maestro deploy AGENTS_FILE WORKFLOW_FILE [options]
class DeployCmd(Command):
    """Command handler for deploying a workflow to a Kubernetes cluster or local server."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)
    
    def __deploy_agents_workflow_streamlit(self):
        try:
            sys.argv = ["uv", "run", "streamlit", "run", "--ui.hideTopBar", "True", "--client.toolbarMode", "minimal", f"{os.path.dirname(__file__)}/streamlit_deploy.py", self.AGENTS_FILE(), self.WORKFLOW_FILE()]
            process = subprocess.Popen(sys.argv)
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"{str(e)}") from e
        return 0

    def __deploy_agents_workflow(self, agents_yaml, workflow_yaml, env):
        try:
            if self.docker():
                deploy = Deploy(agents_yaml, workflow_yaml, env)
                deploy.deploy_to_docker()  
                if not self.silent():
                    Console.ok(f"Workflow deployed: http://127.0.0.1:5000")
            elif self.k8s():
                deploy = Deploy(agents_yaml, workflow_yaml, env)
                deploy.deploy_to_kubernetes()
                if not self.silent():
                    Console.ok(f"Workflow deployed: http://<kubernetes address>:30051")            
            else:
                self.__deploy_agents_workflow_streamlit()
                if not self.silent():
                    Console.ok(f"Workflow deployed: http://localhost:8501/?embed=true")
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"Unable to deploy workflow: {str(e)}") from e
        return 0            

    def auto_prompt(self):
        return self.args.get('--auto-prompt', False)

    def url(self):
        if self.args['--url'] == "" or self.args['--url'] == None:
            return "127.0.0.1:5000"
        return self.args['--url'] 

    def k8s(self):
        if self.args['--k8s'] != "":
            return self.args['--k8s']
        return self.args['--kubernetes'] 

    def docker(self):
        return self.args['--docker']

    def streamlit(self):
        return self.args['--streamlit']

    def AGENTS_FILE(self):
        return self.args['AGENTS_FILE']

    def WORKFLOW_FILE(self):
        return self.args['WORKFLOW_FILE']

    def ENV(self):
        env_vars = self.args['ENV']
        if self.auto_prompt():
            env_vars.append("AUTO_RUN=true")
        return " ".join(env_vars)

    def name(self):
      return "deploy"

    def deploy(self):
        """Deploy a workflow to a Kubernetes cluster or local server.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        try:
            self.__deploy_agents_workflow(self.AGENTS_FILE(), self.WORKFLOW_FILE(), self.ENV())
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to deploy workflow: {str(e)}")
            return 1
        return 0
        

# Mermaid command group
# $ maestro mermaid WORKFLOW_FILE [options]
class MermaidCmd(Command):
    """Command handler for generating mermaid diagrams from a workflow file."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    # private    
    def __mermaid(self, workflow_yaml) -> str:
        mermaid = ""
        workflow = Workflow(None, workflow_yaml)
        if self.sequenceDiagram():
            mermaid = workflow.to_mermaid("sequenceDiagram")
        elif self.flowchart_td():
            mermaid = workflow.to_mermaid("flowchart", "TD")
        elif self.flowchart_lr():            
            mermaid = workflow.to_mermaid("flowchart", "LR")
        else:
            mermaid = workflow.to_mermaid("sequenceDiagram")
        return mermaid

    # public options
    def WORKFLOW_FILE(self):
        return self.args.get('WORKFLOW_FILE')

    def sequenceDiagram(self):
        return self.args.get('--sequenceDiagram')

    def flowchart_td(self):
        return self.args.get('--flowchart-td')

    def flowchart_lr(self):
        return self.args.get('--flowchart-lr')

    def name(self):
      return "mermaid"

    # public command method
    def mermaid(self):
        """Generate a mermaid diagram from a workflow file.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        workflow_yaml = parse_yaml(self.WORKFLOW_FILE())
        try:            
            mermaid = self.__mermaid(workflow_yaml)
            if not self.silent():
                Console.ok("Created mermaid for workflow\n")
            Console.print(mermaid + "\n")
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to generate mermaid for workflow: {str(e)}")
            return 1
        return 0

# MetaAgents command group
# $ maestro meta-agents TEXT_FILE [options]
class MetaAgentsCmd(Command):
    """Command handler for running meta-agents on a text file."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    # private    
    def __meta_agents(self, text_file) -> int:
        try:
            sys.argv = ["uv", "run", "streamlit", "run", "--ui.hideTopBar", "True", "--client.toolbarMode", "minimal", f"{os.path.dirname(__file__)}/cli/streamlit_meta_agents_deploy.py", text_file]
            process = subprocess.Popen(sys.argv)
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"{str(e)}") from e
        return 0

    # public options
    def TEXT_FILE(self):
        return self.args.get('TEXT_FILE')

    def name(self):
      return "meta-agents"

    # public command method
    def meta_agents(self):
        """Run meta-agents on a text file.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        try:
            rc = self.__meta_agents(self.TEXT_FILE())
            if not self.silent():
                Console.ok("Running meta-agents\n")
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to run meta-agents: {str(e)}")
            return 1
        return 0

# Clean command group
#  maestro clean [options]
class CleanCmd(Command):
    """Command handler for cleaning up running processes."""
    
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    def __clean(self):
        try:
            for pid in psutil.pids():
                try:
                    process = psutil.Process(pid)
                    cmd = process.cmdline()
                    if len(cmd) > 3 and "streamlit" in cmd[1]:
                        process.send_signal(signal.SIGTERM)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"{str(e)}") from e

    # public
    
    def name(self):
      return "clean"

    def clean(self):
        """Clean up running processes.
        
        Returns:
            int: Return code (0 for success, 1 for failure)
        """
        try:
            self.__clean()
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to clean: {str(e)}")
            return 1
        return 0

# CreateCr command group
#  maestro create-cr YAML_FILE [options]
def sanitize_name(name):
    new_name = re.sub(r'[^a-zA-Z0-9]','-', name).lower().replace(" ", "-")
    if re.search(r'[.-0-9]$', new_name):
        return new_name + 'e'
    else:
        return new_name

class CreateCrCmd(Command):
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    def YAML_FILE(self):
        return self.args['YAML_FILE']

    def name(self):
      return "create-cr"

    def __create_cr(self):
        try:

            file_path = self.YAML_FILE()
            with open(file_path, 'r') as file:
                multiple = yaml.safe_load_all(file)

                for data in multiple:
                    data['apiVersion'] = "maestro.ai4quantum.com/v1alpha1"
                    if 'metadata' in data and 'name' in data['metadata']:
                        data['metadata']['name'] = sanitize_name(data['metadata']['name'])
                    if 'metadata' in data and 'labels' in data['metadata']:
                        for key in data['metadata']['labels']:
                            data['metadata']['labels'][key] = sanitize_name(data['metadata']['labels'][key])
                    if data['kind'] == "Workflow":
                        # remove template.meatdata
                        if data['spec']['template'].get('metadata'):
                            del data['spec']['template']['metadata']
                        if data['spec']['template'].get('agents'):
                            agents = data['spec']['template']['agents']
                            samitized_agents = []
                            for agent in agents:
                                samitized_agents.append(sanitize_name(agent))
                            data['spec']['template']['agents'] = samitized_agents
                        if data['spec']['template'].get('steps'):
                            steps = data['spec']['template']['steps']
                            for step in steps:
                                if step.get('agent'):
                                    step['agent'] = sanitize_name(step['agent'])
                                if step.get('parallel'):
                                    agents = step['parallel']
                                    samitized_agents = []
                                    for agent in agents:
                                        samitized_agents.append(sanitize_name(agent))
                                    step['parallel'] = samitized_agents
                        if data['spec']['template'].get('exception'):
                            exception = data['spec']['template']['exception']
                            if exception.get('agent'):
                                exception['agent'] = sanitize_name(exception['agent'])
                    with open("temp_yaml", 'w') as file:
                        yaml.safe_dump(data, file)
                        result = subprocess.run(['kubectl', 'apply', "-f", "temp_yaml"], capture_output=True, text=True)
                        if result.returncode != 0:
                            print(f"Stderr: {result.stderr}")
                            return 1
        except Exception as e:
            self._check_verbose()
            raise RuntimeError(f"{str(e)}") from e

    def create_cr(self):
        try:
            self.__create_cr()
        except Exception as e:
            self._check_verbose()
            Console.error(f"Unable to create CR: {str(e)}")
            return 1
        return 0
