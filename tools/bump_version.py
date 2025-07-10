#!/usr/bin/env python3

import os
import re
from pathlib import Path


def parse_version(tag: str) -> tuple[int, int, int]:
    version_str = tag.lstrip("v")
    return tuple(map(int, version_str.strip().split(".")))


def strike_through_release_name(name: str, repo_root: Path):
    file_path = repo_root / ".release_names.md"
    if not file_path.exists():
        print(f"::warning::{file_path} not found. Skipping strike-through.")
        return

    content = file_path.read_text()
    escaped = re.escape(name)
    new_content, count = re.subn(
        rf"^- {escaped}(?!~)",
        f"- ~~{name}~~",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        print(f"::warning::Release name '{name}' not found in {file_path}.")
    else:
        file_path.write_text(new_content)
        print(f"✔️ Struck through release name '{name}' in {file_path}")


def main():
    github_tag = os.environ.get("GITHUB_REF_NAME")
    release_name = os.environ.get("RELEASE_NAME")
    if not github_tag:
        print("::error::GITHUB_REF_NAME not set.")
        exit(1)
    if not re.fullmatch(r"v\d+\.\d+\.\d+", github_tag):
        print(
            f"::error::Invalid GITHUB_REF_NAME '{github_tag}'. Expected format: vX.Y.Z"
        )
        exit(1)

    major, minor, patch = parse_version(github_tag)
    current_version_str = f"{major}.{minor}.{patch}"
    next_version_str = f"{major}.{minor + 1}.0"

    print(f"Updating README to {current_version_str}")
    print(f"Bumping pyproject.toml to {next_version_str}")

    repo_root = Path(__file__).resolve().parent.parent
    pyproject_path = repo_root / "pyproject.toml"
    readme_path = repo_root / "README.md"

    readme_content = readme_path.read_text()
    updated_readme = re.sub(
        r"@v\d+\.\d+\.\d+", f"@v{current_version_str}", readme_content
    )
    readme_path.write_text(updated_readme)
    print(f"✔️ Updated README.md with version tag @v{current_version_str}")

    pyproject_content = pyproject_path.read_text()
    updated_pyproject = re.sub(
        r'version\s*=\s*"\d+\.\d+\.\d+"',
        f'version = "{next_version_str}"',
        pyproject_content,
    )
    pyproject_path.write_text(updated_pyproject)
    print(f"✔️ Bumped pyproject.toml version to {next_version_str}")
    strike_through_release_name(release_name, repo_root)


if __name__ == "__main__":
    main()
