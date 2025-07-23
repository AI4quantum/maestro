#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
from kubernetes import client, config

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client

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


async def get_http_tools(url, converter):
    async with streamablehttp_client(url + "/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            if converter:
                converted = []
                for tool in tools.tools:
                    try:
                        converted.append(converter(session, tool))
                    except Exception as e:
                        print(e)
                return converted
            return tools.tools


async def get_sse_tools(url, converter):
    async with sse_client(url + "/sse") as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            tools = await session.list_tools()
            if converter:
                converted = []
                for tool in tools.tools:
                    converted.append(converter(session, tool))
                return converted
            return tools.tools


async def get_mcp_tools(service_name, converter):
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
            tools = await get_http_tools(url, converter)
        elif transport == "sse":
            tools = await get_sse_tools(url, converter)
        else:
            print(f"{transport} transport not supported")
        print(f"Available tools: {[tool.name for tool in tools]}")
        for tool in tools:
            print(tool)
        return tools
    else:
        print(f"Service: {service_name} not found")


if __name__ == "__main__":
    import sys

    converter = None
    if len(sys.argv) == 3:
        converter = sys.argv[2]
    asyncio.run(get_mcp_tools(sys.argv[1], converter))
