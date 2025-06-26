# Qiskit Workflows: QAOA

Demo of how to run QAOA as a Qiskit Pattern on Maestro.


## Quickstart

### Create a Kind cluster

```bash
kind create cluster --image kindest/node:v1.32.3
```


### Install Qiskit Serverless

(assumes [helm chart](https://github.com/Qiskit/qiskit-serverless/tree/main/charts/qiskit-serverless) is available on local system in current directory)

```bash
helm install qs \
    --set platform=kind \
    --set nginxIngressControllerEnable=false \
    --set gateway.image.repository=icr.io/quantum-public/qiskit-serverless/gateway \
    --set gateway.image.tag=0.22.0 \
    --set gateway.application.ray.nodeImage=icr.io/quantum-public/qiskit-serverless/ray-node:0.22.0 \
    --set gateway.application.ray.cpu=1 \
    --set gateway.application.ray.memory=2 \
    --set gateway.application.debug=1 \
    .
```

After all pods are running, expose the gateway service:

```bash
kubectl port-forward svc/gateway 8000
```


### Add dependencies

```bash
pip install qiskit-serverless qiskit numpy
```


### Upload QAOA function to Qiskit Serverless

```bash
./scripts/upload_function.py
```


### Run workflow

```bash
maestro deploy agents.yaml workflow.yaml
```
