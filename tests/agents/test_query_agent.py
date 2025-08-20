#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from unittest.mock import patch

from fastmcp.client.client import CallToolResult
from mcp.types import TextContent

from maestro.agents.query_agent import QueryAgent

db_data = [
    {
        "id": 0,
        "url": "doc1.md",
        "text": "TestDoc1",
        "metadata": {},
    },
    {
        "id": 1,
        "url": "doc2.md",
        "text": "DocTest2",
        "metadata": {},
    },
    {
        "id": 2,
        "url": "doc3.md",
        "text": "3rdDoc",
        "metadata": {},
    },
]

agent_def = {
    "metadata": {
        "name": "test-query-agent",
        "labels": {
            "custom_agent": "query_agent",
        },
        "query_input": {
            "db_name": "testDB",
            "collection_name": "MaestroDoc",
            "limit": 10,
        },
    },
    "spec": {
        "framework": "custom",
        "description": "desc",
    },
}


class MockClient:
    def __init__(self, url, timeout):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def call_tool(self, tool, params):
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(db_data))],
            data=db_data,
            structured_content=None,
        )


@patch("maestro.agents.query_agent.Client", MockClient)
def test_query_agent():
    agent = QueryAgent(agent_def)
    result = asyncio.run(agent.run("test prompt"))
    assert "TestDoc1" in result
    assert "DocTest2" in result
    assert "3rdDoc" in result
    assert "test prompt" not in result


@patch("maestro.agents.query_agent.Client", MockClient)
def test_query_agent_template_output():
    agent_def_with_template = agent_def.copy()
    agent_def_with_template["spec"]["output"] = """
{{result}}

---

Given the context above, your knowledge, answer the question as best as possible. Be concise.

Question: {{prompt}}
"""
    agent = QueryAgent(agent_def_with_template)
    result = asyncio.run(agent.run("test prompt"))
    assert "TestDoc1" in result
    assert "DocTest2" in result
    assert "3rdDoc" in result
    assert "test prompt" in result
