import sqlite3
import uuid
from datetime import datetime, UTC
import json

DB_FILE = "maestro_logs.db"

def ensure_db_initialized():
    """Ensure the database and required tables exist."""
    conn = sqlite3.connect(DB_FILE)
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
    conn.close()

def generate_workflow_id():
    """Generate a unique workflow ID."""
    return uuid.uuid4().hex

def log_workflow_run(workflow_id, workflow_name, prompt, output, models_used, status):
    """Insert a record into the workflow_runs table."""
    ensure_db_initialized()

    conn = sqlite3.connect(DB_FILE)
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
        json.dumps(models_used),  # stored as JSON string
        status
    ))

    conn.commit()
    conn.close()

def log_agent_response(workflow_id, step_index, agent_name, model, input_text, response_text, tool_used=None, duration_ms=None):
    """Insert a record into the agent_responses table."""
    ensure_db_initialized()

    conn = sqlite3.connect(DB_FILE)
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
    conn.close()
