import json
from pathlib import Path
from maestro.file_logger import FileLogger

def _find_log_file_by_workflow_id(directory: Path, workflow_id: str):
    return next((f for f in directory.glob("*.jsonl") if workflow_id in f.name), None)

def _read_json_lines(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines()]

def test_log_file_contents(tmp_path):
    logger = FileLogger(log_dir=tmp_path)
    workflow_id = logger.generate_workflow_id()

    logger.log_workflow_run(
        workflow_id=workflow_id,
        workflow_name="test_workflow",
        prompt="test prompt",
        output="test output",
        models_used=["model-A", "model-B"],
        status="success"
    )

    log_file = _find_log_file_by_workflow_id(tmp_path, workflow_id)
    assert log_file is not None

    logs = _read_json_lines(log_file)
    summary_logs = [log for log in logs if log["log_type"] == "workflow_summary"]
    assert len(summary_logs) == 1

    log = summary_logs[0]
    assert log["workflow_name"] == "test_workflow"
    assert log["prompt"] == "test prompt"
    assert log["output"] == "test output"
    assert "model-A" in log["models_used"]
    assert "model-B" in log["models_used"]
    assert log["status"] == "success"

def test_log_with_empty_output(tmp_path):
    logger = FileLogger(log_dir=tmp_path)
    workflow_id = logger.generate_workflow_id()

    logger.log_workflow_run(
        workflow_id=workflow_id,
        workflow_name="empty_output_workflow",
        prompt="testing empty output",
        output="",
        models_used=[],
        status="success"
    )

    log_file = _find_log_file_by_workflow_id(tmp_path, workflow_id)
    assert log_file is not None

    logs = _read_json_lines(log_file)
    summary_logs = [log for log in logs if log["log_type"] == "workflow_summary"]
    assert len(summary_logs) == 1

    log = summary_logs[0]
    assert log["workflow_name"] == "empty_output_workflow"
    assert log["prompt"] == "testing empty output"
    assert log["output"] == ""
    assert log["models_used"] == []
    assert log["status"] == "success"

def test_log_agent_response(tmp_path):
    logger = FileLogger(log_dir=tmp_path)
    workflow_id = logger.generate_workflow_id()

    logger.log_workflow_run(
        workflow_id=workflow_id,
        workflow_name="agent_response_workflow",
        prompt="math test",
        output="4",
        models_used=["test-model"],
        status="success"
    )

    logger.log_agent_response(
        workflow_id=workflow_id,
        step_index=0,
        agent_name="example_agent",
        model="test-model",
        input_text="What is 2 + 2?",
        response_text="4",
        tool_used="calculator",
        duration_ms=123
    )

    log_file = _find_log_file_by_workflow_id(tmp_path, workflow_id)
    assert log_file is not None
    logs = _read_json_lines(log_file)
    summary_logs = [log for log in logs if log["log_type"] == "workflow_summary"]
    assert len(summary_logs) == 1
    assert summary_logs[0]["workflow_name"] == "agent_response_workflow"

    agent_logs = [log for log in logs if log["log_type"] == "agent_response"]
    assert len(agent_logs) == 1
    log = agent_logs[0]
    assert log["agent_name"] == "example_agent"
    assert log["model"] == "test-model"
    assert log["input"] == "What is 2 + 2?"
    assert log["response"] == "4"
    assert log["tool_used"] == "calculator"
    assert log["duration_ms"] == 123
