# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

from flask import Flask, request, render_template, Response
import os
import sys
import io
import asyncio
import threading

import yaml
from maestro.workflow import Workflow

app = Flask(__name__)
output = io.StringIO()
workflow_instance = None
thread = None
position = 0


def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data


def generate():
    global output
    global position
    global thread
    message = output.getvalue()
    if len(message) > position:
        lines = output.getvalue()[position:].splitlines()
        for line in lines:
            yield f"data: {line}\n\n"
        position = len(message)


@app.route("/stream")
def stream():
    return Response(generate(), mimetype="text/event-stream")


def start_workflow():
    global workflow_instance
    global output
    sys.stdout = output
    asyncio.run(workflow_instance.run())


@app.route("/", methods=["GET"])
def process_workflow():
    global workflow_instance
    global output
    global thread
    global position
    if request.method == "GET":
        agents_yaml = parse_yaml("src/agents.yaml")
        workflow_yaml = parse_yaml("src/workflow.yaml")
        prompt = request.args.get("Prompt")
        auto_run = os.getenv("AUTO_RUN", "false").lower() == "true"
        should_run = auto_run or prompt
        if prompt:
            workflow_yaml[0]["spec"]["template"]["prompt"] = prompt
        try:
            workflow_instance = Workflow(agents_yaml, workflow_yaml[0])
        except Exception as excep:
            raise RuntimeError("Unable to create agents") from excep
        diagram = workflow_instance.to_mermaid()
        if should_run:
            clear = request.args.get("Clear Output")
            if clear:
                output = io.StringIO()
            position = 0
            thread = threading.Thread(target=start_workflow)
            thread.start()
    name = workflow_yaml[0]["metadata"]["name"]
    return render_template("index.html", result="", title=name, diagram=diagram)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
