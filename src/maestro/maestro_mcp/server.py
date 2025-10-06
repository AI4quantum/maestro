from fastmcp import FastMCP

import json
import os
import sys
import subprocess
import threading
import tempfile
import argparse

from maestro.workflow import Workflow, create_agents as workflow_create_agents
from maestro.cli.fastapi_serve import (
    serve_agent as __serve_agent,
    serve_workflow as __serve_workflow,
)
from maestro.cli.containered_agent import create_deployment_service
from maestro.deploy import Deploy
from maestro.mcptool import create_mcptools

# Initialize FastMCP server
mcp = FastMCP("Maestro")


@mcp.tool()
async def run_workflow(agents: list[str], workflow: str):
    """Run workflow.

    Args:
        agents: list of agent definitions
        workflow: workflow definition
    """
    agent_defs = []
    for agent in agents:
        agent_defs.append(json.loads(agent))
    workflow_def = json.loads(workflow)

    workflow = Workflow(
        agent_defs=agent_defs,
        workflow=workflow_def,
    )
    return await workflow.run()


@mcp.tool()
async def create_agents(agents: list[str]):
    """Create agents

    Args:
        agents: list of agent definitions
    """
    agent_defs = []
    for agent in agents:
        agent_defs.append(json.loads(agent))
    workflow_create_agents(agent_defs)


@mcp.tool()
async def create_tools(tools: list[str]):
    """Create tools

    Args:
        tools: list of tool definitions
    """
    tool_defs = []
    for tool in tools:
        tool_defs.append(json.loads(tool))
    create_mcptools(tool_defs)


def serve_agent_thread(agent, agent_name, host, port):
    __serve_agent(agent, agent_name=agent_name, host=host, port=port)
    os.remove(agent)


@mcp.tool()
async def serve_agent(
    agent: str, agent_name: str = None, host: str = "127.0.0.1", port: int = 8001
):
    """Serve agent

    Args:
        agent: agent definition
        agent_name: agent name in agent_definitions
        host: server IP
        port: server port
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write(agent)
        agent_def = temp_file.name

    thread_instance = threading.Thread(
        target=serve_agent_thread, args=(agent_def, agent_name, host, port)
    )
    thread_instance.start()


def serve_workflow_thread(agents, workflow, host, port):
    __serve_workflow(agents, workflow, host, port)
    os.remove(agents)
    os.remove(workflow)


@mcp.tool()
async def serve_workflow(
    agents: str, workflow: str, host: str = "127.0.0.1", port: int = 8001
):
    """Serve workflow

    Args:
        agents: list of agent definitions
        workflow: workflow definition
        host: server IP
        port: server port
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write(agents)
        agent_defs = temp_file.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write(workflow)
        workflow_def = temp_file.name

    thread_instance = threading.Thread(
        target=serve_workflow_thread, args=(agent_defs, workflow_def, host, port)
    )
    thread_instance.start()


@mcp.tool()
async def serve_container_agent(
    image_url: str,
    app_name: str,
    namespace="default",
    replicas=1,
    container_port=80,
    service_port=80,
    service_type="LoadBalancer",
    node_port=30051,
):
    """Serve container agent

    Args:
        image_url: agent container image registry URL
        app_name: app name in the cluster
    """
    create_deployment_service(
        image_url,
        app_name,
        namespace,
        replicas,
        container_port,
        service_port,
        service_type,
        node_port,
    )


@mcp.tool()
async def deploy_workflow(
    agents: str, workflow: str, target: str = "streamlit", env: str = ""
):
    """Deploy workflow

    Args:
        agents: agents yaml file contents
        workflow: workflow yaml file contents
        target: daploy target type (docker, kubernetes, or streamlit)
        env:environment variables set into container. format: list of key=value string.  Each kye=value is separated by ','
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write(agents)
        agents_yaml = temp_file.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write(workflow)
        workflow_yaml = temp_file.name

    if target == "docker":
        deploy = Deploy(agents_yaml, workflow_yaml, env)
        deploy.deploy_to_docker()
        os.remove(agents_yaml)
        os.remove(workflow_yaml)
    elif target == "kubernetes":
        deploy = Deploy(agents_yaml, workflow_yaml, env)
        deploy.deploy_to_kubernetes()
        os.remove(agents_yaml)
        os.remove(workflow_yaml)
    else:
        try:
            sys.argv = [
                "uv",
                "run",
                "streamlit",
                "run",
                "--ui.hideTopBar",
                "True",
                "--client.toolbarMode",
                "minimal",
                f"{os.path.dirname(__file__)}/../cli/streamlit_deploy.py",
                agents_yaml,
                workflow_yaml,
            ]
            subprocess.Popen(sys.argv)
        except Exception as e:
            raise RuntimeError(f"{str(e)}") from e
    return 0


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Maestro MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the FastMCP server (default: 8000)",
    )
    args = parser.parse_args()

    # Initialize and run the server with the specified port
    mcp.run(transport="streamable-http", port=args.port)
