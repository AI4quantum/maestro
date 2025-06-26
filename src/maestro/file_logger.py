import uuid
from datetime import datetime, UTC
from pathlib import Path

class FileLogger:
    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir) if log_dir else Path.cwd()
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def generate_workflow_id(self):
        return uuid.uuid4().hex

    def log_workflow_run(self, workflow_id, workflow_name, prompt, output, models_used, status):
        log_path = self.log_dir / f"maestro_run_{workflow_id}.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Timestamp     : {datetime.now(UTC).isoformat()}\n")
            f.write(f"Workflow Name : {workflow_name}\n")
            f.write(f"Status        : {status}\n")
            f.write(f"Prompt        : {prompt}\n")
            f.write(f"Output        : {output}\n")
            f.write(f"Models Used   : {models_used}\n")

    def log_agent_response(self, agent_name, input_text, response_text):
        # extend this later
        pass
