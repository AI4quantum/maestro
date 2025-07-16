# Maestro Project User Guide

## Table of Contents
1. [Maestro Language](#maestro-language)
2. [Maestro CLI](#maestro-cli)
3. [Maestro UIs](#maestro-uis)
4. [Examples](#examples)
5. [Demos](https://github.com/AI4quantum/maestro-demos)

## Maestro Language

Maestro defines agents and workflows in yaml format. 
### Agent
Agent example defined in yaml format is: 
```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: current-temperature
  labels:
    app: mas-example
spec:
  model: "llama3.1:latest"
  framework: beeai
  mode: remote
  description: Get the current weather
  tools:
    - code_interpreter
    - weather
  instructions: An input is given of a location. Use the OpenMeteo tool to get today's current forecast for the location. Return results in the format - location, temperature in Fahrenheit, and date.
    Example output - New York City, 44.9°F, March 26, 2025
```
The syntax of the agent definition is defined in the [json schema](https://github.com/AI4quantum/maestro/blob/main/schemas/agent_schema.json).

- **apiVersion**: version of agent definition format.  This must be `maestro/v1alpha1` now.
- **kind**: type of object. `Agent` for agent definition
- **metadata**:
  - **name**: name of agent
  - **labels**: array of key, value pairs. This is optional and can be used to associate any information to this agent 
- **spec**:
  - **model**: LLM model name used by the agent  eg. "llama3.1:latest"
  - **framework**: agent framework type.  Current supported agent frameworks are : "beeai", "crewai", "openai", "remotem", "custom" and "code"
  - **mode**: Remote or Local.  Some agents support agent remotely.  Remote is supported by "beeai" and "remote" 
  - **description**: Description of this agent
  - **tools**: array of tool names. This is not implemented yet.

### Workflow
Workflow example defined in yaml format is:
```yaml
piVersion: maestro/v1alpha1
kind: Workflow
metadata:
  name: maestro-deployment
  labels:
    app: mas-example
spec:
  template:
    metadata:
      labels:
        app: mas-example
    agents:
      - current-temperature
      - hot-or-not
      - cold-activities
      - hot-activities
    prompt: New York City
    steps:
      - name: get-temperature
        agent: current-temperature
      - name: hot-or-not
        agent: hot-or-not
        condition:
        - if: (input.find('hotter') != -1)
          then: hot-activities
          else: cold-activities
      - name: cold-activities
        agent: cold-activities
        condition:
        - default: exit
      - name: hot-activities
        agent: hot-activities
      - name: exit
```
The syntax of the workflow definition is defined in the [json schema](https://github.com/AI4quantum/maestro/blob/main/schemas/workflow_schema.json).

- **apiVersion**: version of agent definition format.  This must be `maestro/v1alpha1` now.
- **kind**: type of object. `Workflow` for workflow definition
- **metadata**:
  - **name**: name of workflow
  - **labels**: array of key, value pairs. This is optional and can be used to associate any information to this workflow 
- **spec**:
  - **template**:
    - **metadata**:
      - **labels**: array of key, value pairs. This is optional and can be used to associate any information to this template
    - **agents**: array of agent names used in this workflow
    - **prompt**: initial prompt for this workflow
    - **event**: definition of event.  Event triggers workflow execution
    - **exception**: definition of exception handling.
    - **steps**: array of steps.  Steps are executed from top to bottom in this list unless the step has `condition` in it. 
      - **name**: name of step
      - **agent**: name of agent for this step

#### Step

The step is an unit of work in the workflow.  It includes execution of agent, execution of agents in parallel or sequential, taking user input, preprocess input of step, post process execution output, deciding the next step to be executed.

The step has properties that define the work of the step.  Everything is optional except `name` property.

- **name**: name of step definition
- **agent**: name of agent executed in this step
- **inputs**: array source passed to agent as argument
  - inputs has an array of `from` that has source of input for the agent input
  - Each input from source for the agent are put into a list
    - source: `prompt`- the initial workflow prompt
    - source: `instructions:step name` - the instructions for the agent in the step
    - source: step name - the result of the step execution
    - source: other string - this string
- **context**: array of string or object passed to agent as context
- **input**: definition of user prompt and user input processing
  - Input takes user input in the command window.
  - Input has `prompt` and `template`
  - The `prompt` is the user input prompt string.  The `{prompt}` in the prompt string is replaced by the input of this step.
  - The `template` is the string to the next step.  The `{prompt}` and `{response}` in the template string are replaced by the input of this step and the user input.  
- **loop**: definition iterative agent execution
  - When the input is an array, loop repeats agent execution until each input element is passed to the agent 
  - When the input is not an array, loop repeats agent execution until the output meets the `until` expression.
  - The until expression is a python statement that returns true or false.  The loop stops when the until expression is true.  The LLM output is passed in the expression as a variable `input`.
  ```
  loop:
    agent: agent1
    until expression
  ```    
- **condition**: step execution flow control.  The next step is changed according to the agent execution output
  - Condition supports `if`, `then`, `else` and `case` `do`.
  - expression is a python statement that returns true or false.  The LLM output is passed in the expression as a variable `input`.
  - The based on the expression evaluation, the next step is selected. 
  - if:
  ```
  - if: expression
    then: next step 1
    else: next step 2  
  ```
  - case:
  ```
  - case: expression 1
    do: next step 1
  - case: expression 2
    do: next step 2
  - default
    do: next step 3
  ```
- **parallel**: array of agents that are executed in parallel
  - Parallel has an array of agents.  It executes all agents in the array at the same time.  The output of each agent is put together in order in the array in the output.
  - When the input is an array, each element of the array passed to the agent in the array.
  - When the input in not an array, the same input is passed to all agents in the array.
  ```
  parallel:
  - agent1
  - agent2
  ```

### event

The event is one way to trigger workflow execution.  Only cron event is supported now.

- **name**: name of event definition
- **cron**: cron job in standard cron format
- **agent**: agent name executed in event processing
- **steps**: step name executed in event processing
- **exit**: cron job exit condition.  Python statement that evaluates the execution output.  True for exit

### exception

The exception is executed when an exception happens during the execution of the workflow.

- **name**: name of exception definition
- **agent**: name of agent executed in exception handling

## Maestro CLI

The Maestro Command Line Interface (CLI) allows users to manage workflows that includes validate, run, deploy and some other commands.

### Basic Commands

- `maestro create` AGENTS_FILE [options]: create agent  
- `maestro deploy` AGENTS_FILE WORKFLOW_FILE [options] [ENV...] deploy and run the workflow in docker, kubernetes or Streamit
  - target option: `--deocker`: deployed in docker, `--k8s`: deployed in kubernetes cluster, `--streamlit`: deployed in streamlit
  - environment option: `env` takes a string that has list of key=value separated by comma.
  - auto_prompt option: '--auto-prompt` automatically starts workflow when the workflow is deployed 
- `maestro mermaid` WORKFLOW_FILE [options]: generate the mermaid output for the workflow
- `maestro run` WORKFLOW_FILE [options]: run the workflow with existing agents in command window
- `maestro run` AGENTS_FILE WORKFLOW_FILE [options]: create agents and run the workflow in command window
- `maestro serve` AGENTS_FILE WORKFLOW_FILE [options]: serve agents via HTTP API endpoints
  - the WORKFLOW_FILE is optional.  If it is provided, the workflow is served via HTTP API endpoints 
  - `--port PORT`: port to serve on (default: 8000)
  - `--host HOST`: host to bind to (default: 127.0.0.1)
  - `--agent-name NAME`: specific agent name to serve (if multiple agents in file)
  - `--streaming`: enable streaming responses
- `maestro validate` YAML_FILE [options]: validate agent or workflow definition yaml file
- `maestro validate` SCHEMA_FILE YAML_FILE [options]: validate agent or workflow definition yaml file using the specified schema file 
- `maestro meta-agents` TEXT_FILE [options]: run maestro meta agent with the given description file
- `maestro clean` [options]: clean up Streamit servers of maestro
- `maestro create-cr` YAML_FILE [options]: create maestro custom resources in kubernetes cluster

### Serving Agents via HTTP API

The `maestro serve` command allows you to expose Maestro agents as HTTP API endpoints, making them accessible via REST API calls. This is useful for integrating agents into web applications, microservices, or other systems that need to communicate with AI agents.

#### Basic Usage

```bash
# Serve a single agent from an agents file
maestro serve agents.yaml

# Serve on a custom port and host
maestro serve agents.yaml --port 8080 --host 0.0.0.0

# Serve a specific agent from a multi-agent file
maestro serve agents.yaml --agent-name my-agent

# Enable streaming responses
maestro serve agents.yaml --streaming
```

#### API Endpoints

Once the server is running, the following endpoints are available:

**POST /chat** - Send prompts to the agent
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?", "stream": false}'
```

Response:
```json
{
  "response": "Hello! I'm doing well, thank you for asking. How can I help you today?",
  "agent_name": "serve-test-agent",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**GET /health** - Health check endpoint
```bash
curl "http://127.0.0.1:8000/health"
```

Response:
```json
{
  "status": "healthy",
  "agent_name": "serve-test-agent",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**GET /agents** - List available agents
```bash
curl "http://127.0.0.1:8000/agents"
```

Response:
```json
{
  "agents": ["serve-test-agent"],
  "current_agent": "serve-test-agent"
}
```

**GET /docs** - Auto-generated API documentation (Swagger UI)

#### Example Agent Configuration

```yaml
apiVersion: maestro.ai4quantum.com/v1alpha1
kind: Agent
metadata:
  name: serve-test-agent
spec:
  framework: mock
  description: A simple test agent for serving via HTTP
  instructions: You are a helpful assistant. Respond to user prompts in a friendly manner.
  input: text
  output: text
```

#### Use Cases

- **Web Application Integration**: Embed AI agents in web applications
- **Microservices**: Create AI-powered microservices
- **API Gateway**: Expose agents through API gateways
- **Testing**: Test agent functionality via HTTP requests
- **Integration**: Connect agents to other systems via REST APIs

#### Security Considerations

- The server runs on localhost by default for security
- Use `--host 0.0.0.0` only when you need external access
- Consider adding authentication and rate limiting for production use
- Use HTTPS in production environments

### Serving Workflow via HTTP API

The `maestro serve` command with agants and workflow files allows you to expose Maestro workflow as HTTP API endpoints, making them accessible via REST API calls. This is useful for integrating workflow into another workflows, web applications, microservices, or other systems that need to communicate with AI workflow.

#### Basic Usage

```bash
# Serve a workflow in a workflow file
maestro serve agents.yaml workflow.yaml

# Serve on a custom port and host
maestro serve agents.yaml workflow.yaml --port 8080 --host 0.0.0.0
```

#### API Endpoints

Once the server is running, the following endpoints are available:

**POST /chat** - Send prompts to the workflow
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?", "stream": false}'
```

Response:
```json
{'response': "{'final_prompt': 'Hello, this is a test!', 'step1': 'Hello, this is a test!', 'step2': 'Hello, this is a test!', 'step3': 'Hello, this is a test!'}", 'workflow_name': 'simple workflow', 'timestamp': '2025-07-08T01:01:35.420413Z'}

```

**GET /health** - Health check endpoint
```bash
curl "http://127.0.0.1:8000/health"
```

Response:
```json
{
  "status": "healthy",
  "agent_name": "serve-test-agent",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**GET /docs** - Auto-generated API documentation (Swagger UI)


## Maestro UIs

### Streamlit deploy UI

Maestro initial UI

There are 2 parts in Maestro UI.  The first part is information about the workflow.  It has the name of the workflow, buttons that show contents of the agent and the workflow definitons and a button that shows the diagram of the workflow.  The second part is workflow execution.  It has the workflow prompt input field and its prompt suggestions and the submit button that triggers the workflow.  The output of the workflow execution is also displayed in this part.

![Screenshot 2025-06-05 at 11 09 36 AM](https://github.com/user-attachments/assets/7a7cd362-6995-471f-a1b5-ec9c6729c8b4)

Show diagram button shows the workflow diagram 

![Screenshot 2025-06-05 at 11 13 50 AM](https://github.com/user-attachments/assets/afabaa19-0a9d-4893-b6c6-da958caf6492)

agents.yaml and workflow.yaml buttons show agent and workflow yaml files contents

![Screenshot 2025-06-05 at 11 14 49 AM](https://github.com/user-attachments/assets/82a51bde-3032-4a46-a794-8368e8cfd0ea)

Submit button starts the workflow with the input prompt string

![Screenshot 2025-06-05 at 11 26 06 AM](https://github.com/user-attachments/assets/1acebecf-0add-4ae7-b873-13d4e8992cfd)

### Docker, Kubernates deploy UI

Maestro initial UI

![Screenshot 2025-06-05 at 12 39 01 PM](https://github.com/user-attachments/assets/0053422d-f1be-4cd5-af10-323630e3aa7d)

The workflow name and "Agent definitions" links show or download the workflow and agent yaml files.
The workflow diagram is shown.
The input field for the prompt and the Re-run button starting the workflow at the bottom.

![Screenshot 2025-06-05 at 12 40 30 PM](https://github.com/user-attachments/assets/b87f4a78-6218-4a85-a1b8-de01a9f0da1e)

The workflow output come out after the input of the prompt string and pressing of the Re-run button

### maestro run output

The `maestro run` command output comes out in the command window.
![Screenshot 2025-06-05 at 1 07 28 PM](https://github.com/user-attachments/assets/f9b9f90c-6e9a-4c8d-b9fc-6b178355644d)

## Examples

### [Weather Checker AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/weather-checker.ai/README.md): Simple Sequential Workflow
The weather checker ai is a simple sequential workflow.  I have 2 agents Temperature agent that retrieves the current temperature of the given location and hot-or-not Agent that retrieves the historical temperature of the given location and returns whether the current temperature is hotter or colder.

#### agent.yaml
```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: Temperature Agent
  labels:
    app: mas-example
spec:
  model: "llama3.1:latest"
  framework: beeai
  mode: remote
  description: Get the current weather
  tools:
    - code_interpreter
    - weather
  instructions: An input is given of a location.  Use the OpenMeteo tool to get today's current forecast for the location. Return results in the format -location, temperature in Fahrenheit, and date.
---
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: hot-or-not Agent
  labels:
    app: mas-example
spec:
  model: "llama3.1:latest"
  framework: beeai
  mode: remote
  description: Is the current temperature hotter than usual?
  tools:
    - code_interpreter
    - weather
  instructions: |
    Use the OpenMeteo weather tool to find the historical temperature of the given location.  Return whether the current temperature is hotter or colder.

    Example Process:
    Input: New York, 50 degrees F

    Compare input against historical temperature (lets say 55) in input location.

    Output: The current temperature is colder than the historical temperature.
```
 
#### workflow.yaml
```yaml
apiVersion: maestro/v1alpha1
kind: Workflow
metadata:
  name: Weather Checker AI
  labels:
    app: mas-example
spec:
  template:
    metadata:
      labels:
        app: mas-example
    agents:
      - Temperature Agent
      - hot-or-not Agent
    prompt: New York City
    steps:
      - name: get_temperature
        agent: Temperature Agent
      - name: compare_temperature
        agent: hot-or-not Agent
```
### loop workflow: Simple Loop Workflow
The loop workflow demonstrates simple loop workflow.  It has 2 agents. The generate1-10 agent that generates one number between 1 and 10 and the countdown Agent that gets a number and dicrease it by 1 and it returns "happy" when number becomes 0.  The countdown agent is executed in the loop until the agent returns "happy. 

#### agent.yaml
```
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: generate1-10
  labels:
    app: test-example
spec:
  model: "llama3.1:latest"
  mode: remote
  description:
  tools:
    - code_interpreter
    - test
  instructions: genereate a number between 1 and 10 and just output the number

---

apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: countdown
  labels:
    app: test-example
spec:
  model: "llama3.1:latest"
  mode: remote
  description: this is a test
  tools:
    - code_interpreter
    - test
  instructions: you get a nunber.  Dicrease the number by 1 and if the number becomes 0, output "happy" otherwise output the new number.
```
#### workflow.yaml
```
apiVersion: maestro/v1
kind: Workflow
metadata:
  name: loop workflow
  labels:
    app: example
spec:
  strategy:
    type: sequence
  template:
    metadata:
      name: loop-workflow
      labels:
        app: example
	use-case: test
    agents:
	- generate1-10
        - countdown
    prompt: Generate a number
    steps:
      - name: step1
        agent: generate1-10
      - name: step2
        loop:
            agent: countdown
            until: (input.find("happy") != -1)
```
#### output
```
🐝 Running generate1-10...

🐝 Response from generate1-10: 7

🐝 Running countdown...

🐝 Response from countdown: 6

🐝 Running countdown...

🐝 Response from countdown: 5

🐝 Running countdown...

🐝 Response from countdown: 4

🐝 Running countdown...

🐝 Response from countdown: 3

🐝 Running countdown...

🐝 Response from countdown: 2

🐝 Running countdown...

🐝 Response from countdown: 1

🐝 Running countdown...

🐝 Response from countdown: 0

🐝 Running countdown...

🐝 Response from countdown: happy
```

## Demos

For comprehensive demos and examples, visit: [https://github.com/AI4quantum/maestro-demos](https://github.com/AI4quantum/maestro-demos)

### Demos with workflow

- [Activity Planner AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/activity-planner.ai/README.md)
- [CBOM AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/cbom.ai/README.md)
- [IBM Summary AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/ibm-summary.ai/README.md)
- [Summary AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/summary.ai/README.md)
- [Weather Checker AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/weather-checker.ai/README.md)

## Demos with agent / tool integration

- [Activity Planner CrewAI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/activity-planner-crewai.ai/README.md)
- [MCP GH Tools AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/mcp-gh-tools.ai/README.md)
- [OpenAI MCP AI](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/mcp-gh-tools.ai/README.md)

## Demo Meta Agent
- [Meta Agents](https://github.com/AI4quantum/maestro-demos/blob/main/workflows/meta-agents/README.md)
