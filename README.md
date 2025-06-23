# Maestro

Maestro is a tool for managing and running AI agents and workflows.

## Installation

```bash
pip install git+https://github.com/AI4quantum/maestro.git@v0.1.0
```

Note: If using crewai agents, install:
```bash
pip install "maestro[crewai] @ git+https://github.com/AI4quantum/maestro.git@v0.1.0"
```

## Usage

1. Run a workflow:
```bash
maestro run <workflow_path>
```

2. Run an agent:
```bash
maestro run <agent_path>
```

3. Validate a workflow or agent:
```bash
maestro validate <path>
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/AI4quantum/maestro.git
cd maestro
```

2. Install development dependencies:
```bash
uv pip install -e .
```

3. Run tests:
```bash
uv run pytest
```

4. Run linter:
```bash
uv run black
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.