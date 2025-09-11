import os
import subprocess
import sys
import time
import requests


def wait_for_api_health(host="127.0.0.1", port=8000, timeout=60, check_interval=1):
    """Wait for the API server to be healthy by polling the /health endpoint.

    Args:
        host: API server host
        port: API server port
        timeout: Maximum time to wait in seconds
        check_interval: Time between health checks in seconds

    Returns:
        bool: True if API is healthy, False if timeout reached
    """
    url = f"http://{host}:{port}/health"
    start_time = time.time()

    print(f"[INFO] Waiting for API server to be ready at {url}...")

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("[INFO] API server is ready!")
                    return True
        except (requests.RequestException, ValueError):
            pass

        time.sleep(check_interval)

    print(f"[ERROR] API server failed to become ready within {timeout} seconds")
    return False


def main():
    if len(sys.argv) < 5:
        print(
            "Usage: node_deploy.py AGENTS_FILE WORKFLOW_FILE API_HOST API_PORT [UI_PORT]"
        )
        sys.exit(1)

    agents_file = sys.argv[1]
    workflow_file = sys.argv[2]
    api_host = sys.argv[3]
    api_port = int(sys.argv[4])
    api_proc = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-c",
            f"from maestro.cli.fastapi_serve import serve_workflow; serve_workflow('{agents_file}', '{workflow_file}', host='{api_host}', port={api_port})",
        ]
    )

    if not wait_for_api_health(api_host, api_port):
        print("[ERROR] Failed to start API server")
        try:
            api_proc.terminate()
        except Exception:
            pass
        sys.exit(1)

    if len(sys.argv) >= 6:
        ui_port = int(sys.argv[5])
    else:
        ui_port = int(os.getenv("MAESTRO_UI_PORT", "5173"))
    ui_proc = None
    # Project root: three levels up from this file (src/maestro/cli/node_deploy.py -> project root)
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    ui_cwd = os.path.join(project_root, "web", "maestro-ui")
    npm_cmd = ["npm", "run", "dev"]
    ui_env = os.environ.copy()
    ui_env.setdefault("PORT", str(ui_port))
    ui_proc = subprocess.Popen(npm_cmd, cwd=ui_cwd, env=ui_env)
    print(f"[INFO] API server running at http://{api_host}:{api_port}")
    print(f"[INFO] UI running at http://localhost:{ui_port}")

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
