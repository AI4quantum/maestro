# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""FastAPI server module for serving Maestro agents via HTTP endpoints."""

import json
import os
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from maestro.workflow import create_agents, Workflow
from maestro.agents.agent import restore_agent
from maestro.cli.common import parse_yaml, Console

from dotenv import load_dotenv

load_dotenv()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    prompt: str
    stream: bool = False


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    agent_name: str
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health endpoint."""

    status: str
    agent_name: Optional[str] = None
    timestamp: str


class FastAPIServer:
    """FastAPI server for serving Maestro agents."""

    def __init__(self, agents_file: str, agent_name: Optional[str] = None):
        """Initialize the FastAPI server.

        Args:
            agents_file: Path to the agents YAML file
            agent_name: Specific agent name to serve (if multiple agents in file)
        """
        self.agents_file = agents_file
        self.agent_name = agent_name
        self.agents = {}
        self.app = FastAPI(
            title="Maestro Agent Server",
            description="HTTP API for serving Maestro agents",
            version="1.0.0",
        )
        allowed_origins = [
            x.strip() for x in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        ]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET", "POST"],
        )
        self._setup_routes()
        self._load_agents()

    def _setup_routes(self):
        """Set up FastAPI routes."""

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            """Chat with the agent."""
            try:
                if not self.agents:
                    raise HTTPException(status_code=500, detail="No agents loaded")

                # Select the agent to use
                agent = None
                if self.agent_name and self.agent_name in self.agents:
                    agent = self.agents[self.agent_name]
                elif len(self.agents) == 1:
                    # Use the first (and only) agent
                    agent = list(self.agents.values())[0]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent '{self.agent_name}' not found. Available agents: {list(self.agents.keys())}",
                    )

                if request.stream:
                    return StreamingResponse(
                        self._stream_response(agent, request.prompt),
                        media_type="text/plain",
                    )
                else:
                    response = await agent.run(request.prompt)
                    return ChatResponse(
                        response=response,
                        agent_name=agent.agent_name,
                        timestamp=datetime.utcnow().isoformat() + "Z",
                    )

            except Exception as e:
                Console.error(f"Error in chat endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            """Health check endpoint."""
            return HealthResponse(
                status="healthy",
                agent_name=self.agent_name
                or (list(self.agents.keys())[0] if self.agents else None),
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        @self.app.get("/agents")
        async def list_agents():
            """List available agents."""
            return {
                "agents": list(self.agents.keys()),
                "current_agent": self.agent_name
                or (list(self.agents.keys())[0] if self.agents else None),
            }

    def _load_agents(self):
        """Load agents from the agents file."""
        try:
            agents_yaml = parse_yaml(self.agents_file)
            create_agents(agents_yaml)

            # Load agents into memory
            for agent_def in agents_yaml:
                agent_name = agent_def["metadata"]["name"]
                if not self.agent_name or agent_name == self.agent_name:
                    restored = restore_agent(agent_name)

                    # Handle case where restore_agent returns a tuple
                    if isinstance(restored, tuple):
                        agent = restored[0]  # Extract the agent object from the tuple
                    else:
                        agent = restored

                    self.agents[agent_name] = agent

            if not self.agents:
                raise RuntimeError(f"No agents found in {self.agents_file}")

            Console.ok(
                f"Loaded {len(self.agents)} agent(s): {list(self.agents.keys())}"
            )

        except Exception as e:
            Console.error(f"Failed to load agents: {str(e)}")
            raise

    async def _stream_response(self, agent, prompt: str):
        """Stream response from agent."""
        try:
            # For now, we'll get the full response and yield it
            # In the future, we could implement true streaming if agents support it
            response = await agent.run(prompt)
            yield f"data: {json.dumps({'response': response, 'agent_name': agent.agent_name})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the FastAPI server."""
        Console.print(f"Starting Maestro agent server on {host}:{port}")
        Console.print(f"API documentation available at: http://{host}:{port}/docs")
        Console.print(f"Health check available at: http://{host}:{port}/health")

        uvicorn.run(self.app, host=host, port=port, log_level="info")


def serve_agent(
    agents_file: str,
    agent_name: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
):
    """Serve an agent via FastAPI.

    Args:
        agents_file: Path to the agents YAML file
        agent_name: Specific agent name to serve
        host: Host to bind to
        port: Port to serve on
    """
    server = FastAPIServer(agents_file, agent_name)
    server.run(host, port)


class WorkflowChatRequest(BaseModel):
    """Request model for chat endpoint."""

    prompt: str


class WorkflowChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    workflow_name: str
    timestamp: str


class WorkflowHealthResponse(BaseModel):
    """Response model for health endpoint."""

    status: str
    workflow_name: str
    timestamp: str


class FastAPIWorkflowServer:
    """FastAPI server for serving Maestro workflow."""

    def __init__(self, agents_file: str, workflow_file: str):
        """Initialize the FastAPI server.

        Args:
            agents_file: Path to the agents YAML file
            workflow_file: Path to the workflow YAML file
        """
        self.agents_file = agents_file
        self.workflow_file = workflow_file
        self.workflow = {}
        self.app = FastAPI(
            title="Maestro Workflow Server",
            description="HTTP API for serving Maestro workflow",
            version="1.0.0",
        )
        allowed_origins = [
            x.strip() for x in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        ]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET", "POST"],
        )
        self._setup_routes()
        self._load_workflow()
        self.workflow_name = self.workflow.workflow["metadata"]["name"]

    def _setup_routes(self):
        """Set up FastAPI routes."""

        @self.app.post("/chat", response_model=WorkflowChatResponse)
        async def chat(request: WorkflowChatRequest):
            """Chat with the workflow."""
            try:
                if not self.workflow:
                    raise HTTPException(status_code=500, detail="No workflow loaded")

                response = await self.workflow.run(request.prompt)
                try:
                    str_response = json.dumps(response)
                except Exception:
                    str_response = str(response)
                return WorkflowChatResponse(
                    response=str_response,
                    workflow_name=self.workflow_name,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                )

            except Exception as e:
                Console.error(f"Error in chat endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health", response_model=WorkflowHealthResponse)
        async def health():
            """Health check endpoint."""
            return WorkflowHealthResponse(
                status="healthy",
                workflow_name=self.workflow_name,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

    def _load_workflow(self):
        """Load agents from the agents file."""
        try:
            agents_yaml = parse_yaml(self.agents_file)
            workflow_yaml = parse_yaml(self.workflow_file)
            self.workflow = Workflow(agents_yaml, workflow_yaml[0])
            Console.ok("Workflow loaded")
        except Exception as e:
            Console.error(f"Failed to load workflow: {str(e)}")
            raise

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the FastAPI server."""
        Console.print(f"Starting Maestro workflow server on {host}:{port}")
        Console.print(f"API documentation available at: http://{host}:{port}/docs")
        Console.print(f"Health check available at: http://{host}:{port}/health")

        uvicorn.run(self.app, host=host, port=port, log_level="info")


def serve_workflow(
    agents_file: str, workflow_file: str, host: str = "127.0.0.1", port: int = 8000
):
    """Serve a workflow via FastAPI.

    Args:
        agents_file: Path to the agents YAML file
        workflow_file: Path to the workflow YAML file
        host: Host to bind to
        port: Port to serve on
    """
    server = FastAPIWorkflowServer(agents_file, workflow_file)
    server.run(host, port)
