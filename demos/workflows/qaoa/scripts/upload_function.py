#! /usr/bin/env python3

from qiskit_serverless import ServerlessClient, QiskitFunction
import os

serverless = ServerlessClient(
    token=os.environ.get("GATEWAY_TOKEN", "awesome_token"),
    host=os.environ.get("GATEWAY_HOST", "http://localhost:8000"),
)

function = QiskitFunction(
    title="qaoa",
    entrypoint="qaoa.py",
    working_dir="./functions/qaoa/",
    dependencies=["qiskit_aer"]
)

serverless.upload(function)
print("Available functions:")
for f in serverless.functions():
    print(f)
