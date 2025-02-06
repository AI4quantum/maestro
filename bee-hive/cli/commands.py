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

import os, yaml, json, jsonschema

from jsonschema.exceptions import ValidationError
from common import Console, parse_yaml

# Base class for all commands
class Command:
    def __init__(self, args):
        self.args = args
        self.__init_dry_run()
        
    def __init_dry_run(self):
        if self.args.get('--dry-run') and self.args['--dry-run']:
            self.__dry_run = True
            os.environ["DRY_RUN"] = "True"        
    
    def println(self, msg):
        self.print(msg + "\n")

    def print(self, msg):
        Console.print(msg)

    def warn(self, msg):
        Console.warn(msg)

    def verbose(self):
        return self.args['--verbose']
    
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
        if self.args['validate']:
            return self.validate
        elif self.args['create']:
            return self.create
        elif self.args['run']:
            return self.run
        elif self.args['deploy']:
            return self.deploy
        else:
            raise Exception("Invalid subcommand")

# validate command group
#  maestro validate SCHEMA_FILE YAML_FILE [options]
class Validate(Command):
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    def SCHEMA_FILE(self):
        return self.args['SCHEMA_FILE']

    def YAML_FILE(self):
        return self.args['YAML_FILE']

    def name(self):
      return "validate"

    def validate(self):
        Console.print("validating {yaml_file} with schema {schema_file}".format(yaml_file=self.YAML_FILE(), schema_file=self.SCHEMA_FILE()))
        with open(self.SCHEMA_FILE(), 'r') as f:
            schema = json.load(f)
        with open(self.YAML_FILE(), 'r') as f:
            yamls = yaml.safe_load_all(f)
            for yaml_data in yamls:
                json_data = json.dumps(yaml_data, indent=4)
                try:
                    jsonschema.validate(yaml_data, schema)
                    Console.ok("YAML file is valid.")
                except ValidationError as ve:
                    Console.error("YAML file is NOT valid:\n {error_message}".format(error_message=str(ve.message)))
                    return 1
        return 0

# Create command group
#  maestro create AGENTS_FILE [options]
class Create(Command):
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    def __create_agents(self, agents_yaml):
        return 0 #TODO

    def AGENTS_FILE(self):
        return self.args['AGENTS_FILE']

    def name(self):
      return "create"

    def create(self):
        agents_yaml = parse_yaml(self.AGENTS_FILE())
        try:
            return self.__create_agents(agents_yaml)
        except Exception as e:
            raise RuntimeError("Unable to create agents: {message}".format(message=str(e))) from e

# Run command group
#  maestro run AGENTS_FILE WORKFLOW_FILE [options]
class Run(Command):
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)

    def __run_agents_workflow(self, agents_yaml, workflow_yaml):
        return 0 #TODO

    def AGENTS_FILE(self):
        return self.args['AGENTS_FILE']

    def WORKFLOW_FILE(self):
        return self.args['WORKFLOW_FILE']

    def name(self):
      return "run"

    def run(self):
        agents_yaml = parse_yaml( self.AGENTS_FILE())
        workflow_yaml = parse_yaml( self.WORKFLOW_FILE())
        try:
            return self.__run_agents_workflow(agents_yaml, workflow_yaml)
        except Exception as e:
            raise RuntimeError("Unable to run workflow: {message}".format(message=str(e))) from e        
        

# Deploy command group
#  maestro deploy AGENTS_FILE WORKFLOW_FILE [options]
class Deploy(Command):
    def __init__(self, args):
        self.args = args
        super().__init__(self.args)
    
    def __deploy_agents_workflow(self, agents_yaml, workflow_yaml):
        return 0 #TODO

    def AGENTS_FILE(self):
        return self.args['AGENTS_FILE']

    def WORKFLOW_FILE(self):
        return self.args['WORKFLOW_FILE']

    def name(self):
      return "deploy"

    def deploy(self):
        agents_yaml = parse_yaml( self.AGENTS_FILE())
        workflow_yaml = parse_yaml( self.WORKFLOW_FILE())
        try:
            return self.__deploy_agents_workflow(agents_yaml, workflow_yaml)
        except Exception as e:
            raise RuntimeError("Unable to deploy workflow: {message}".format(message=str(e))) from e        
