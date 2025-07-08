# api/routes/builder.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter()

MAESTRO_SERVE_URL = "http://localhost:8001"

class BuilderInput(BaseModel):
    content: str

@router.post("/api/chat_builder_agent")
async def chat_builder_agent(input: BuilderInput):
    """
    Call the meta-agent (e.g. TaskInterpreter + AgentYAMLBuilder) to generate agents.yaml content.
    """
    try:
        # Call TaskInterpreter
        interpreter_resp = requests.post(
            f"{MAESTRO_SERVE_URL}/chat",
            json={"prompt": input.content, "agent": "TaskInterpreter"}
        )
        if interpreter_resp.status_code != 200:
            raise Exception(interpreter_resp.text)
        task_plan = interpreter_resp.json().get("response", "")

        builder_resp = requests.post(
            f"{MAESTRO_SERVE_URL}/chat",
            json={"prompt": task_plan, "agent": "AgentYAMLBuilder"}
        )
        if builder_resp.status_code != 200:
            raise Exception(builder_resp.text)
        final_yaml = builder_resp.json().get("response", "")

        return {
            "response": final_yaml,
            "yaml_files": [{"name": "agents.yaml", "content": final_yaml}]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Builder failed: {e}")

@router.post("/api/chat_builder_workflow")
async def chat_builder_workflow(input: BuilderInput):
    """
    Call the WorkflowYAMLBuilder to generate workflow.yaml content.
    """
    try:
        builder_resp = requests.post(
            f"{MAESTRO_SERVE_URL}/chat",
            json={"prompt": input.content, "agent": "WorkflowYAMLBuilder"}
        )
        if builder_resp.status_code != 200:
            raise Exception(builder_resp.text)

        workflow_yaml = builder_resp.json().get("response", "")

        return {
            "response": workflow_yaml,
            "yaml_files": [{"name": "workflow.yaml", "content": workflow_yaml}]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow Builder failed: {e}")
