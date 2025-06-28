from pathlib import Path
from maestro.file_logger import FileLogger

def _find_log_file_by_workflow_id(directory: Path, workflow_id: str):
    return next((f for f in directory.glob("*.log") if workflow_id in f.name), None)

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
    assert log_file is not None, "Log file was not created"
    contents = log_file.read_text()

    assert "test_workflow" in contents
    assert "test prompt" in contents
    assert "test output" in contents
    assert "model-A" in contents
    assert "model-B" in contents
    assert "success" in contents

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
    contents = log_file.read_text()

    assert "empty_output_workflow" in contents
    assert "Output        : \n" in contents
    assert "testing empty output" in contents
    assert "success" in contents

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
    contents = log_file.read_text()

    assert "--- Agent Response ---" in contents
    assert "example_agent" in contents
    assert "test-model" in contents
    assert "What is 2 + 2?" in contents
    assert "4" in contents
    assert "calculator" in contents
    assert "Duration (ms) : 123" in contents

    assert "agent_response_workflow" in contents
    assert "math test" in contents
    assert "Output        : 4" in contents
    assert "success" in contents
