# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

#!/usr/bin/env python3

import sys, subprocess
import re

def lint():
    try:
        subprocess.run(["ruff", "format", "."], check=True)
        subprocess.run(["ruff", "check", "."], check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)

def commit():
    if len(sys.argv) < 2:
        print('Usage: uv run commit "<commit message>"')
        sys.exit(1)

    commit_msg = sys.argv[1]
    if not re.match(r'^(feat|fix|docs|style|refactor|test|chore)(\([a-z-]+\))?: .+', commit_msg):
        print('Error: Commit message must follow the conventional commits format:')
        print('<type>(<scope>): <subject>')
        print('\nTypes: feat, fix, docs, style, refactor, test, chore')
        sys.exit(1)

    print("📦 Adding files...")
    subprocess.run(["git", "add", "--all"], check=True)

    print("📝 Committing changes...")
    subprocess.run(["git", "commit", "-s", "-m", commit_msg], check=True)

    print("Successfully committed changes")

if __name__ == '__main__':
    commit()
