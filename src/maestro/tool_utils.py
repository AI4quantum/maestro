#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
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


def find_mcp_service(name):
    """
    Look for the service of mcp server name if it exist, it returns the service namd, url, and transport type for the server
    """

    # Load kubeconfig file
    config.load_kube_config()
    v1 = client.CoreV1Api()
    apis = client.CustomObjectsApi()
    namespace = "default"

    # Fetch services with the specified labels
    services = v1.list_service_for_all_namespaces(
        label_selector=f"app.kubernetes.io/instance={name},app.kubernetes.io/name=mcpserver"
    )
    for service in services.items:
        # Fetch the MCPServer CRD instance
        crd = apis.get_namespaced_custom_object(
            group=group, version=version, name=name, namespace=namespace, plural=plural
        )
        if crd:
            transport = crd["spec"]["transport"]
            external = None
            if service.spec.type == "NodePort" and service.spec.ports[0].node_port:
                external = f"http://127.0.0.1:{service.spec.ports[0].node_port}"
            return (
                service.metadata.name,
                f"http://{service.metadata.name}:{service.spec.ports[0].port}",
                transport,
                external,
            )
    return None, None, None, None


async def get_http_tools(url, converter, stack):
    transport = await stack.enter_async_context(streamablehttp_client(url + "/mcp"))
    stdio, write, _ = transport
    session = await stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()
    tools = await session.list_tools()
    if converter:
        converted = []
        for tool in tools.tools:
            try:
                print(f"puttings ession:{session}")
                converted.append(converter(session, tool))
            except Exception as e:
                print(e)
        return converted
    return tools.tools


async def get_sse_tools(url, converter, stack):
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
            tools = await get_http_tools(url, converter, stack)
        elif transport == "sse" or transport == "stdio":
            tools = await get_sse_tools(url, converter, stack)
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
