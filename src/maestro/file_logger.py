# maestro/file_logger.py

import uuid
import os
import json
from datetime import datetime, UTC
from pathlib import Path

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

    def _write_json_line(self, log_path, data):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def log_agent_response(
        self,
        workflow_id,
        step_index,
        agent_name,
        model,
        input_text,
        response_text,
        tool_used=None,
        duration_ms=None
    ):
        log_path = self.log_dir / f"maestro_run_{workflow_id}.jsonl"
        data = {
            "log_type": "agent_response",
            "timestamp": datetime.now(UTC).isoformat(),
            "workflow_id": workflow_id,
            "step_index": step_index,
            "agent_name": agent_name,
            "model": model,
            "input": input_text,
            "response": response_text,
            "tool_used": tool_used,
            "duration_ms": duration_ms
        }
        self._write_json_line(log_path, data)

    def log_workflow_run(
        self,
        workflow_id,
        workflow_name,
        prompt,
        output,
        models_used,
        status
    ):
        log_path = self.log_dir / f"maestro_run_{workflow_id}.jsonl"
        data = {
            "log_type": "workflow_summary",
            "timestamp": datetime.now(UTC).isoformat(),
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "status": status,
            "prompt": prompt,
            "output": output,
            "models_used": models_used
        }
        self._write_json_line(log_path, data)
