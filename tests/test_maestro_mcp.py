import asyncio
import pytest
import json
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from maestro.cli.common import parse_yaml


async def run_workflow(session):
    print("run_workflow\n")
    agent_defs = parse_yaml("tests/yamls/agents/openai_agent.yaml")
    agent_def_strings = []
    for agent_def in agent_defs:
        agent_def_strings.append(json.dumps(agent_def))
    workflow_defs = parse_yaml("tests/yamls/workflows/openai_workflow.yaml")
    workflow_def_string = json.dumps(workflow_defs[0])
    result = await session.call_tool(
        "run_workflow", {"agents": agent_def_strings, "workflow": workflow_def_string}
    )
    print(f"response: {result}")
    assert not result.isError


async def create_agents(session):
    print("create_agents\n")
    agent_defs = parse_yaml("tests/yamls/agents/openai_agent.yaml")
    agent_def_strings = []
    for agent_def in agent_defs:
        agent_def_strings.append(json.dumps(agent_def))
    result = await session.call_tool("create_agents", {"agents": agent_def_strings})
    print(f"response: {result}")
    assert not result.isError


async def serve_agent(session):
    print("serve_agent\n")
    with open("tests/yamls/agents/openai_agent.yaml", "r", encoding="utf-8") as file:
        agent = file.read()
        print(agent)
    result = await session.call_tool("serve_agent", {"agent": agent, "port": 30055})
    print(f"response: {result}")
    assert not result.isError


async def serve_workflow(session):
    print("serve_workflow\n")
    with open("tests/yamls/agents/openai_agent.yaml", "r", encoding="utf-8") as file:
        agent = file.read()
    with open(
        "tests/yamls/workflows/openai_workflow.yaml", "r", encoding="utf-8"
    ) as file:
        workflow = file.read()
    result = await session.call_tool(
        "serve_workflow", {"agents": agent, "workflow": workflow, "port": 30056}
    )
    print(f"response: {result}")
    assert not result.isError


async def serve_container_agent(session):
    print("serve_container_agent\n")
    result = await session.call_tool(
        "serve_container_agent",
        {"image_url": "localhost/container-agent:latest", "app_name": "test_app"},
    )
    print(f"response: {result}")
    assert not result.isError


async def deploy_workflow(session):
    print("deploy_workflow\n")
    with open("tests/yamls/agents/openai_agent.yaml", "r", encoding="utf-8") as file:
        agent = file.read()
    with open(
        "tests/yamls/workflows/openai_workflow.yaml", "r", encoding="utf-8"
    ) as file:
        workflow = file.read()
    result = await session.call_tool(
        "deploy_workflow",
        {"agents": agent, "workflow": workflow, "target": "docker", "env": ""},
    )
    print(f"docker response: {result}")
    assert not result.isError
    result = await session.call_tool(
        "deploy_workflow",
        {"agents": agent, "workflow": workflow, "target": "kubernetes", "env": ""},
    )
    print(f"kubernetes response: {result}")
    assert not result.isError
    result = await session.call_tool(
        "deploy_workflow",
        {"agents": agent, "workflow": workflow, "target": "streamlit", "env": ""},
    )
    print(f"streamlit response: {result}")
    assert not result.isError


@pytest.mark.skipif(
    os.getenv("DEPLOY_KUBERNETES_TEST") == "1", reason="No kubernetes skipped"
)
@pytest.mark.asyncio
async def test():
    BASE_URL = "http://localhost:8000"
    STREAM_URL = f"{BASE_URL}/mcp"

    async with streamablehttp_client(STREAM_URL) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            await run_workflow(session)
            await create_agents(session)
            await serve_agent(session)
            await serve_workflow(session)
            await serve_container_agent(session)
            await deploy_workflow(session)


if __name__ == "__main__":
    asyncio.run(test())
