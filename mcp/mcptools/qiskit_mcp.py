#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

from typing import Any
from mcp.server.fastmcp import FastMCP
import json
import os
import importlib

# Qiskit Catalog handling

if os.getenv("IQP_TOKEN") != "None":
    module = importlib.import_module("qiskit_ibm_catalog")

class Job:
    def __init__(self, job_id):
        self.job_id = job_id
        self.result = {}
        self.status = ""

    def result(self):
        return self.result

    def status():
        return self.status

    def logs():
        return self.logs

async def run_qiskit_function(function_name: str, args: Any) -> str:
    if os.getenv("IQP_TOKEN") == "None":
        match function_name:
            case "kipu-quantum/iskay-quantum-optimizer":
                return(json.dumps({
                    'solution': {'0': -1, '1': -1, '2': -1, '3': 1, '4': 1},
                    'solution_info': {
                        'bitstring': '11100',
                        'cost': -13.8,
                        'seed_transpiler': 42,
                        'mapping': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
                     },
                     'prob_type': 'spin'
                }))
            case "q-ctrl/optimization-solver":
                return(json.dumps({
                    'solution_bitstring_cost': 3.0,
                    'final_bitstring_distribution': {'000001': 100, '000011': 2},
                    'iteration_count': 3,
                    'solution_bitstring': '000001',
                    'variables_to_bitstring_index_map': {'n[1]': 5, 'n[2]': 4, 'n[3]': 3, 'n[4]': 2, 'n[5]': 1},
                    'best_parameters': [0.19628831763697097, -1.047052334523102], 'warnings': []
                }))
            case "qunasys/quri-chemistry":
                return({"result":"result"})
            case "global-data-quantum/quantum-portfolio-optimizer":
                result = {
                    'time_step_0': {
                        '8801.T': 0.11764705882352941,
                        'ITX.MC': 0.20588235294117646,
                        'META': 0.38235294117647056,
                        'GBPJPY=X': 0.058823529411764705,
                        'TMBMKDE-10Y': 0.0,
                        'CLF': 0.058823529411764705,
                        'XS2239553048': 0.17647058823529413
                    },
                    'time_step_1': {
                        '8801.T': 0.11428571428571428,
                        'ITX.MC': 0.14285714285714285,
                        'META': 0.2,
                        'GBPJPY=X': 0.02857142857142857,
                        'TMBMKDE-10Y': 0.42857142857142855,
                        'CLF': 0.0,
                        'XS2239553048': 0.08571428571428572
                    },
                    'time_step_2': {
                        '8801.T': 0.0,
                        'ITX.MC': 0.09375,
                        'META': 0.3125,
                        'GBPJPY=X': 0.34375,
                        'TMBMKDE-10Y': 0.0,
                        'CLF': 0.0,
                        'XS2239553048': 0.25
                    },
                    'time_step_3': {
                        '8801.T': 0.3939393939393939,
                        'ITX.MC': 0.09090909090909091,
                        'META': 0.12121212121212122,
                        'GBPJPY=X': 0.18181818181818182,
                        'TMBMKDE-10Y': 0.0,
                        'CLF': 0.0,
                        'XS2239553048': 0.21212121212121213
                    }
                }
                metadata = {"all_samples_metrics": {"objective_costs": [1.25, 0.98], "states": [[0, 1, 0, 1, 0, 1], [0, 0, 0, 1, 1, 1]], "rest_breaches": [0.0, 0.25], "sharpe_ratios": [1.1, 0.7], "returns": [0.15, 0.10]}}
                return(json.dumps({"result": result, "metadata": metadata}))
            case _:
                print("Not supported function")
                return None
    else:
        catalog = module.QiskitFunctionsCatalog(os.getenv("IQP_TOKEN"))
        qiskit_function = catalog.load(function_name)
        instance = os.getenv("IQP_INSTANCE", "project-based/internal/functions")
        if instance == "None":
            instance = "project-based/internal/functions"
        channel = os.getenv("IQP_CHANNEL", "ibm_quantum")
        if channel == "None":
            channel = "ibm_quantum"
        job = qiskit_function.run(**args, instance=instance, channel=channel)
        print(f"Job id: {job.job_id}")

        job_status = job.status()
        while job_status != "DONE" and job_status != "ERROR":
            job_status = job.status()
            print(job_status)
            time.sleep(30)

        if job_status == "ERROR":
            return json.dumps({"logs":job.logs(), "result": job.result()})
        else:
            return json.dumps(job.result())


# Initialize FastMCP server
mcp = FastMCP("qiskitmcp")

# MCP Tools

@mcp.tool()
async def run_iskay_optimizer(problem: dict[str, float], problem_type: str, backend_name:str, instance: str, options: dict[str, Any]) -> str:
    """Quantum Optimizer that solves Quadratic Unconstrained Binary Optimization and higher-order (HUBO) optimization problems

    Args:
        problem: Coefficients of the optmization problem encoded in a dictionary as follows: { "()" : A, "(i,): Bi, "(i,j)": Cij, ....} The keys of the dictionary must be strings containing a valid tuple if non-repeating integers.
        problem_type: spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation
        backend_name: name of backend
        instance: cloud resource name
        options: options to handle hardware submission. format is dictionary.  shots: nunber of iteration, num_iterations: total number of Bias Field iterations, use_session: where to run within a session    
    Ouput:
        solution: solution of the optimization
        solution_info: information related to the optimization
    """
    arguments = {
        "problem": problem,
        "problem_type": problem_type,
        "instance": instance,
        "backend_name": backend_name,  # such as "ibm_fez"
        "options": options,
    }
    return await run_qiskit_function("kipu-quantum/iskay-quantum-optimizer",arguments)

@mcp.tool()
async def run_qctrl_optimizer(problem: str, problem_type: str, backend_name:str, instance: str, options: dict[str, Any]) -> str:
    """Q-CTRL Optimizer is flexible and can be used to solve combinatorial optimization problems defined as objective functions or arbitrary graphs.

    Args:
        problem: Polynomial expression representation of an objective function. Ideally created in Python with an existing SymPy Poly object and formatted into a string using sympy.srepr. or Graph representation of a specific problem type. The graph should be created using the networkx library in Python. It should then converted to a string by using the networkx function
        problem_type: Name of the problem class; only used for graph and spin chain problem definitions, which are limited to "maxcut" or "spin_chain"; not required for arbitrary objective function problem definitions
    spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation
        backend_name: name of backend
        instance: cloud resource name
        options: options to handle hardware submission. format is dictionary.  session_id: An existing Qiskit Runtime session ID, job_tags: A list of job tags 
    Ouput:
        solution_bitstring_cost: int
        final_bitstring_distribution: dict
        iteration_count: int
        solution_bitstring: int
        variables_to_bitstring_index_map: dict
        best_parameters: list
    """
    arguments = {
        "problem": problem,
        "problem_type": problem_type,
        "instance": instance,
        "backend_name": backend_name,  # such as "ibm_fez"
        "options": options,
    }
    return qiskit_functions.run_qiskit_function("q-ctrl/optimization-solver", arguments)

@mcp.tool()
async def run_qunasys_quri_chemistry(molecule: dict) -> str:
    """
    Fetches the ground state energy of a given molecule using QURI Chemistry

    Args:
        molecule: dict
          atom: str - The list of atom coordinates
          basis: str - The basis set to represent the electronic wave function. default: sto-3g
          spin: float - The Sz quantum number of the molecule. default: 0.0
          charge: int - The total charge of the molecule. default: 0
          active_space: json - The active space you want to choose. Review the “Active space” table for more information. default: None
    note: active apace details
              n_active_ele: int - The number of active electrons
              n_active_orb: int - The number of active spatial orbitals
              active_orbs_indices: list[int] - The list of active spatial orbital indices
          

    Returns:
        result: job result
    """
    qsci_setting = {"n_shots": 1e5, "number_of_states_pick_out": 12000}

    qsci_double_exc_json = {
      "ansatz": "DoubleExcitation",
      "state_prep_method": "CCSD",
      "ansatz_setting": {
          "n_amplitudes": 20
      },
    }

    mitigation_setting = {  # Refer to the "Error mitigation" section for details.
      "configuration_recovery": {"number_of_states_pick_out": 10000}
    }

    arguments = {
      "method": "QSCI",
      "molecule": molecule,
      "circuit_options": qsci_double_exc_json,
      "qsci_setting": qsci_setting,
      "mitigation_setting": mitigation_setting,
      "instance": "TODO_REPLACEME_CLOUD_RESROUCE_NAME",
      "backend_name": "ibm_torino",
    }
    return qiskit_functions.run_qiskit_function("qunasys/quri-chemistry", arguments)


@mcp.tool()
async def run_dpo_solver(assets: dict, qubo_settings: dict, optimizer_settings: dict, ansatz_settings: dict, backend_name:str, previous_session_id=[], apply_postprocess:bool=True ) -> str:
    """Run the Quantum Portfolio Optimizer function that uses the Variational Quantum Eigensolver (VQE) algorithm to solve a Quadratic Unconstrained Binary Optimization (QUBO) problem, addressing dynamic portfolio optimization problems

    Args:
        asset: Dictionary with the asset prices
           template is:
             {
                "asset_name": {
                   "date": closing_value,
                   ...
                },
                ...
             }
           example is:
             {
                 "8801.T": {
                     "2023-01-01": 2374.0,
                     "2023-01-02": 2374.0,
                     "2023-01-03": 2374.0,
                     "2023-01-04": 2356.5,
                     ...
                 },
                 "AAPL": {
                     "2023-01-01": 145.2,
                     "2023-01-02": 146.5,
                     "2023-01-03": 147.3,
                     "2023-01-04": 148.1,
                     ...
                 },
                 ...
             }
           Note: The asset data must contain, at least, the closing prices at (nt+1) * dt (see the qubo_settings input section) time stamps (for example, days).

        qubo_settings: Dictionary of the qubo setting with following keys and values.
          nc: int - Number of time steps. Required
          nq: int - Number of resolution qubits. Required
          max_investment: float - Maximum number of invested currency units across all assets. Required
          dt: int - Time window considered in each time step. The unit matches the time intervals between the keys in the asset data. default is 30
          risk_aversion: float - Risk aversion coefficient. default is 1000
          transaction_fee: float - Transaction fee coefficient. default 0s 0.01
          restriction_coeff: float - Lagrange multiplier used to enforce the problem constraint within the QUBO formulation. default is 1

        ansatz_settings: optional
        optimizer_settings: optional
        backend: optional
        previous_session_id: optional
        apply_postprocess: optional
        tags: optional

     Ouput:
        result: resulting strategies
        metadata: information related to the result
    """

    arguments = {
        "asset": asset,
        "qubo_settings": qubo_settings,
        "optimizer_settings": optimizer_settings,
        "ansatz_settings": ansatz_settings,
        "backend_name": backend_name,
        "previous_session_id": previous_session_id,
        "apply_postprocess": apply_postprocess,
    }
    return qiskit_functions.run_qiskit_funtion("global-data-quantum/quantum-portfolio-optimizer", arguments)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
