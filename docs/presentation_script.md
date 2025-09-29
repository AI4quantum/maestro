# Maestro Presentation Script (10 minutes)

## Introduction (1 minute)
Good [morning/afternoon/evening], everyone. Today, I'm excited to introduce you to Maestro, an orchestration framework for AI agents that addresses a critical challenge in the AI development landscape. While Large Language Models have become increasingly powerful, building robust applications with them remains complex. Maestro simplifies this process by providing a structured way to coordinate multiple AI agents, manage workflows, and integrate external tools.

Maestro is an open-source project under the Apache-2.0 license that started in November 2024, primarily written in Python. Let's dive into what makes it special.

## What is Maestro (1.5 minutes)
At its core, Maestro is designed to enable the creation, management, and execution of complex workflows involving multiple AI agents. Think of it as a conductor that coordinates different AI specialists to work together harmoniously.

The key features that make Maestro powerful include:
- **Agent Orchestration**: Coordinate multiple AI agents to collaborate on complex tasks
- **Workflow Management**: Define step-by-step processes with conditional logic and flow control
- **Tool Integration**: Connect agents with external tools and services
- **YAML Configuration**: Define agents and workflows using simple, readable YAML files
- **Flexible Deployment**: Run locally, in containers, or on Kubernetes

This flexibility allows developers to build sophisticated AI applications without getting bogged down in implementation details.

## Agents in Maestro (2 minutes)
Agents are the building blocks of any Maestro application. The framework supports multiple agent types to fit different needs:

- **BeeAI**: For those already using the BeeAI framework
- **CrewAI**: For those already using the CrewAI framework
- **DSPy**: Integration with DSPy for enhanced reasoning capabilities
- **OpenAI**: Direct integration with OpenAI's powerful models
- **Code**: Execute arbitrary Python code as part of your workflow
- **Custom**: Create your own agent implementations for specialized needs
- **Remote**: Connect to remote agent services
- **Mock**: For testing and development purposes

Let me show you how simple it is to define an agent in Maestro. Here's an example YAML configuration:

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

This configuration creates a weather agent using the gpt-oss model that can access a weather tool. The declarative nature makes it easy to understand and modify.

## Workflows in Maestro (2.5 minutes)
Workflows are where Maestro truly shines. They allow you to define how agents interact and collaborate to accomplish complex tasks. Maestro supports sophisticated flow controls:

- **Sequential Steps**: Execute agents in a predefined order
- **Conditional Branching**: Use if/then/else or case/do conditions
- **Context Routing**: Direct specific outputs to specific agents
- **Parallel Execution**: Run multiple agents simultaneously
- **Looping**: Repeat steps until a condition is met
- **Event-based Execution**: Trigger workflows based on events or schedules
- **Error Handling**: Define exception handlers for workflow errors

Here's an example workflow that optimizes a financial portfolio:

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

This workflow coordinates three specialized agents: one to gather stock information, another to optimize the portfolio, and a third to visualize the results. The workflow passes a list of financial instruments as the initial prompt.

## Tools in Maestro (2 minutes)
Tools extend the capabilities of agents by connecting them to external services and functionalities. Maestro provides several ways to integrate tools:

- **MCP Tools**: Model Context Protocol tools for standardized integration
- **Built-in Tools**: Weather, search, code execution, and more
- **Custom Tools**: Create and integrate your own specialized tools

Here's how you can define a weather tool using YAML:

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

This configuration connects to a weather service running locally, making it available to any agent that needs weather information.

## Conclusion and Getting Started (1 minute)
To summarize, Maestro provides a powerful framework for orchestrating AI agents in complex workflows, enabling sophisticated applications that leverage multiple specialized agents working together with external tools and services.

If you're interested in getting started with Maestro:
- Visit our GitHub repository at github.com/AI4quantum/maestro
- Install Maestro with pip: `pip install git+https://github.com/AI4quantum/maestro.git@v0.7.0`
- Check out our demos repository for examples
- Explore the Maestro Builder for a visual interface
- Reach out to our maintainers listed in the MAINTAINERS.md file

Thank you for your attention! I'm happy to answer any questions you might have about Maestro and how it can help with your AI application development needs.