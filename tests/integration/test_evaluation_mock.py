#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
import yaml

from maestro.workflow import Workflow


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    return docs[0] if docs else None


def test_mock_evaluation_runs_without_api_key(monkeypatch):
    monkeypatch.setenv("MAESTRO_AUTO_EVALUATION", "true")
    monkeypatch.delenv("WATSONX_APIKEY", raising=False)

    agents_yaml_path = os.path.join(
        os.path.dirname(__file__), "..", "yamls", "agents", "evaluation_test_agent.yaml"
    )
    workflow_yaml_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "yamls",
        "workflows",
        "evaluation_test_workflow.yaml",
    )

    agents_def = _load_yaml(os.path.abspath(agents_yaml_path))
    workflow_def = _load_yaml(os.path.abspath(workflow_yaml_path))

    assert agents_def is not None and isinstance(agents_def, dict)
    assert workflow_def is not None and isinstance(workflow_def, dict)

    # Run the workflow entirely with mock agent; evaluation middleware should no-op gracefully
    wf = Workflow(agent_defs=[agents_def], workflow=workflow_def)
    result = asyncio.run(wf.run())

    # Validate basic successful execution shape
    assert isinstance(result, dict)
    assert "final_prompt" in result
    assert result["final_prompt"]  # non-empty output from mock agent
