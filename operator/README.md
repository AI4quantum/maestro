# Maestro Operator

This is an experimental feature of the maestro deployment in kubernetes clusters.  

This implements the maestro agent and workflow as kubernetes CRD.  An additional CRD workflowrun is defined to invoke the workflow execution.

Maestro "agent" and "workflow" are mapped to "Agent" and "Workflow" custom resources.  "maestro create-cr" takes maestro yaml file and deploys the agent and workflow in the cluster as the custom resources.  Another custom resource "WorkflowRun" has agent and workflow custom resource names and other configuration to run the workflow in the cluster.  Creating the "WorkflowRun" custom resource instance invoke the Maestro workflow.
Here is an example of the "WorkflowRun"

The names of workflow and agent are updated to match kubernetes resource naming rules.  All capital letters are changed to lowercases and the all special characters including spaces except "-" are replace to "-".

```
apiVersion: maestro.ai4quantum.com/v1alpha1
kind: WorkflowRun
metadata:
  labels:
    app.kubernetes.io/name: operator
    app.kubernetes.io/managed-by: kustomize
  name: weather-checker-ai
spec:
  agents:                      # List of agent names used in the workflow
  - temperature-agent
  - hot-or-not-agent
  workflow: maestro-deployment # Workflow name
  loglevel: DEBUG              # Currentry no effect
  nodeport: 30051              # Node port number for NodePort service, if it is not set, the service type is ClusterIP 
  environments: myconfigmap    # ConfigMap name that has the environment variables
  secrets: mysecret            # Secret name that has the secret environment variables
```

The necessary environment variables can be provided in the ConfigMap or Secret.

```
kind: ConfigMap
metadata:
  name: myconfigmap
data:
  BEE_API_KEY: sk-proj-testkey
  BEE_API: "http://127.0.0.1:4000"
```

```
apiVersion: v1
kind: Secret
metadata:
  name: mysecret
type: kubernetes.io/basic-auth
stringData:
  username: admin
  password: t0p-Secret
``` 

The agents used in the workflow are created when the workflowrun custom resource instance is created.  So the agent can be customized before the workflow is started.


## How to build and run operator:

1. build images
        cd operator
        make docker-build
        make engine-docker-build
2. Create a kind cluster
        kind create cluster --config tests/integration/deploys/kind-config.yaml
3. Load images cluster
        kind load docker-image localhost/controller:latest
        kind load docker-image localhost/maestro-engine:latest
4. Install Maestro Operator
        kubectl apply -f config/crd/bases
        make deploy
5. Deploy test agents, workflow, configmap and workflowrun
        cd ..
        python deploycr.py https://github.com/AI4quantum/maestro-demos/blob/main/workflows/weather-checker.ai/agents.yaml
python deploycr.py https://github.com/AI4quantum/maestro-demos/blob/main/workflows/weather-checker.ai/workflow.yaml
        kubectl apply -f operator/test/config/test-configmap.yaml
        kubectl apply -f operator/test/config/test-workflowrun.yaml
6. open a browser to 127.0.0.1:30051

"DRY_RUN" is set in the "operator/test/config/test-configmap.yaml".  The "BEE_API" and ""BEE_API_KEY" must be set to run with real agent.
