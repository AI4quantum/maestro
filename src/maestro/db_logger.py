import sqlite3
import uuid
import json
from datetime import datetime, UTC
from threading import Lock

class DbLogger:
    _instance = None
    _lock = Lock()

    def __new__(cls, db_path="maestro_logs.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DbLogger, cls).__new__(cls)
                cls._instance._db_path = db_path
                cls._instance._ensure_initialized()
            return cls._instance

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def _ensure_initialized(self):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    workflow_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    workflow_name TEXT,
                    prompt TEXT,
                    output TEXT,
                    models_used TEXT,
                    status TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS agent_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT,
                    step_index INTEGER,
                    agent_name TEXT,
                    model TEXT,
                    input TEXT,
                    response TEXT,
                    tool_used TEXT,
                    duration_ms INTEGER
                )
            """)
            conn.commit()

    def generate_workflow_id(self):
        return uuid.uuid4().hex

    def log_workflow_run(self, workflow_id, workflow_name, prompt, output, models_used, status):
        self._insert_workflow_run(workflow_id, workflow_name, prompt, output, models_used, status)

    def log_agent_response(self, workflow_id, step_index, agent_name, model, input_text, response_text, tool_used=None, duration_ms=None):
        self._insert_agent_response(workflow_id, step_index, agent_name, model, input_text, response_text, tool_used, duration_ms)

    def _insert_workflow_run(self, workflow_id, workflow_name, prompt, output, models_used, status):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO workflow_runs (
                    workflow_id, timestamp, workflow_name, prompt, output,
                    models_used, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_id,
                datetime.now(UTC).isoformat(),
                workflow_name,
                prompt,
                output,
                json.dumps(models_used),
                status
            ))
            conn.commit()

    def _insert_agent_response(self, workflow_id, step_index, agent_name, model, input_text, response_text, tool_used=None, duration_ms=None):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO agent_responses (
                    workflow_id, step_index, agent_name, model, input,
                    response, tool_used, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_id,
                step_index,
                agent_name,
                model,
                input_text,
                response_text,
                tool_used,
                duration_ms
            ))
            conn.commit()
