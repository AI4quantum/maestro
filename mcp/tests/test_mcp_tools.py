#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import sys
import os
import unittest
import pytest
import asyncio
from unittest import TestCase

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TOOLS_DATA_FIXTURE = {}
TOOLS_DATA_FIXTURE['run_iskay_optimizer'] = {
"name":'run_iskay_optimizer',
"description":'Quantum Optimizer that solves Quadratic Unconstrained Binary Optimization and higher-order (HUBO) optimization problems\n    The running status of the optimizer is returned by get_optimizer_job_status.\n    The result of the optimizer is returned by get_optmizer_result \n\n    Args:\n        problem: Coefficients of the optmization problem encoded in a dictionary as follows: { "()" : A, "(i,): Bi, "(i,j)": Cij, ....} The keys of the dictionary must be strings containing a valid tuple if non-repeating integers.\n        problem_type: spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation\n        backend_name: name of backend\n        instance: cloud resource name\n        options: options to handle hardware submission. format is dictionary.  shots: nunber of iteration, num_iterations: total number of Bias Field iterations, use_session: where to run within a session    \n    Ouput:\n        job_id: job id of the optimization job\n    ',
"inputSchema":{'properties': {'problem': {'additionalProperties': {'type': 'number'}, 'title': 'Problem', 'type': 'object'}, 'problem_type': {'title': 'Problem Type', 'type': 'string'}, 'backend_name': {'title': 'Backend Name', 'type': 'string'}, 'instance': {'title': 'Instance', 'type': 'string'}, 'options': {'additionalProperties': True, 'title': 'Options', 'type': 'object'}}, 'required': ['problem', 'problem_type', 'backend_name', 'instance', 'options'], 'title': 'run_iskay_optimizerArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['run_qctrl_optimizer'] = {
"name":'run_qctrl_optimizer',
"description":'Q-CTRL Optimizer is flexible and can be used to solve combinatorial optimization problems defined as objective functions or arbitrary graphs.\n    The running status of the optimizer is returned by get_optimizer_job_status.\n    The result of the optimizer is returned by get_optmizer_result \n\n    Args:\n        problem: Polynomial expression representation of an objective function. Ideally created in Python with an existing SymPy Poly object and formatted into a string using sympy.srepr. or Graph representation of a specific problem type. The graph should be created using the networkx library in Python. It should then converted to a string by using the networkx function\n        problem_type: Name of the problem class; only used for graph and spin chain problem definitions, which are limited to "maxcut" or "spin_chain"; not required for arbitrary objective function problem definitions\n    spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation\n        backend_name: name of backend\n        instance: cloud resource name\n        options: options to handle hardware submission. format is dictionary.  session_id: An existing Qiskit Runtime session ID, job_tags: A list of job tags \n    Ouput:\n        job_id: job id of the optimization job\n    ',
"inputSchema":{'properties': {'problem': {'title': 'Problem', 'type': 'string'}, 'problem_type': {'title': 'Problem Type', 'type': 'string'}, 'backend_name': {'title': 'Backend Name', 'type': 'string'}, 'instance': {'title': 'Instance', 'type': 'string'}, 'options': {'additionalProperties': True, 'title': 'Options', 'type': 'object'}}, 'required': ['problem', 'problem_type', 'backend_name', 'instance', 'options'], 'title': 'run_qctrl_optimizerArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['run_qunasys_quri_chemistry'] = {
"name":'run_qunasys_quri_chemistry',
"description":'\n    Fetches the ground state energy of a given molecule using QURI Chemistry\n    The running status is returned by get_quri_chemistry_job_status with job_id as the argument\n    The result of the optimizer is returned by get_quri_chemistry_result with job_id as the argument\n\n    Args:\n        molecule: dict\n          atom: str - The list of atom coordinates\n          basis: str - The basis set to represent the electronic wave function. default: sto-3g\n          spin: float - The Sz quantum number of the molecule. default: 0.0\n          charge: int - The total charge of the molecule. default: 0\n          active_space: json - The active space you want to choose. Review the “Active space” table for more information. default: None\n    note: active apace details\n              n_active_ele: int - The number of active electrons\n              n_active_orb: int - The number of active spatial orbitals\n              active_orbs_indices: list[int] - The list of active spatial orbital indices\n          \n\n    Returns:\n        job_id: job id of the optimization job\n    ',
"inputSchema":{'properties': {'molecule': {'additionalProperties': True, 'title': 'Molecule', 'type': 'object'}}, 'required': ['molecule'], 'title': 'run_qunasys_quri_chemistryArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['get_quri_chemistry_job_status'] = {
"name":'get_quri_chemistry_job_status',
"description":'Get the quri_chemistry job status by job_id.  When the returned status is DONE, call the get_optimizer_result to get the job result" \n\n    Args:\n        job_id: job_id returned from run_qunasys_quri_chemistry call\n    Output:\n        one of QUEUED, INITIALIZING, RUNNING, DONE, ERROR CANCELED\n    ',
"inputSchema":{'properties': {'job_id': {'title': 'Job Id', 'type': 'string'}}, 'required': ['job_id'], 'title': 'get_quri_chemistry_job_statusArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['get_quri_chemistry_job_result'] = {
"name":'get_quri_chemistry_job_result',
"description":'Get quri_chemistry job result by job_id." \n\n    Args:\n        job_id: job_id returned from run_qunasys_quri_chemistry call.\n    Returns:\n        A float of the QSCI energy\n    ',
"inputSchema":{'properties': {'job_id': {'title': 'Job Id', 'type': 'string'}}, 'required': ['job_id'], 'title': 'get_quri_chemistry_job_resultArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['get_optimizer_job_status'] = {
"name":'get_optimizer_job_status',
"description":'Get the optimizer job status by job_id.  When the returned status is DONE, call the get_optimizer_result to get the job result" \n\n    Args:\n        job_id: job_id returned from optimizer call\n    Output:\n        one of QUEUED, INITIALIZING, RUNNING, DONE, ERROR, CANCELED\n    ',
"inputSchema":{'properties': {'job_id': {'title': 'Job Id', 'type': 'string'}}, 'required': ['job_id'], 'title': 'get_optimizer_job_statusArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['get_optimizer_result'] = {
"name":'get_optimizer_result',
"description":'Get the optimizer job result by job_id." \n\n    Args:\n        job_id: job_id returned from run_optimizer call.\n    Output:\n        result of the optimization\n    ',
"inputSchema":{'properties': {'job_id': {'title': 'Job Id', 'type': 'string'}}, 'required': ['job_id'], 'title': 'get_optimizer_resultArguments', 'type': 'object'},
"annotations":None}



class TestMCPToolDefinitions(TestCase):
    def setUp(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=[os.path.dirname(os.path.abspath(__file__))+"/../mcptools/qiskit_mcp.py"],
            env=None
        )
          
    def test_each_tool(self):
        async def test():
            async with stdio_client(self.server_params) as (read, write), ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
            for tool in tools_result.tools:
                assert TOOLS_DATA_FIXTURE[tool.name]["name"] == tool.name
                assert TOOLS_DATA_FIXTURE[tool.name]["description"] == tool.description
                assert TOOLS_DATA_FIXTURE[tool.name]["inputSchema"] == tool.inputSchema
        asyncio.run(test())



        

