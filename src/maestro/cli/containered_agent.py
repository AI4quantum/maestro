# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

from kubernetes import client, config
from maestro.cli.common import parse_yaml, Console


def create_containered_agent(
    agents_file: str, agent_name: str = None, host: str = "127.0.0.1", port: int = 8000
):
    """
    Create a containered agent
    """
    try:
        agents_yaml = parse_yaml(agents_file)
        # Load agents into memory
        for agent_def in agents_yaml:
            name = agent_def["metadata"]["name"]
            if not agent_name or agent_name == name:
                create_deployment_service(
                    agent_def["spec"]["image"],
                    name,
                    container_port=port,
                )
                break
    except Exception as e:
        Console.error(f"Failed to load agents: {str(e)}")
        raise


def create_deployment_service(
    image_url,
    app_name,
    namespace="default",
    replicas=1,
    container_port=80,
    service_port=80,
    service_type="LoadBalancer",
    node_port=30051,
):
    """
    Creates a Kubernetes Deployment and Service for a given container image.

    Args:
        image_url (str): The URL of the container image (e.g., "nginx:latest").
        app_name (str): The name for the Kubernetes application (used for labels, deployment, and service names).
        namespace (str): The Kubernetes namespace to deploy to (default: "default").
        replicas (int): The number of desired replicas for the deployment (default: 1).
        container_port (int): The port the container listens on (default: 80).
        service_port (int): The port the service exposes (default: 80).
        service_type (str): The type of Kubernetes Service (e.g., "LoadBalancer", "NodePort", "ClusterIP").
    """
    config.load_kube_config()  # Loads Kubernetes configuration from default kubeconfig file

    api_apps_v1 = client.AppsV1Api()
    api_core_v1 = client.CoreV1Api()

    # Define Deployment
    deployment_manifest = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=app_name, labels={"app": app_name}),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app": app_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": app_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=app_name,
                            image=image_url,
                            image_pull_policy="IfNotPresent",
                            ports=[
                                client.V1ContainerPort(container_port=container_port)
                            ],
                        )
                    ]
                ),
            ),
        ),
    )

    # Create Deployment
    try:
        api_apps_v1.create_namespaced_deployment(
            body=deployment_manifest, namespace=namespace
        )
        Console.print(
            f"Deployment '{app_name}' created successfully in namespace '{namespace}'."
        )
    except client.ApiException as e:
        Console.print(f"Error creating Deployment: {e}")

    # Define Service
    service_manifest = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=app_name, labels={"app": app_name}),
        spec=client.V1ServiceSpec(
            selector={"app": app_name},
            ports=[
                client.V1ServicePort(
                    port=service_port, target_port=container_port, node_port=node_port
                )
            ],
            type=service_type,
        ),
    )

    # Create Service
    try:
        api_core_v1.create_namespaced_service(
            body=service_manifest, namespace=namespace
        )
        Console.print(
            f"Service '{app_name}' created successfully in namespace '{namespace}'."
        )
    except client.ApiException as e:
        Console.print(f"Error creating Service: {e}")
