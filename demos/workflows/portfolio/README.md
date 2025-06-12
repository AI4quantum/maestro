# Quantum Portfolio Optimizer Example

A multi-agent workflow using Maestro: Allows user to select a set of stock then the quantum portfolio optimizer makes the optimized portfolio with the stocks

## Mermaid Diagram

<!-- MERMAID_START -->
```mermaid
sequenceDiagram
participant stock
participant portfolio
stock->>portfolio: stock
portfolio->>portfolio: portfolio

```
<!-- MERMAID_END -->

## Getting Started

* Run a local instance of the [bee-stack](https://github.com/i-am-bee/bee-stack/blob/main/README.md)

* Verify a valid llm is available to bee-stack

* Install [maestro](https://github.com/i-am-bee/beeai-labs) dependencies: `cd ../../../maestro && poetry shell && poetry install && cd -`

* Configure environmental variables: `cp example.env .env`

* Copy `.env` to common directory: `cp .env ./../common/src`

## Running the Workflow

Assuming you are in maestro top level:

`maestro deploy demos/workflows/portfolio/agent.yaml demos/workflows/portfolio/workflow.yaml` 


