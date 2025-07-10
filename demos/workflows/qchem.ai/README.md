# Summary.ai Example

A multi-agent workflow using Maestro: Allows user to retrieve information about a chemical molecule, query quri chemistry, and get a summary of relevant news papers and patents.

## Mermaid Diagram

<!-- MERMAID_START -->
```mermaid
sequenceDiagram
participant input molecule
participant pubchem agent
participant open fermion
participant mock quri
participant news patents papers
participant generate summary
input molecule->>pubchem agent: Step1
pubchem agents->>open fermion: Step2
open fermion->>mock quri: Step3
mock quri->>news patents papers: Step4
news patents papers->>generatue summary: Step5
end
```
<!-- MERMAID_END -->

## Getting Started

* Run a local instance of the [bee-stack](https://github.com/i-am-bee/bee-stack/blob/main/README.md)

* Verify a valid llm is available to bee-stack

* Install [maestro](https://github.com/AI4quantum/maestro): 
   ```bash
   pip install git+https://github.com/AI4quantum/maestro.git@v0.1.0
   ```
* Install requirements `pip install -r ./demos/workflows/qchem.ai/requirements.txt`

* (Optional) In order to query patents, search and replace the value for `X-API-KEY` with your USPTO apikey in the `agents.yaml`

* Configure environmental variables: `cp example.env .env`

## Running the Workflow

Assuming you are in maestro top level:

Create the agents:
````bash
maestro create ./demos/workflows/qchem.ai/agents.yaml
````

To run the workflow:

If you've already created the agents:
```bash
maestro run ./demos/workflows/qchem.ai/workflow.yaml
``` 
