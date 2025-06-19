from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from qiskit_ibm_catalog import QiskitFunctionsCatalog
import json
 
# Initialize FastMCP server
mcp = FastMCP("qiskitmcp")

@mcp.tool()
async def run_iskay_optimizer(problem: dict[str, float], problem_type: str, backend_name:str, instance: str, options: dict[str, Any]) -> str:
    """Quantum Optimizer that solves Quadratic Unconstrained Binary Optimization and higher-order (HUBO) optimization problems
    The running status of the optimizer is returned by get_optimizer_job_status.
    The result of the optimizer is returned by get_optmizer_result 

    Args:
        problem: Coefficients of the optmization problem encoded in a dictionary as follows: { "()" : A, "(i,): Bi, "(i,j)": Cij, ....} The keys of the dictionary must be strings containing a valid tuple if non-repeating integers.
        problem_type: spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation
        backend_name: name of backend
        instance: cloud resource name
        options: options to handle hardware submission. format is dictionary.  shots: nunber of iteration, num_iterations: total number of Bias Field iterations, use_session: where to run within a session    
    Ouput:
        job_id: job id of the optimization job
    """
    # catalog = QiskitFunctionsCatalog()
 
    # Access Function
    # optimizer = catalog.load("kipu-quantum/iskay-quantum-optimizer")

    arguments = {
        "problem": problem,
        "problem_type": problem_type,
        "instance": instance,
        "backend_name": backend_name,  # such as "ibm_fez"
        "options": options,
    }
 
    # job = optimizer.run(**arguments)
    # return job.job_id
    return "job-iskay"

@mcp.tool()
async def run_qctrl_optimizer(problem: str, problem_type: str, backend_name:str, instance: str, options: dict[str, Any]) -> str:
    """Q-CTRL Optimizer is flexible and can be used to solve combinatorial optimization problems defined as objective functions or arbitrary graphs.
    The running status of the optimizer is returned by get_optimizer_job_status.
    The result of the optimizer is returned by get_optmizer_result 

    Args:
        problem: Polynomial expression representation of an objective function. Ideally created in Python with an existing SymPy Poly object and formatted into a string using sympy.srepr. or Graph representation of a specific problem type. The graph should be created using the networkx library in Python. It should then converted to a string by using the networkx function
        problem_type: Name of the problem class; only used for graph and spin chain problem definitions, which are limited to "maxcut" or "spin_chain"; not required for arbitrary objective function problem definitions
    spin for cost function written in Ising fomulation or binary for cost function written in QUBO/HUBO formulation
        backend_name: name of backend
        instance: cloud resource name
        options: options to handle hardware submission. format is dictionary.  session_id: An existing Qiskit Runtime session ID, job_tags: A list of job tags 
    Ouput:
        job_id: job id of the optimization job
    """
    # catalog = QiskitFunctionsCatalog()
 
    # Access Function
    # optimizer = catalog.load("q-ctrl/optimization-solver")

    arguments = {
        "problem": problem,
        "problem_type": problem_type,
        "instance": instance,
        "backend_name": backend_name,  # such as "ibm_fez"
        "options": options,
    }
 
    # job = optimizer.run(**arguments)
    # return job.job_id
    return "job-qctrl"

@mcp.tool()
async def run_qunasys_quri_chemistry(molecule: dict) -> str:
    """
    Fetches the ground state energy of a given molecule using QURI Chemistry
    The running status is returned by get_quri_chemistry_job_status with job_id as the argument
    The result of the optimizer is returned by get_quri_chemistry_result with job_id as the argument

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
        job_id: job id of the optimization job
    """
    #catalog = QiskitFunctionsCatalog()
    #function = catalog.load("qunasys/quri-chemistry")

    #qsci_setting = {"n_shots": 1e5, "number_of_states_pick_out": 12000}

    #qsci_double_exc_json = {
    #  "ansatz": "DoubleExcitation",
    #  "state_prep_method": "CCSD",  
    #  "ansatz_setting": {
    #      "n_amplitudes": 20
    #  },
    #}

    #mitigation_setting = {  # Refer to the "Error mitigation" section for details.
    #  "configuration_recovery": {"number_of_states_pick_out": 10000}
    #}

    #job = function.run(
    #  method="QSCI",
    #  molecule=molecule,
    #  circuit_options=qsci_double_exc_json,
    #  qsci_setting=qsci_setting,
    #  mitigation_setting=mitigation_setting,
    #  instance="TODO_REPLACEME_CLOUD_RESROUCE_NAME",
    #  backend_name="ibm_torino",
    #)
 
    # job = optimizer.run(**arguments)
    # return job.job_id
    return "job-quri"

@mcp.tool()
async def get_quri_chemistry_job_status(job_id: str) -> str:
    """Get the quri_chemistry job status by job_id.  When the returned status is DONE, call the get_optimizer_result to get the job result" 

    Args:
        job_id: job_id returned from run_qunasys_quri_chemistry call
    Output:
        one of QUEUED, INITIALIZING, RUNNING, DONE, ERROR CANCELED
    """

    # catalog = QiskitFunctionsCatalog()
    # job = catalog.get_job_by_id(job_id)
    # status = job.status()
    # return status
    if job_id == "job-quri":
        return "DONE"
    else:
        return "ERROR"

@mcp.tool()
async def get_quri_chemistry_job_result(job_id: str) -> str:
    """Get quri_chemistry job result by job_id." 

    Args:
        job_id: job_id returned from run_qunasys_quri_chemistry call.
    Returns:
        A float of the QSCI energy
    """
    # catalog = QiskitFunctionsCatalog()
    # job = catalog.get_job_by_id(job_id)
    # result = job.result()
    # return result
    if job_id == "job-quri":
        return "RESULT"
    else:
        return "ERROR"

    
@mcp.tool()
async def get_optimizer_job_status(job_id: str) -> str:
    """Get the optimizer job status by job_id.  When the returned status is DONE, call the get_optimizer_result to get the job result" 

    Args:
        job_id: job_id returned from optimizer call
    Output:
        one of QUEUED, INITIALIZING, RUNNING, DONE, ERROR, CANCELED
    """

    # catalog = QiskitFunctionsCatalog()
    # job = catalog.get_job_by_id(job_id)
    # status = job.status()
    # return status
    if job_id == "job-iskay":
        return "DONE"
    elif job_id == "job-qctrl":
        return "DONE"
    else:
        return "ERROR"
 
@mcp.tool()
async def get_optimizer_result(job_id: str) -> str:
    """Get the optimizer job result by job_id." 

    Args:
        job_id: job_id returned from run_optimizer call.
    Output:
        result of the optimization
    """

    # catalog = QiskitFunctionsCatalog()
    # job = catalog.get_job_by_id(job_id)
    # result = job.result()
    # return result
    result_kipu = json.dumps(
        {'solution': {'0': -1, '1': -1, '2': -1, '3': 1, '4': 1},
         'solution_info': {'bitstring': '11100',
                           'cost': -13.8,
                           'seed_transpiler': 42,
                           'mapping': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
                           },
         'prob_type': 'spin'}
    )
    result_qctrl = json.dumps(
        {'solution_bitstring_cost': 3.0,
         'final_bitstring_distribution': {'000001': 100, '000011': 2},
         'iteration_count': 3,
         'solution_bitstring': '000001',
         'variables_to_bitstring_index_map': {'n[1]': 5, 'n[2]': 4, 'n[3]': 3, 'n[4]': 2, 'n[5]': 1},
         'best_parameters': [0.19628831763697097, -1.047052334523102], 'warnings': []
         }
    )

    if job_id == "job-iskay":
        return result_kipu
    elif job_id == "job-qctrl":
        return result_qctrl
    else:
        return "ERROR"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
