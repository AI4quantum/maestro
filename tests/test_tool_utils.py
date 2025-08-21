#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import unittest
from unittest import TestCase
from maestro.tool_utils import find_mcp_service


class Test_tool_utils(TestCase):
    mcp_server_list = "test_mcp_server_list.json"

    def setUp(self):
        os.environ["MCP_SERVER_LIST"] = self.mcp_server_list
        with open(self.mcp_server_list, "w") as f:
            contents = """
[
    {
        "name": "slack",
        "url": "http://localhost:30055",
        "transport": "streamable-http",
        "access_token": null
    },
    {
        "name": "weather",
        "url": "http://localhost:8000",
        "transport": "streamable-http",
        "access_token": null
    }
]
            """
            f.write(contents)

    def tearDown(self):
        os.remove(self.mcp_server_list)

    def test_(self):
        name, url, transport, external, token = find_mcp_service("weather")
        assert name == "weather"
        assert url == "http://localhost:8000"
        assert transport == "streamable-http"
        assert external == "http://localhost:8000"
        assert not token

        name, url, transport, external, token = find_mcp_service("none")
        assert not name
        assert not url
        assert not transport
        assert not external
        assert not token


if __name__ == "__main__":
    unittest.main()
