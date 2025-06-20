# Maestro

Maestro is a tool for managing and running AI agents and workflows.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AI4quantum/maestro.git
cd maestro
```

2. Install dependencies:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Note: If using scoring agents, install:
```bash
uv pip install -e .[scoring]
```

## Usage

1. Run a workflow:
```bash
uv run maestro run <workflow_path>
```

2. Run an agent:
```bash
uv run maestro run <agent_path>
```

3. Validate a workflow or agent:
```bash
uv run maestro validate <path>
```

## Development

1. Install development dependencies:
```bash
uv pip install -e .
```

2. Run tests:
```bash
uv run pytest
```

3. Run linter:
```bash
uv run black
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.