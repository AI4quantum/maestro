# Core Principles

## Preserve Existing Code

Do not modify code unnecessarily.

If a change is required, make the smallest, simplest modification that achieves the goal.

Avoid over-engineering or introducing complexity.

## Minimalism

No unnecessary comments or explanations in the code.

Code should be self-explanatory whenever possible.

Keep files clean and consistent with the current style.

## Environment

Always activate the .venv before running commands or making changes:

`source .venv/bin/activate`

Ensure dependencies are installed in the .venv, not globally.

## Development Workflow

Keep changes isolated to the relevant file(s).

Use existing patterns and structures whenever possible.

Avoid refactoring unless it is absolutely required for the task.

## Testing

Prefer simple, direct test cases over exhaustive coverage.

## Pull Requests

Keep PRs focused on a single issue or feature.

Provide clear commit messages explaining what was changed and why.

Avoid extra formatting or cosmetic changes unless they are directly related to the task.

## Do & Don’t

✅ Do

Always activate .venv before running commands.

Make the smallest change needed to solve the problem.

Follow existing code style and patterns.

Keep changes isolated and focused.

Write clear commit messages with context.

❌ Don’t

Don’t modify code that doesn’t need to change.

Don’t add unnecessary comments or explanations in code.

Don’t introduce new dependencies unless absolutely required.

Don’t refactor large sections unless it’s unavoidable.

Don’t mix unrelated changes in the same commit or PR.