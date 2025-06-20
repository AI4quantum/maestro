# Simple Workflow Demo Example

This demo shows how to use Maestro to create a simple example workflow.

## Prerequisites

* Python 3.12
* [maestro](https://github.com/AI4quantum/maestro) installed

## Setup

1. Install [maestro](https://github.com/AI4quantum/maestro)
```bash
pip install git+https://github.com/ajbozarth/maestro.git
```

## Running the workflow

Assuming you are in the `demos` directory:

1. Create the agents:
```bash
maestro create workflows/simple/agents.yaml
```

2. Run the workflow:

If you already created the agents and enabled the tool:
```bash
maestro run workflows/simple/workflow.yaml
```

OR

Directly deploy the workflow via streamlit: 
```bash
maestro deploy workflows/simple/agents.yaml workflows/simple/workflow.yaml
```
