# Maestro

Maestro is a tool for managing and running AI agents and workflows.

## Installation

### Requirements

- Python 3.11, 3.12, or 3.13
- uv installed (for dev install)

### Install

```bash
pip install git+https://github.com/AI4quantum/maestro.git@v0.8.0
```

Note: If using scoring or crewai agents, install:
```bash
pip install "maestro[crewai] @ git+https://github.com/AI4quantum/maestro.git@v0.8.0"
```

**Python Version Note**: While Maestro core supports Python 3.11-3.13, some demos and examples are tested primarily with Python 3.12. For the most stable experience with demos, we recommend using Python 3.12.

## Usage

1. Run a workflow:
```bash
maestro run <workflow_path>
```

2. Create an agent:
```bash
maestro create <agent_path>
```

3. Validate a workflow or agent:
```bash
maestro validate <path>
```

4. Serve workflows with streaming:
```bash
maestro serve <agents_file> <workflow_file>
```

## Streaming API

Maestro provides real-time streaming capabilities for workflows.

### Quick Example

```bash
# Start streaming server
maestro serve agents.yaml workflow.yaml

# Test streaming
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your prompt"}' \
  --no-buffer
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/AI4quantum/maestro.git
cd maestro
```

2. Install in editable mode (automatically builds UI if Node.js is available):
```bash
uv pip install -e .
```

Or use uv sync for development dependencies:
```bash
uv sync --all-extras
```

3. Run tests:
```bash
uv run pytest
```

4. Run the formatter:
```bash
uv run ruff format
```

5. Run the linter:
```bash
uv run ruff check --fix
```

**Note**: If Node.js is available, the UI will be automatically built during installation (`npm install && npm run build`). If Node.js is not installed, the UI components will be skipped but all core functionality will still work.

## UI Options

Maestro provides multiple ways to interact with workflows:

### React UI (Default)
Deploy workflows with React's interactive interface:

```bash
maestro deploy agents.yaml workflow.yaml
```

### React UI
Deploy workflows with the React/TypeScript interface:

```bash
maestro deploy agents.yaml workflow.yaml --node-ui
```

Both UIs are automatically built and included during installation when Node.js is available.

## Agent Evaluation

Maestro includes automatic evaluation capabilities using IBM's watsonx governance platform:

Note: This feature is optional and disabled by default. To opt in, set the environment variable `MAESTRO_AUTO_EVALUATION=true` when running workflows. If unset or set to anything else, evaluation will be skipped.

```bash
# Enable optional evaluation (opt-in)
export MAESTRO_AUTO_EVALUATION=true
maestro run <agents_file> <workflow_file>
```

Alternatively, you can enable evaluation via the CLI flag:

```bash
maestro run <agents_file> <workflow_file> --evaluate
```

- Reference: [IBM watsonx governance Agentic AI Evaluation SDK](https://dataplatform.cloud.ibm.com/docs/content/wsj/model/wxgov-agentic-ai-evaluation-sdk.html?context=wx&locale=en#examples)
- Prerequisites: IBM Cloud account, valid `WATSONX_APIKEY`, service access to watsonx.governance (usage may incur costs), and a Python 3.11 evaluation environment (`.venv-eval`).
- Agent model: Your choice of inference model for agents is independent from evaluation. For example, you can run a local Ollama model like `llama3.1:latest` for generation while using watsonx for evaluation.

For setup and usage, see the detailed guide: [Watsonx Evaluation README](docs/WATSONX_EVALUATION_README.md)

### Features
- **Automatic Evaluation**: No code changes required
- **Multiple Metrics**: Answer Relevance, Faithfulness, Context Relevance, Answer Similarity
- **Real Scores**: Actual numerical metrics (0.0-1.0 scale)
- **Transparent Integration**: Works with any existing agent
- **Dedicated Environment**: Uses `.venv-eval` (Python 3.11) for watsonx compatibility

For detailed documentation, see [Watsonx Evaluation README](docs/WATSONX_EVALUATION_README.md).

## Builder Frontend and Demos

The Maestro Builder (web interface) has been moved to a separate repository: [maestro-builder](https://github.com/AI4quantum/maestro-builder)

Example use cases are also in a separate repository: [maestro-demos](https://github.com/AI4quantum/maestro-demos)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.
