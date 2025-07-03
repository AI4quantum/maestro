"""
Maestro Builder API
A FastAPI application to support the Maestro Builder frontend application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import yaml
from datetime import datetime
import uuid
import os
from pathlib import Path

# Import our AI agent and database
from ai_agent import MaestroBuilderAgent
from database import Database

# Initialize FastAPI app
app = FastAPI(
    title="Maestro Builder API",
    description="API for the Maestro Builder application",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI agent and database
ai_agent = MaestroBuilderAgent()
db = Database()

# Data models
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Maestro Builder API", "version": "1.0.0"}

@app.post("/api/chat_builder_agent", response_model=ChatResponse)
async def chat_builder_agent(message: ChatMessage, chat_id: Optional[str] = None):
    """
    Chat with the Maestro Builder agent to create YAML configurations.
    
    Args:
        message: The chat message from the user
        chat_id: Optional chat session ID for continuing conversations
    
    Returns:
        ChatResponse with AI response and updated YAML files
    """
    try:
        # Create or get existing chat session
        if not chat_id:
            chat_id = db.create_chat_session()
        else:
            # Verify chat session exists, create if not
            session = db.get_chat_session(chat_id)
            if not session:
                chat_id = db.create_chat_session(chat_id)
        
        # Add user message to database
        db.add_message(chat_id, "user", message.content)
        
        # Get current YAML files for context
        current_yamls = db.get_yaml_files(chat_id)
        
        # If no YAML files exist, initialize with defaults
        if not current_yamls:
            current_yamls = {
                "agents.yaml": "# Agents configuration will be generated here\nagents:\n  # Your agents will appear here",
                "workflow.yaml": "# Workflow configuration will be generated here\nworkflow:\n  # Your workflow will appear here"
            }
        
        # Generate AI response using the MaestroBuilderAgent
        ai_response = ai_agent.generate_response(message.content, current_yamls)
        
        # Add AI response to database
        db.add_message(chat_id, "assistant", ai_response["response"])
        
        # Update YAML files in database
        db.update_yaml_files(chat_id, ai_response["yaml_files"])
        
        return ChatResponse(
            response=ai_response["response"],
            yaml_files=[{"name": name, "content": content} for name, content in ai_response["yaml_files"].items()],
            chat_id=chat_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/api/get_yamls/{chat_id}", response_model=List[YamlFile])
async def get_yamls(chat_id: str):
    """
    Get the YAML files for a specific chat session.
    
    Args:
        chat_id: The chat session ID
    
    Returns:
        List of YAML files with their content
    """
    try:
        yaml_files = db.get_yaml_files(chat_id)
        
        if not yaml_files:
            raise HTTPException(status_code=404, detail="Chat session not found or no YAML files")
        
        result = []
        for name, content in yaml_files.items():
            result.append(YamlFile(name=name, content=content))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving YAML files: {str(e)}")

@app.get("/api/chat_history", response_model=List[ChatHistory])
async def get_chat_history():
    """
    Get the history of all chat conversations.
    
    Returns:
        List of chat history entries
    """
    try:
        sessions = db.get_all_chat_sessions()
        history = []
        
        for session in sessions:
            # Get the last message for each session
            messages = db.get_messages(session["id"], limit=1)
            last_message = messages[-1]["content"] if messages else ""
            
            history.append(ChatHistory(
                id=session["id"],
                name=session["name"],
                created_at=datetime.fromisoformat(session["created_at"]),
                last_message=last_message,
                message_count=session["message_count"]
            ))
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@app.get("/api/chat_session/{chat_id}", response_model=ChatSession)
async def get_chat_session(chat_id: str):
    """
    Get a complete chat session including messages and YAML files.
    
    Args:
        chat_id: The chat session ID
    
    Returns:
        Complete chat session data
    """
    try:
        session = db.get_chat_session(chat_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get messages
        messages = db.get_messages(chat_id)
        
        # Get YAML files
        yaml_files = db.get_yaml_files(chat_id)
        
        return ChatSession(
            id=session["id"],
            name=session["name"],
            created_at=datetime.fromisoformat(session["created_at"]),
            updated_at=datetime.fromisoformat(session["updated_at"]),
            message_count=session["message_count"],
            messages=messages,
            yaml_files=yaml_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat session: {str(e)}")

@app.post("/api/chat_sessions")
async def create_chat_session(name: Optional[str] = None):
    """
    Create a new chat session.
    
    Args:
        name: Optional name for the chat session
    
    Returns:
        New chat session ID
    """
    try:
        chat_id = db.create_chat_session(name=name)
        return {"chat_id": chat_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

@app.delete("/api/delete_all_chats")
async def delete_all_chat_sessions():
    """
    Delete all chat sessions and all associated data.
    
    Returns:
        Success message
    """
    try:
        success = db.delete_all_chat_sessions()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete all chat sessions")
        
        return {"message": "All chat sessions deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting all chat sessions: {str(e)}")

@app.delete("/api/chat_sessions/{chat_id}")
async def delete_chat_session(chat_id: str):
    """
    Delete a chat session and all associated data.
    
    Args:
        chat_id: The chat session ID to delete
    
    Returns:
        Success message
    """
    try:
        success = db.delete_chat_session(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"message": "Chat session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat session: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        sessions = db.get_all_chat_sessions()
        return {
            "status": "healthy",
            "database": "connected",
            "sessions_count": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 