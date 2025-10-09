#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=False, capture_output=True, text=True
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


def check_node_available():
    node_ok, _ = run_command("node --version")
    npm_ok, _ = run_command("npm --version")
    return node_ok and npm_ok


def build_ui():
    ui_dir = Path(__file__).parent / "src" / "maestro" / "ui"

    if not ui_dir.exists():
        print("Warning: UI directory not found, skipping UI build")
        return False

    package_json = ui_dir / "package.json"
    if not package_json.exists():
        print("Warning: package.json not found, skipping UI build")
        return False

    dist_dir = ui_dir / "dist"
    if dist_dir.exists() and package_json.stat().st_mtime < dist_dir.stat().st_mtime:
        print("UI dist is up to date, skipping build")
        return True

    print("Building UI assets...")

    print("Installing npm dependencies...")
    success, stderr = run_command("npm install", cwd=ui_dir)
    if not success:
        print(f"Warning: npm install failed: {stderr}")
        return False

    print("Building UI...")
    success, stderr = run_command("npm run build", cwd=ui_dir)
    if not success:
        print(f"Warning: npm run build failed: {stderr}")
        return False

    print("UI build completed successfully")
    return True


def main():
    print("Maestro build script starting...")

    if not check_node_available():
        print("Warning: Node.js/npm not available, UI will not be built")
        return 0

    if build_ui():
        print("Build completed successfully")
    else:
        print("Build completed with warnings")

    return 0


if __name__ == "__main__":
    sys.exit(main())
