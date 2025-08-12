# SPDX-License-Identifier: Apache-2.0

import os
import shlex
from contextlib import AsyncExitStack
from typing import List, Optional, Union, Tuple, Callable
from maestro.tool_utils import find_mcp_service

from agents.mcp import MCPServerSse, MCPServerStdio, MCPServerStreamableHttp

# MCP Servers can be of either type
MCPServerInstance = Union[MCPServerSse, MCPServerStdio, MCPServerStreamableHttp]


# Uses openai agent specific types - though concepts are similar across implementations
# TODO: can this be refactored so we can support more types of agents
async def setup_mcp_servers(
    print_func: Callable = print, agent_name: str = "GenericAgent"
) -> Tuple[List[MCPServerInstance], AsyncExitStack]:
    """
    Parses MAESTRO_MCP_ENDPOINTS, connects to MCP servers (SSE/Stdio),
    and returns a list of active server instances and an AsyncExitStack
    to manage their lifecycles.

    Args:
        print_func (Callable): Function used for logging output.
        agent_name (str): Name of the agent requesting setup (for logging).

    Returns:
        Tuple[List[MCPServerInstance], AsyncExitStack]:
            - A list of successfully connected MCPServerSse/MCPServerStdio instances.
            - An AsyncExitStack managing the context of these servers.
            The caller MUST manage this stack (e.g., using 'async with').
    """
    active_servers: List[MCPServerInstance] = []
    stack = AsyncExitStack()

    # List of mcp servers, comma separated. either executable+args or a URL
    mcp_endpoints_str = os.getenv("MAESTRO_MCP_ENDPOINTS", "")
    endpoint_definitions = [
        ep.strip() for ep in mcp_endpoints_str.split(",") if ep.strip()
    ]

    if not endpoint_definitions:
        print_func(
            f"DEBUG [{agent_name} - MCP Setup]: No MCP endpoints configured in MAESTRO_MCP_ENDPOINTS."
        )
        return active_servers, stack

    print_func(
        f"DEBUG [{agent_name} - MCP Setup]: Attempting MCP connections: {endpoint_definitions}..."
    )

    for i, endpoint_def in enumerate(endpoint_definitions):
        server_name_base = f"{agent_name}_MCP_Server_{i + 1}"
        server: Optional[MCPServerInstance] = None
        server_type = "Unknown"
        server_id = endpoint_def

        try:
            if endpoint_def.startswith(("http://", "https://")):
                # Remote SSE Server - http
                server_type = "SSE"
                server = MCPServerSse(
                    name=f"{server_name_base}_SSE", params={"url": endpoint_def}
                )
            else:
                # Local Stdio Server (local executable to run, with args)
                server_type = "Stdio"
                parts = shlex.split(endpoint_def)
                if not parts:
                    print_func(
                        f"WARN [{agent_name} - MCP Setup]: Skipping invalid empty MCP command: '{endpoint_def}'"
                    )
                    continue
                command, args = parts[0], parts[1:]
                current_env = os.environ.copy()
                server = MCPServerStdio(
                    name=f"{server_name_base}_Stdio",
                    params={"command": command, "args": args, "env": current_env},
                    cache_tools_list=True,
                )
                server_id = endpoint_def

            await stack.enter_async_context(server)
            active_servers.append(server)
            print_func(
                f"INFO [{agent_name} - MCP Setup]: MCP Server ({server_type}) connected: {server.name} ({server_id})"
            )

        except ConnectionRefusedError:
            print_func(
                f"WARN [{agent_name} - MCP Setup]: MCP Server ({server_type}) connection refused: {server_name_base} ({server_id})"
            )
        except FileNotFoundError:
            print_func(
                f"WARN [{agent_name} - MCP Setup]: MCP Server ({server_type}) command not found: {server_name_base} ({server_id})"
            )
        except Exception as conn_err:
            print_func(
                f"WARN [{agent_name} - MCP Setup]: Failed MCP connection {server_name_base} ({server_id}): {conn_err}"
            )

    if not active_servers and endpoint_definitions:
        print_func(
            f"WARN [{agent_name} - MCP Setup]: Failed to connect to any configured MCP servers."
        )
    elif active_servers:
        print_func(
            f"INFO [{agent_name} - MCP Setup]: Successfully connected to {len(active_servers)} MCP server(s)."
        )

    return active_servers, stack


async def get_mcp_servers(tools, stack):
    mcp_servers = []
    if tools:
        for tool_name in tools:
            name, service_url, transport, external_url, access_token = find_mcp_service(
                tool_name
            )
            if name:
                url = external_url
                if os.getenv("KUBERNETES_SERVICE_HOST") and os.getenv(
                    "KUBERNETES_SERVICE_PORT"
                ):
                    url = service_url
                if os.getenv("KUBERNETES_POD") == "true":
                    url = service_url
                if os.path.exists(
                    "/var/run/secrets/kubernetes.io/serviceaccount/token"
                ):
                    url = service_url

                if url.endswith("/"):
                    url = url[:-1]
                if url.endswith("/mcp"):
                    url = url[: -len("/mcp")]
                elif url.endswith("/sse"):
                    url = url[: -len("/sse")]

                headers = None
                if access_token:
                    headers = {"Authorization": f"Bearer {access_token}"}
                if transport == "sse" or transport == "stdio":
                    server = MCPServerSse(
                        name=tool_name, params={"url": url + "/sse", "headers": headers}
                    )
                else:
                    server = MCPServerStreamableHttp(
                        name=tool_name, params={"url": url + "/mcp", "headers": headers}
                    )
                await server.connect()
                mcp_servers.append(server)
                await stack.enter_async_context(server)
    return mcp_servers
