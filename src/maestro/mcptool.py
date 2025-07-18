#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

from kubernetes import client, config


def create_mcptools(tool_defs):
    for tool_def in tool_defs:
        create_mcptool(tool_def)


# Load kubeconfig
config.load_kube_config()

# Create an instance of the API class for the custom resource definition
api_instance = client.CustomObjectsApi()

# Define the plural and singular names for the custom resource
plural = "mcpservers"
singular = "mcpserver"

# Define the group, version, and kind for the custom resource
group = "toolhive.stacklok.dev"
version = "v1alpha1"
kind = "MCPServer"


def create_mcptool(body):
    # Create the CRD instance
    body["apiVersion"] = f"{group}/{version}"
    body["kind"] = "MCPServer"
    namespace = body["metadata"].get("namespace")
    if not namespace:
        namespace = "default"
    api_response = api_instance.create_namespaced_custom_object(
        group, version, namespace, plural, body
    )
    print(f"MCP tool: {api_response['metadata']['name']} successfully created")
