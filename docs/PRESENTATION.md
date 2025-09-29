## Maestro

**Repository**: [https://github.com/AI4quantum/maestro](https://github.com/AI4quantum/maestro)
**Started**: 11/2024
**Code**: python 81.3%
**License**: Apache-2.0 license

---

## What is Maestro

Maestro is an orchestration framework for AI agents that enables the creation, management, and execution of complex workflows involving multiple AI agents. Key features include:

- **Agent Orchestration**: Coordinate multiple AI agents to work together on complex tasks
- **Workflow Management**: Define step-by-step processes with conditional logic and flow control
- **Tool Integration**: Connect agents with external tools and services
- **YAML Configuration**: Define agents and workflows using simple YAML files
- **Flexible Deployment**: Run locally, in containers, or on Kubernetes

---

## Agents in Maestro

### Supported Agent Types
- **BeeAI**: Default agent framework with local and remote options
- **CrewAI**: Integration with CrewAI framework
- **DSPy**: Integration with DSPy framework for reasoning
- **OpenAI**: Direct integration with OpenAI models
- **Code**: Execute arbitrary Python code
- **Custom**: Create custom agent implementations
- **Remote**: Connect to remote agent services
- **Mock**: For testing and development

---

### Example Agent YAML
```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: weather
  labels:
    app: weather
spec:
  model: gpt-oss:latest
  description: retrieve weather information
  instructions: You are a helpful agent. You have a weather tool.
  framework: openai
  mode: local
  tools:
  - weather
```

---

## Workflows in Maestro

### Supported Flow Controls
- **Sequential Steps**: Execute agents in a predefined order
- **Conditional Branching**: Use `if/then/else` or `case/do` conditions to control flow
- **Context Routing**: Direct specific outputs to specific agents using the `from` field
- **Parallel Execution**: Run multiple agents simultaneously with `parallel`
- **Looping**: Repeat steps until a condition is met with `loop` and `until`
- **Event-based Execution**: Trigger workflows based on events with `cron` scheduling
- **Error Handling**: Define exception handlers for workflow errors

---

### Example Workflow YAML
```yaml
apiVersion: maestro/v1
kind: Workflow
metadata:
  name: portfolio workflow
  labels:
    app: portfolio optimizer
spec:
  template:
    metadata:
      name: portfolio
      labels:
        app: portfolio
    agents:
      - stock
      - portfolio
      - plot
    prompt: 8801.T, ITX.MC, META, GBPJPY=X, CLF
    steps:
      - name: stock
        agent: stock
      - name: portfolio
        agent: portfolio
      - name: plot
        agent: plot
```

---

## Tools in Maestro

Maestro supports integrating external tools with agents through:

- **MCP Tools**: Model Control Protocol tools for standardized integration
- **Built-in Tools**: Weather, search, code execution, etc.
- **Custom Tools**: Create and integrate your own tools

---

### Example Tool YAML
```yaml
apiVersion: maestro/v1alpha1
kind: MCPTool
metadata:
  name: weather
  namespace: default
spec:
  url: "http://localhost:8000/mcp" 
  transport: streamable-http
  name: weather
  description: weather 
```

---

Maestro provides a powerful framework for orchestrating AI agents in complex workflows, enabling sophisticated applications that leverage multiple specialized agents working together with external tools and services.

---

## Get Started

- **Repository**: [https://github.com/AI4quantum/maestro](https://github.com/AI4quantum/maestro)
- **Installation**: `pip install git+https://github.com/AI4quantum/maestro.git@v0.7.0`
- **Demos**: [https://github.com/AI4quantum/maestro-demos](https://github.com/AI4quantum/maestro-demos)
- **Builder**: [https://github.com/AI4quantum/maestro-builder](https://github.com/AI4quantum/maestro-builder)
- **Contacts**: [maestro/MAINTAINERS.md](https://github.com/AI4quantum/maestro/blob/main/MAINTAINERS.md)
