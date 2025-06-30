# Contributing to Maestro Demos

Thank you for your interest in contributing to Maestro demos! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/AI4quantum/maestro.git
cd maestro
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Activate the virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

## Development Workflow

1. Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "feat: your feature description"
```

3. Push your changes and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Code Style

We use [black](https://github.com/psf/black) for code formatting and [pylint](https://pylint.pycqa.org/) for linting. To ensure your code meets our style guidelines:

1. Install development dependencies:
```bash
uv pip install -e ".[dev]"
```

2. Run the linter:
```bash
uv run pylint src/
```

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. The format is:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Changes to the build process or auxiliary tools

Example:
```bash
git commit -m "feat(agent): add new agent type"
```

## Pull Request Process

1. Ensure all dependencies are installed (`uv pip install -e .`).
2. Run the test suite (`uv run pytest`).
3. Run the linter (`uv run pylint src/`).
4. Update documentation if necessary.
5. Create a pull request with a clear description of the changes.

## Additional Resources

- [Issue Tracker](https://github.com/AI4quantum/maestro/issues)
- [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Project Structure

```markdown
/maestro
│── /src                    # Source code for core functionalities
│   │── /schemas            # JSON schema definitions for agents and workflows
│       │── agent_schema.json
│       │── workflow_schema.json
│── /demos                  # Demo-specific workflows and agents
│   │── /workflows          
│       │── agents.yaml     # YAML file defining the agents used in the demo
│       │── workflow.yaml         
│── .env                    # Environment variables (use `example.env` as reference)
│── README.md               # Project documentation
│── CONTRIBUTING.md         # Contribution guidelines
```

---

## Setting Up Your Environment

### 1. Clone the Repository

```bash
git clone https://github.com/AI4quantum/maestro.git
cd maestro
```

### 2. Set Up the Virtual Environment

```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
uv pip install -e .
```

### 3. Configure Environment Variables

- Copy `example.env` and rename it to `.env`:

  ```bash
  cp example.env .env
  ```

---

## Validating and Running Demos with Maestro

### Validate Workflow and Agent YAML Files

Note: All these commands assume you are running from maestro top-level directory.

Ensure that your YAML definitions adhere to the correct schema before running them.

```bash
maestro validate ./schemas/agent_schema.json ./src/agents/meta_agent/agents.yaml
```

### Create Agents

To create agents (with the ability to manually add tools):

```bash
maestro create ./src/agents/meta_agent/agents.yaml
```

### Run the Workflow

If you have already created the agents and enabled the tools:

```bash
maestro run None ./src/agents/meta_agent/workflow.yaml
```

OR create the agents and run workflow in the same step:

```bash
maestro run ./src/agents/meta_agent/agents.yaml ./src/agents/meta_agent/workflow.yaml
```

---

## Creating a New Demo

### 1. Define Agents

- Create a YAML file in `/demos/agents.yaml` to define agents.
- Follow the `agent_schema.json` structure.

#### Example `agents.yaml`

```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: search_arxiv
spec:
  model: llama3.1
  description: "Searches for relevant ArXiv papers."
  instructions: "Given a topic, fetch relevant papers."
```

### 2. Define the Workflow

- Create a YAML file in `/demos/workflow.yaml`.
- Ensure it follows `workflow_schema.json`.

#### Example `workflow.yaml`

```yaml
apiVersion: maestro/v1alpha1
kind: Workflow
metadata:
  name: arxiv_search_demo
spec:
  strategy:
    type: sequence
  steps:
    - name: search_arxiv
      agent: search_arxiv
    - name: filter_papers
      agent: selector_agent
    - name: summarize
      agent: summary_agent
```

### 3. Document the Demo

- Add a `README.md` inside the `/demos` folder.
- Include:
  - Overview of the demo
  - Installation/setup steps
  - Example command to run the demo

---

## Testing and Debugging

### Debugging Tips

- Ensure all dependencies are installed (`uv pip install -e .`).
- Check for missing agents (`agent_store.json` must contain registered agents).
- Validate YAML schemas using `maestro validate` before running workflows.

---

## Code Style and Best Practices

- Use **docstrings** for all functions and classes.
- Write **meaningful commit messages**:

  ```bash
  git commit -m "Add new ArXiv search agent"
  ```

- Ensure workflows are **modular and reusable**.

---

## Submitting a Pull Request

1. **Fork the repository** and create a new branch:

   ```bash
   git checkout -b feature-new-demo
   ```
  
2. **Make your changes and commit**.
3. **Push to your fork** and create a Pull Request.

---

By following these guidelines, we ensure that all demos are consistent, well-documented, and easy to run using **Maestro**.
