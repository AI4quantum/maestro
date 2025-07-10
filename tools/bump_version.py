#!/usr/bin/env python3

import re
import os
from pathlib import Path


def parse_version(tag: str) -> tuple[int, int, int]:
    version_str = tag.lstrip("v")
    return tuple(map(int, version_str.strip().split(".")))


def main():
    github_tag = os.environ.get("GITHUB_REF_NAME")
    if not github_tag:
        print("::error::GITHUB_REF_NAME not set.")
        exit(1)

    major, minor, patch = parse_version(github_tag)
    current_version_str = f"{major}.{minor}.{patch}"
    next_version_str = f"{major}.{minor + 1}.0"

    print(f"Updating README to {current_version_str}")
    print(f"Bumping pyproject.toml to {next_version_str}")

    repo_root = Path(__file__).parent.parent
    pyproject_path = repo_root / "pyproject.toml"
    readme_path = repo_root / "README.md"

    readme_content = readme_path.read_text()
    updated_readme = re.sub(
        r"@v\d+\.\d+\.\d+", f"@v{current_version_str}", readme_content
    )
    readme_path.write_text(updated_readme)

    pyproject_content = pyproject_path.read_text()
    updated_pyproject = re.sub(
        r'version\s*=\s*"\d+\.\d+\.\d+"',
        f'version = "{next_version_str}"',
        pyproject_content,
    )
    pyproject_path.write_text(updated_pyproject)


if __name__ == "__main__":
    main()
