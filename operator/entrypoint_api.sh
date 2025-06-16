#!/bin/sh

cp /etc/config/agents ./src/agents.yaml
cp /etc/config/workflow ./src/workflow.yaml
mkdir static
cp /etc/config/workflow ./static/workflow.yaml
cp /etc/config/agents ./static/agents.yaml

python3.11 src/api.py

