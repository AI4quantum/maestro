# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Streamlit deployment module for Maestro workflow UI."""

import sys
import os
import psutil

def find_repo_root(path, marker="pyproject.toml"):
    while path != "/":
        if marker in os.listdir(path):
            return path
        path = os.path.dirname(path)
    return None

repo_root = find_repo_root(os.path.dirname(os.path.abspath(__file__)))
if repo_root:
    src_dir = os.path.join(repo_root, "src")
    sys.path.insert(0, src_dir)

import streamlit as st
import streamlit.web.cli as st_cli

from streamlit import runtime
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from maestro.cli.common import parse_yaml

from streamlit_workflow_ui import StreamlitWorkflowUI

sys_stdout = sys.stdout

def deploy_agents_workflow_streamlit(agents_file, workflow_file):
    """Deploy and run a Maestro workflow using Streamlit UI."""
    workflow_yaml = parse_yaml(workflow_file)

    st.set_page_config(
        page_title="Maestro Workflow",
        page_icon="🤖",
        layout="centered"
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to Maestro workflow"}]

    st.image("images/maestro.png", width=200)
    st.title("Maestro workflow")

    ui = StreamlitWorkflowUI(agents_file, workflow_file, workflow_yaml[0]['spec']['template']['prompt'], 'Maestro workflow')
    ui.setup_ui()

if __name__ == '__main__':
    if runtime.exists():
        ctx = get_script_run_ctx()
        deploy_agents_workflow_streamlit(sys.argv[1], sys.argv[2])
        add_script_run_ctx(psutil.Process(os.getpid()), ctx)
    else:
        sys.exit(st_cli.main())
