"""
Maestro Builder API
A FastAPI application to support the Maestro Builder frontend application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from ai_agent import MaestroBuilderAgent
from database import Database
import uuid
import requests

# Initialize FastAPI app
app = FastAPI(
    title="Maestro Builder API",
    description="API for the Maestro Builder application",
    version="1.0.0",
)

# CORS settings for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent + database
ai_agent = MaestroBuilderAgent()
db = Database()


# ---------------------------------------
# Models
# ---------------------------------------
class ChatMessage(BaseModel):
    content: str
    role: str = "user"


class ChatResponse(BaseModel):
    response: str
    yaml_files: List[Dict[str, str]]
    chat_id: str


class ChatHistory(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_message: str
    message_count: int


class YamlFile(BaseModel):
    name: str
    content: str


class ChatSession(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    messages: List[Dict[str, Any]]
    yaml_files: Dict[str, str]


# ---------------------------------------
# Routes
# ---------------------------------------


@app.get("/")
async def root():
    return {"message": "Maestro Builder API", "version": "1.0.0"}


@app.post("/api/chat_builder_agent", response_model=ChatResponse)
async def chat_builder_agent(message: ChatMessage):
    try:
        resp = requests.post(
            "http://localhost:8000/chat",
            json={"prompt": message.content, "agent": "TaskInterpreter"},
        )
        if resp.status_code != 200:
            raise Exception(resp.text)

        full_output = resp.json().get("response", "")
        extracted_yaml = ""
        if "```yaml" in full_output:
            extracted_yaml = (
                full_output.split("```yaml", 1)[-1].split("```", 1)[0].strip()
            )
        elif "```" in full_output:
            extracted_yaml = full_output.split("```", 1)[-1].split("```", 1)[0].strip()

        return {
            "response": full_output,
            "yaml_files": [{"name": "agents.yaml", "content": extracted_yaml}],
            "chat_id": str(uuid.uuid4()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Builder Agent failed: {e}")


@app.post("/api/chat_builder_workflow", response_model=ChatResponse)
async def chat_builder_workflow(message: ChatMessage):
    try:
        payload = {
            "prompt": message.content,
            "agent": "WorkflowYAMLBuilder",
        }
        if message.chat_id:
            payload["chat_id"] = message.chat_id
        resp = requests.post("http://localhost:8000/chat", json=payload)

        if resp.status_code != 200:
            raise Exception(resp.text)

        response_json = resp.json()
        workflow_yaml = response_json.get("response", "")
        chat_id = response_json.get("chat_id")

        return {
            "response": workflow_yaml,
            "chat_id": chat_id,
            "yaml_files": [{"name": "workflow.yaml", "content": workflow_yaml}],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow Builder failed: {e}")


@app.get("/api/get_yamls/{chat_id}", response_model=List[YamlFile])
async def get_yamls(chat_id: str):
    try:
        yaml_files = db.get_yaml_files(chat_id)
        if not yaml_files:
            raise HTTPException(
                status_code=404, detail="Chat session not found or no YAML files"
            )
        return [
            YamlFile(name=name, content=content) for name, content in yaml_files.items()
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving YAML files: {str(e)}"
        )


@app.get("/api/chat_history", response_model=List[ChatHistory])
async def get_chat_history():
    try:
        sessions = db.get_all_chat_sessions()
        history = []
        for session in sessions:
            messages = db.get_messages(session["id"], limit=1)
            last_message = messages[-1]["content"] if messages else ""
            history.append(
                ChatHistory(
                    id=session["id"],
                    name=session["name"],
                    created_at=datetime.fromisoformat(session["created_at"]),
                    last_message=last_message,
                    message_count=session["message_count"],
                )
            )
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving chat history: {str(e)}"
        )


@app.get("/api/chat_session/{chat_id}", response_model=ChatSession)
async def get_chat_session(chat_id: str):
    try:
        session = db.get_chat_session(chat_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = db.get_messages(chat_id)
        yaml_files = db.get_yaml_files(chat_id)

        return ChatSession(
            id=session["id"],
            name=session["name"],
            created_at=datetime.fromisoformat(session["created_at"]),
            updated_at=datetime.fromisoformat(session["updated_at"]),
            message_count=session["message_count"],
            messages=messages,
            yaml_files=yaml_files,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving chat session: {str(e)}"
        )


@app.post("/api/chat_sessions")
async def create_chat_session(name: Optional[str] = None):
    try:
        chat_id = db.create_chat_session(name=name)
        return {"chat_id": chat_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating chat session: {str(e)}"
        )


@app.delete("/api/delete_all_chats")
async def delete_all_chat_sessions():
    try:
        success = db.delete_all_chat_sessions()
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to delete all chat sessions"
            )
        return {"message": "All chat sessions deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting all chat sessions: {str(e)}"
        )


@app.delete("/api/chat_sessions/{chat_id}")
async def delete_chat_session(chat_id: str):
    try:
        success = db.delete_chat_session(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return {"message": "Chat session deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting chat session: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    try:
        sessions = db.get_all_chat_sessions()
        return {
            "status": "healthy",
            "database": "connected",
            "sessions_count": len(sessions),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
