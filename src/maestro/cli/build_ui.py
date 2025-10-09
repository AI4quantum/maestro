#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def main():
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        build_script = project_root / "build.py"

        if not build_script.exists():
            print("❌ Error: build.py not found")
            sys.exit(1)

        print("🔨 Building UI assets...")
        result = subprocess.run([sys.executable, str(build_script)])

        if result.returncode == 0:
            print("✅ UI build completed successfully")
        else:
            print("⚠️ UI build completed with warnings")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: UI build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
