#!/bin/bash

cd "$(dirname "$0")/../../../" || exit 1
echo "📂 Running from: $(pwd)"
export PYTHONPATH="$(pwd):$(pwd)/src"
echo "🐍 PYTHONPATH set to: $PYTHONPATH"
if ! command -v maestro &> /dev/null
then
    echo "⚠️  Maestro CLI not found, installing..."
    pip install --user maestro
fi

echo "📝 Validating agents.yaml..."
PYTHONPATH=$PYTHONPATH maestro validate ./schemas/agent_schema.json ./demos/workflows/ibm-summary.ai/agents.yaml

echo "📝 Validating workflow.yaml..."
PYTHONPATH=$PYTHONPATH maestro validate ./schemas/workflow_schema.json ./demos/workflows/ibm-summary.ai/workflow.yaml

echo "🚀 Running workflow..."
PYTHONPATH=$PYTHONPATH maestro run ./demos/workflows/ibm-summary.ai/agents.yaml ./demos/workflows/ibm-summary.ai/workflow.yaml