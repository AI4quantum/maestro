import os
import subprocess
import sys
import time


def main():
    if len(sys.argv) < 3:
        print("Usage: node_deploy.py AGENTS_FILE WORKFLOW_FILE")
        sys.exit(1)

    agents_file = sys.argv[1]
    workflow_file = sys.argv[2]

    host = os.getenv("MAESTRO_HOST", "127.0.0.1")
    port = int(os.getenv("MAESTRO_PORT", "8000"))

    # Start FastAPI workflow server in a child process via uv
    api_proc = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-c",
            (
                "from maestro.cli.fastapi_serve import serve_workflow; "
                f"serve_workflow('{agents_file}', '{workflow_file}', host='{host}', port={port})"
            ),
        ]
    )

    # Give the API a moment to start
    time.sleep(2)

    # Start Vite dev server
    ui_cwd = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web", "maestro-ui"
    )
    npm_cmd = ["npm", "run", "dev"]
    ui_env = os.environ.copy()
    ui_env.setdefault("PORT", "5173")
    ui_proc = subprocess.Popen(npm_cmd, cwd=ui_cwd, env=ui_env)

    try:
        api_proc.wait()
    finally:
        try:
            ui_proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    main()
