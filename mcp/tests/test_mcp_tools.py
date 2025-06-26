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
"description":'Quantum Optimizer that solves Quadratic Unconstrained Binary Optimization and higher-order (HUBO) optimization problems\n\n    Args:\n        problem: Coefficients of the optmization problem encoded in a dictionary as follows: { "()" : A, "(i,): Bi, "(i,j)": Cij, ....} The keys of the dictionary must be strings containing a valid tuple if non-repeating integers.\n        problem_type: spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation\n        backend_name: name of backend\n        instance: cloud resource name\n        options: options to handle hardware submission. format is dictionary.  shots: nunber of iteration, num_iterations: total number of Bias Field iterations, use_session: where to run within a session    \n    Ouput:\n        solution: solution of the optimization\n        solution_info: information related to the optimization\n    ',
"inputSchema":{'properties': {'problem': {'additionalProperties': {'type': 'number'}, 'title': 'Problem', 'type': 'object'}, 'problem_type': {'title': 'Problem Type', 'type': 'string'}, 'backend_name': {'title': 'Backend Name', 'type': 'string'}, 'instance': {'title': 'Instance', 'type': 'string'}, 'options': {'additionalProperties': True, 'title': 'Options', 'type': 'object'}}, 'required': ['problem', 'problem_type', 'backend_name', 'instance', 'options'], 'title': 'run_iskay_optimizerArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['run_qctrl_optimizer'] = {
"name":'run_qctrl_optimizer',
"description":'Q-CTRL Optimizer is flexible and can be used to solve combinatorial optimization problems defined as objective functions or arbitrary graphs.\n\n    Args:\n        problem: Polynomial expression representation of an objective function. Ideally created in Python with an existing SymPy Poly object and formatted into a string using sympy.srepr. or Graph representation of a specific problem type. The graph should be created using the networkx library in Python. It should then converted to a string by using the networkx function\n        problem_type: Name of the problem class; only used for graph and spin chain problem definitions, which are limited to "maxcut" or "spin_chain"; not required for arbitrary objective function problem definitions\n    spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation\n        backend_name: name of backend\n        instance: cloud resource name\n        options: options to handle hardware submission. format is dictionary.  session_id: An existing Qiskit Runtime session ID, job_tags: A list of job tags \n    Ouput:\n        solution_bitstring_cost: int\n        final_bitstring_distribution: dict\n        iteration_count: int\n        solution_bitstring: int\n        variables_to_bitstring_index_map: dict\n        best_parameters: list\n    ',
"inputSchema":{'properties': {'problem': {'title': 'Problem', 'type': 'string'}, 'problem_type': {'title': 'Problem Type', 'type': 'string'}, 'backend_name': {'title': 'Backend Name', 'type': 'string'}, 'instance': {'title': 'Instance', 'type': 'string'}, 'options': {'additionalProperties': True, 'title': 'Options', 'type': 'object'}}, 'required': ['problem', 'problem_type', 'backend_name', 'instance', 'options'], 'title': 'run_qctrl_optimizerArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['run_qunasys_quri_chemistry'] = {
"name":'run_qunasys_quri_chemistry',
"description":'\n    Fetches the ground state energy of a given molecule using QURI Chemistry\n\n    Args:\n        molecule: dict\n          atom: str - The list of atom coordinates\n          basis: str - The basis set to represent the electronic wave function. default: sto-3g\n          spin: float - The Sz quantum number of the molecule. default: 0.0\n          charge: int - The total charge of the molecule. default: 0\n          active_space: json - The active space you want to choose. Review the “Active space” table for more information. default: None\n    note: active apace details\n              n_active_ele: int - The number of active electrons\n              n_active_orb: int - The number of active spatial orbitals\n              active_orbs_indices: list[int] - The list of active spatial orbital indices\n          \n\n    Returns:\n        result: job result\n    ',
"inputSchema":{'properties': {'molecule': {'additionalProperties': True, 'title': 'Molecule', 'type': 'object'}}, 'required': ['molecule'], 'title': 'run_qunasys_quri_chemistryArguments', 'type': 'object'},
"annotations":None}

TOOLS_DATA_FIXTURE['run_dpo_solver'] = {
"name":'run_dpo_solver',


"description":'Run the Quantum Portfolio Optimizer function that uses the Variational Quantum Eigensolver (VQE) algorithm to solve a Quadratic Unconstrained Binary Optimization (QUBO) problem, addressing dynamic portfolio optimization problems\n\n    Args:\n        asset: Dictionary with the asset prices\n           template is:\n             {\n                "asset_name": {\n                   "date": closing_value,\n                   ...\n                },\n                ...\n             }\n           example is:\n             {\n                 "8801.T": {\n                     "2023-01-01": 2374.0,\n                     "2023-01-02": 2374.0,\n                     "2023-01-03": 2374.0,\n                     "2023-01-04": 2356.5,\n                     ...\n                 },\n                 "AAPL": {\n                     "2023-01-01": 145.2,\n                     "2023-01-02": 146.5,\n                     "2023-01-03": 147.3,\n                     "2023-01-04": 148.1,\n                     ...\n                 },\n                 ...\n             }\n           Note: The asset data must contain, at least, the closing prices at (nt+1) * dt (see the qubo_settings input section) time stamps (for example, days).\n\n        qubo_settings: Dictionary of the qubo setting with following keys and values.\n          nc: int - Number of time steps. Required\n          nq: int - Number of resolution qubits. Required\n          max_investment: float - Maximum number of invested currency units across all assets. Required\n          dt: int - Time window considered in each time step. The unit matches the time intervals between the keys in the asset data. default is 30\n          risk_aversion: float - Risk aversion coefficient. default is 1000\n          transaction_fee: float - Transaction fee coefficient. default 0s 0.01\n          restriction_coeff: float - Lagrange multiplier used to enforce the problem constraint within the QUBO formulation. default is 1\n\n        ansatz_settings: optional\n        optimizer_settings: optional\n        backend: optional\n        previous_session_id: optional\n        apply_postprocess: optional\n        tags: optional\n\n     Ouput:\n        result: resulting strategies\n        metadata: information related to the result\n    ',
"inputSchema":{'properties': {'assets': {'additionalProperties': True, 'title': 'Assets', 'type': 'object'}, 'qubo_settings': {'additionalProperties': True, 'title': 'Qubo Settings', 'type': 'object'}, 'optimizer_settings': {'additionalProperties': True, 'title': 'Optimizer Settings', 'type': 'object'}, 'ansatz_settings': {'additionalProperties': True, 'title': 'Ansatz Settings', 'type': 'object'}, 'backend_name': {'title': 'Backend Name', 'type': 'string'}, 'previous_session_id': {'default': [], 'title': 'previous_session_id', 'type': 'string'}, 'apply_postprocess': {'default': True, 'title': 'Apply Postprocess', 'type': 'boolean'}}, 'required': ['assets', 'qubo_settings', 'optimizer_settings', 'ansatz_settings', 'backend_name'], 'title': 'run_dpo_solverArguments', 'type': 'object'},
"annotations":None}

class TestMCPToolDefinitions(TestCase):
    def setUp(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=[os.path.dirname(os.path.abspath(__file__))+"/../mcptools/qiskit_mcp.py"],
            env={"IQP_TOKEN": "None", "IQP_CHANNEL": "None", "IQP_INSTANCE": "None"}
        )
        print("#####")
        print(os.path.dirname(os.path.abspath(__file__))+"/../mcptools/qiskit_mcp.py")
        print(os.getcwd())
          
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
