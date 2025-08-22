#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import json
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
    kube = True
    try:
        config.load_kube_config()
    except Exception:
        kube = False

    json_data = []
    for tool_def in tool_defs:
        if kube:
            try:
                create_mcptool(tool_def)
            except Exception:
                kube = False
        create_json(tool_def, json_data)
    if len(json_data):
        print(json_data)
        json_file = os.getenv("MCP_SERVER_LIST")
        if json_file:
            if os.path.exists(json_file):
                with open(json_file, "r") as f:
                    current_data = json.load(f)
                    json_data = current_data + json_data
            with open(json_file, "w") as f:
                json.dump(json_data, f)


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


def create_json(body, list):
    if body["spec"].get("url"):
        json_data = {
            "name": body["metadata"]["name"],
            "url": body["spec"]["url"].replace("/mcp", ""),
            "transport": body["spec"]["transport"],
            "access_token": body["metadata"].get("token"),
        }
        list.append(json_data)
