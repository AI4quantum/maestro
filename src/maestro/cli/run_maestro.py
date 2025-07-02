#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Maestro

Usage:
  maestro create AGENTS_FILE [options]
  maestro deploy AGENTS_FILE WORKFLOW_FILE [options] [ENV...]
  maestro mermaid WORKFLOW_FILE [options]
  maestro run WORKFLOW_FILE [options]
  maestro run AGENTS_FILE WORKFLOW_FILE [options]
  maestro serve AGENTS_FILE [options]
  maestro validate YAML_FILE [options]
  maestro validate SCHEMA_FILE YAML_FILE [options]
  maestro meta-agents TEXT_FILE [options]
  maestro clean [options]
  maestro create-cr YAML_FILE [options]

  maestro (-h | --help)
  maestro (-v | --version)

Options:
  --verbose              Show all output.
  --silent               Show no additional output on success, e.g., no OK or Success etc
  --dry-run              Mocks agents and other parts of workflow execution.
  --prompt               Reads a user prompt and executes workflow with it
  --auto-prompt          Run prompt by default if specified

  --streamlit            Deploys locally as streamlit application (default deploy)

  --url                  The deployment URL, default: 127.0.0.1:5000
  --k8s                  Deploys to Kubernetes
  --kubernetes
  --docker               Deploys to Docker

  --sequenceDiagram      Sequence diagram mermaid
  --flowchart-td         Flowchart TD (top down) mermaid
  --flowchart-lr         Flowchart LR (left right) mermaid

  --port PORT            Port to serve on (default: 8000)
  --host HOST            Host to bind to (default: 127.0.0.1)
  --agent-name NAME      Specific agent name to serve (if multiple in file)
  --streaming            Enable streaming responses

  -h --help              Show this screen.
  -v --version           Show version.

"""

from docopt import docopt

from maestro.cli.common import Console


def __execute(command):
    try:
        rc = command.execute()
        if rc != 0:
            Console.error(f"executing command: {rc}")
        return rc
    except Exception as e:
        Console.error(str(e))
        return 1


def __run_cli():
    from maestro.cli.commands import CLI

    args = docopt(__doc__, version="Maestro CLI v0.0.4")
    command = CLI(args).command()
    return __execute(command)


if __name__ == "__main__":
    __run_cli()
