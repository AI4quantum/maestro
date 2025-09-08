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

    # Start FastAPI workflow server
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

    # UI mode: dev (Vite) or prod (Docker)
    mode = os.getenv("MAESTRO_UI_MODE", "dev").lower()
    ui_proc = None
    # Project root: three levels up from this file (src/maestro/cli/node_deploy.py -> project root)
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    if mode == "prod":
        ui_cwd = os.path.join(project_root, "web", "maestro-ui")
        image_tag = os.getenv("MAESTRO_UI_IMAGE", "maestro-ui:latest")
        host_port = os.getenv("MAESTRO_UI_PORT", "8080")
        subprocess.check_call(["docker", "build", "-t", image_tag, "."], cwd=ui_cwd)
        ui_proc = subprocess.Popen(
            [
                "docker",
                "run",
                "--rm",
                "-p",
                f"{host_port}:80",
                image_tag,
            ]
        )
        print(f"[INFO] UI (prod) running at http://localhost:{host_port}")
    else:
        ui_cwd = os.path.join(project_root, "web", "maestro-ui")
        npm_cmd = ["npm", "run", "dev"]
        ui_env = os.environ.copy()
        ui_env.setdefault("PORT", "5173")
        ui_proc = subprocess.Popen(npm_cmd, cwd=ui_cwd, env=ui_env)
        print("[INFO] UI (dev) running at http://localhost:5173")

    try:
        api_proc.wait()
    finally:
        if ui_proc is not None:
            try:
                ui_proc.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
