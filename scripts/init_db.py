import sqlite3
import os


DB_FILE = "maestro_logs.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# workflow table
c.execute("""
CREATE TABLE IF NOT EXISTS workflow_runs (
    workflow_id TEXT PRIMARY KEY,
    timestamp TEXT,
    workflow_name TEXT,
    prompt TEXT,
    output TEXT,
    models_used TEXT,
    status TEXT,
    relevance_score REAL,
    hallucination_score REAL
)
""")

# agent table
c.execute("""
CREATE TABLE IF NOT EXISTS agent_responses (
    workflow_id TEXT,
    step_index INTEGER,
    agent_name TEXT,
    model TEXT,
    input TEXT,
    response TEXT,
    tool_used TEXT,
    duration_ms INTEGER,
    PRIMARY KEY (workflow_id, step_index),
    FOREIGN KEY (workflow_id) REFERENCES workflow_runs(workflow_id)
)
""")

conn.commit()
conn.close()
print(f"Initialized logging database: {DB_FILE}")