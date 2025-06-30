import uuid
from datetime import datetime, UTC
from pathlib import Path
import os

home_path = Path.home()
if os.access(home_path, os.W_OK):
    DEFAULT_LOG_DIR = home_path / ".maestro" / "logs"
else:
    DEFAULT_LOG_DIR = Path("./logs")

class FileLogger:
    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def generate_workflow_id(self):
        return uuid.uuid4().hex

    def log_workflow_run(self, workflow_id, workflow_name, prompt, output, models_used, status):
        log_path = self.log_dir / f"maestro_run_{workflow_id}.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"Timestamp     : {datetime.now(UTC).isoformat()}\n")
            f.write(f"Workflow Name : {workflow_name}\n")
            f.write(f"Status        : {status}\n")
            f.write(f"Prompt        : {prompt}\n")
            f.write(f"Output        : {output}\n")
            f.write(f"Models Used   : {models_used}\n")

    def log_agent_response(self, workflow_id, step_index, agent_name, model, input_text, response_text, tool_used=None, duration_ms=None):
        log_path = self.log_dir / f"maestro_run_{workflow_id}.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n--- Agent Response ---\n")
            f.write(f"Step Index    : {step_index}\n")
            f.write(f"Agent Name    : {agent_name}\n")
            f.write(f"Model         : {model}\n")
            f.write(f"Input         : {input_text}\n")
            f.write(f"Response      : {response_text}\n")
            if tool_used:
                f.write(f"Tool Used     : {tool_used}\n")
            if duration_ms is not None:
                f.write(f"Duration (ms) : {duration_ms}\n")
