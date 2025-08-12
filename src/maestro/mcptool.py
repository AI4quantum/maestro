#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

from kubernetes import client, config

# Define the plural and singular names for the custom resource
toolhivePlural = "mcpservers"
toolhiveSingular = "mcpserver"

# Define the group, version, and kind for the custom resource
toolhiveGroup = "toolhive.stacklok.dev"
toolhiveVersion = "v1alpha1"
toolhiveKind = "MCPServer"

# Define the plural and singular names for the custom resource
remotePlural = "remotemcpservers"
remoteSingular = "remotemcpserver"

# Define the group, version, and kind for the custom resource
remoteGroup = "maestro.ai4quantum.com"
remoteVersion = "v1alpha1"
remoteKind = "RemoteMCPServer"


def create_mcptools(tool_defs):
    # Load kubeconfig
    config.load_kube_config()
    for tool_def in tool_defs:
        create_mcptool(tool_def)


def create_mcptool(body):
    # Create an instance of the API class for the custom resource definition
    api_instance = client.CustomObjectsApi()
    url = body["spec"].get("url")
    apiVersion = ""
    group = ""
    version = ""
    plural = ""
    if url:
        # Create the RemoteMCPServer CRD instance
        apiVersion = f"{remoteGroup}/{remoteVersion}"
        kind = "RemoteMCPServer"
        group = remoteGroup
        version = remoteVersion
        plural = remotePlural
    else:
        # Create the MCPServer CRD instance
        apiVersion = f"{toolhiveGroup}/{toolhiveVersion}"
        kind = "MCPServer"
        group = toolhiveGroup
        version = toolhiveVersion
        plural = toolhivePlural
    # Create the CRD instance
    body["apiVersion"] = apiVersion
    body["kind"] = kind
    namespace = body["metadata"].get("namespace")
    if not namespace:
        namespace = "default"
    api_response = api_instance.create_namespaced_custom_object(
        group, version, namespace, plural, body
    )
    print(f"MCP tool: {api_response['metadata']['name']} successfully created")
