#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import requests


def main():
    github_token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]

    with open(".release_names.md", "r") as f:
        all_names = [
            line.strip().lstrip("- ")
            for line in f
            if line.strip() and not line.strip().startswith("**") and "~~" not in line
        ]

    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(
        f"https://api.github.com/repos/{repo}/releases", headers=headers
    )

    if not response.ok:
        print(f"::error::Failed to fetch releases: {response.status_code}")
        exit(1)

    releases = response.json()
    used_names = {
        r["name"].split(" – ")[0]
        for r in releases
        if r.get("name") and " – " in r["name"]
    }

    next_name = next((name for name in all_names if name not in used_names), None)

    if not next_name:
        print("::error::No unused release names available.")
        exit(1)

    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"release_name={next_name}\n")


if __name__ == "__main__":
    main()
