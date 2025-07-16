#!/bin/bash

export DRY_RUN=1
maestro serve simple_agent.yaml --host 0.0.0.0 --port 30051 --agent-name test1
