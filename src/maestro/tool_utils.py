#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import json
import base64
import asyncio
from kubernetes import client, config

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack

plural = "mcpservers"
singular = "mcpserver"

# Define the group, version, and kind for the custom resource
group = "toolhive.stacklok.dev"
version = "v1alpha1"
kind = "MCPServer"

remoteGroup = "maestro.ai4quantum.com"
remoteVersion = "v1alpha1"
remoteKind = "RemoteMCPServer"
remotePlural = "remotemcpservers"
remoteSingular = "remotemcpserver"


def find_mcp_service(name):
    """
    Look for the service of mcp server name if it exist, it returns the service namd, url, and transport type for the server
    """

    # Load kubeconfig file
    kube = True
    try:
        config.load_kube_config()
    except Exception:
        kube = False
    v1 = client.CoreV1Api()
    apis = client.CustomObjectsApi()
    namespace = "default"

    if kube:
        try:
            # Fetch services with the specified labels
            services = v1.list_service_for_all_namespaces(
                label_selector=f"app.kubernetes.io/instance={name},app.kubernetes.io/name=mcpserver"
            )
            for service in services.items:
                # Fetch the MCPServer CRD instance
                crd = apis.get_namespaced_custom_object(
                    group=group,
                    version=version,
                    name=name,
                    namespace=namespace,
                    plural=plural,
                )
                if crd:
                    transport = crd["spec"]["transport"]
                    external = None
                    if (
                        service.spec.type == "NodePort"
                        and service.spec.ports[0].node_port
                    ):
                        external = f"http://127.0.0.1:{service.spec.ports[0].node_port}"
                    return (
                        service.metadata.name,
                        f"http://{service.metadata.name}:{service.spec.ports[0].port}",
                        transport,
                        external,
                        None,
                    )
        except Exception:
            None

    # remote MCP server
    if kube:
        try:
            remote_crd = apis.get_namespaced_custom_object(
                group=remoteGroup,
                version=remoteVersion,
                name=name,
                namespace=namespace,
                plural=remotePlural,
            )
            if remote_crd:
                transport = remote_crd["spec"]["transport"]
                url = remote_crd["spec"]["url"]
                name = remote_crd["spec"]["name"]
                if url.endswith("/"):
                    url = url[:-1]
                if url.endswith("/mcp"):
                    url = url[: -len("/mcp")]
                elif url.endswith("/sse"):
                    url = url[: -len("/sse")]
                accessToken = None
                secretName = remote_crd["spec"].get("secretName")
                if secretName:
                    secret = v1.read_namespaced_secret(
                        name=secretName, namespace="default"
                    )
                    if secret:
                        accessToken = base64.b64decode(
                            secret.data["MCP_ACCESS_TOKEN"]
                        ).decode("utf-8")
                return (name, url, transport, url, accessToken)
        except Exception:
            None

    # local MCP server list
    # Example Json file
    # [
    #    {
    #        "name": "server1",
    #        "url": "http://server1.example.com",
    #        "transport": "streamable-http",
    #        "access_token": "abc123"
    #    },
    #    {
    #        "name": "server2",
    #        "url": "http://server2.example.com",
    #        "transport": "sse",
    #        "access_token": "def456"
    #    },
    #    {
    #        "name": "server3",
    #        "url": "http://server3.example.com",
    #        "transport": "stdio",
    #        "access_token": null
    #    }
    # ]

    json_file = os.getenv("MCP_SERVER_LIST")
    if json_file:
        with open(json_file, "r") as f:
            server_list = json.load(f)

        for server in server_list:
            if server.get("name") == name:
                return (
                    server.get("name"),
                    server.get("url"),
                    server.get("transport"),
                    server.get("url"),
                    server.get("access_token"),
                )

    return None, None, None, None, None


async def get_http_tools(url, converter, stack, accessToken):
    if accessToken:
        headers = {"Authorization": f"Bearer {accessToken}"}
        transport = await stack.enter_async_context(
            streamablehttp_client(url + "/mcp", headers=headers)
        )
    else:
        transport = await stack.enter_async_context(streamablehttp_client(url + "/mcp"))
    stdio, write, _ = transport
    session = await stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()
    tools = await session.list_tools()
    if converter:
        converted = []
        for tool in tools.tools:
            try:
                print(f"puttings session:{session}")
                converted.append(converter(session, tool))
            except Exception as e:
                print(e)
        return converted
    return tools.tools


async def get_sse_tools(url, converter, stack, accessToken):
    if accessToken:
        headers = {"Authorization": f"Bearer {accessToken}"}
        transport = await stack.enter_async_context(
            streamablehttp_client(url + "/mcp", headers=headers)
        )
    else:
        transport = await stack.enter_async_context(sse_client(url + "/sse"))
    stdio, write = transport
    session = await stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()
    tools = await session.list_tools()
    if converter:
        converted = []
        for tool in tools.tools:
            print(f"puttings ession:{session}")
            converted.append(converter(session, tool))
        return converted
    return tools.tools


async def get_mcp_tools(service_name, converter, stack):
    service, service_url, transport, external, accessToken = find_mcp_service(
        service_name
    )

    if service:
        print(f"Service Name: {service}")
        print(f"Service URL: {service_url}")
        print(f"Transport: {transport}")
        print(f"External: {external}")

        url = external
        if os.getenv("KUBERNETES_SERVICE_HOST") and os.getenv(
            "KUBERNETES_SERVICE_PORT"
        ):
            url = service_url
        if os.getenv("KUBERNETES_POD") == "true":
            url = service_url
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
            url = service_url

        if transport == "streamable-http":
            tools = await get_http_tools(url, converter, stack, accessToken)
        elif transport == "sse" or transport == "stdio":
            tools = await get_sse_tools(url, converter, stack, accessToken)
        else:
            print(f"{transport} transport not supported")
        print(f"Available tools: {[tool.name for tool in tools]}")
        for tool in tools:
            print(tool)
        return tools
    else:
        print(f"Service: {service_name} not found")


def get_mcp_tool_url(service_name):
    service, service_url, transport, external = find_mcp_service(service_name)

    if service:
        print(f"Service Name: {service}")
        print(f"Service URL: {service_url}")
        print(f"Transport: {transport}")
        print(f"External: {external}")

        url = external
        if os.getenv("KUBERNETES_SERVICE_HOST") and os.getenv(
            "KUBERNETES_SERVICE_PORT"
        ):
            url = service_url
        if os.getenv("KUBERNETES_POD") == "true":
            url = service_url
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
            url = service_url

        if transport == "streamable-http":
            return url + "/mcp", "streamable_http"
        elif transport == "sse" or transport == "stdio":
            return url + "/sse", "sse"
        else:
            print(f"{transport} transport not supported")
            return None, None
    else:
        print(f"Service: {service_name} not found")
        return None, None


if __name__ == "__main__":
    import sys

    mcp_stack = AsyncExitStack()
    converter = None
    if len(sys.argv) == 3:
        converter = sys.argv[2]
    asyncio.run(get_mcp_tools(sys.argv[1], converter, mcp_stack))
