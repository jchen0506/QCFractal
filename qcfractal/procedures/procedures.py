"""
All procedures tasks involved in on-node computation.
"""

import json
from typing import Union

from qcelemental.models import OptimizationInput, Molecule

from ..interface.models import OptimizationRecord, ResultRecord, QCSpecification
from .procedures_util import parse_hooks, parse_single_tasks, unpack_single_task_spec


class SingleResultTasks:
    """Single is a simple Result
     Unique by: driver, method, basis, option (the name in the options table),
     and program.
    """

    def __init__(self, storage, logger):
        self.storage = storage
        self.logger = logger

    def parse_input(self, data):
        """Parse input json into internally appropriate format


        Format of the input data:
        data = {
            "meta": {
                "procedure": "single",
                "driver": "energy",
                "method": "HF",
                "basis": "sto-3g",
                "keywords": "default",
                "program": "psi4"
                },
            },
            "data": ["mol_id_1", "mol_id_2", ...],
        }

        """

        # Unpack all molecules
        moleucle_list = self.storage.get_add_molecules_mixed(data.data)["data"]

        if data.meta["keywords"]:
            keywords = self.storage.get_add_keywords_mixed([data.meta["keywords"]])["data"][0]

        else:
            keywords = None


        # Grab the tag if available
        tag = data.meta.pop("tag", None)

        # Construct full tasks
        new_tasks = []
        results_ids = []
        existing_ids = []
        for mol in moleucle_list:
            if mol is None:
                results_ids.append(None)
                continue

            mol = Molecule(**mol)

            record = ResultRecord(**data.meta, molecule=mol.id)
            inp = record.build_schema_input(mol, keywords)
            inp.extras["_qcfractal_tags"] = {"program": record.program, "keywords": record.keywords}

            ret = self.storage.add_results([record.json_dict()])

            base_id = ret["data"][0]
            results_ids.append(base_id)

            # Task is complete
            if len(ret["meta"]["duplicates"]):
                existing_ids.append(base_id)
                continue

            # Build task object
            task = {
                "spec": {
                    "function": "qcengine.compute",  # todo: add defaults in models
                    "args": [inp.json_dict(), data.meta["program"]],  # todo: json_dict should come from results
                    "kwargs": {}  # todo: add defaults in models
                },
                "hooks": [],  # todo: add defaults in models
                "tag": tag,
                "parser": "single",
                "base_result": ("results", base_id)
            }

            new_tasks.append(task)

        return new_tasks, results_ids, existing_ids, []

    def submit_tasks(self, data):

        new_tasks, results_ids, existing_ids, errors = self.parse_input(data)

        self.storage.queue_submit(new_tasks)

        n_inserted = 0
        missing = []
        for num, x in enumerate(results_ids):
            if x is None:
                missing.append(num)
            else:
                n_inserted += 1

        results = {
            "meta": {
                "n_inserted": n_inserted,
                "duplicates": [],
                "validation_errors": [],
                "success": True,
                "error_description": False,
                "errors": errors
            },
            "data": {
                "ids": results_ids,
                "submitted": [x["base_result"][1] for x in new_tasks],
                "existing": existing_ids,
            }
        }

        return results

    def parse_output(self, data):

        # Add new runs to database
        # Parse out hooks and data to same key/value
        completed_tasks = []
        updates = []
        for d in data:
            r = self.storage.get_results(id=d["base_result"]["id"])["data"][0]
            r = ResultRecord(**r)
            r.consume_output(d["result"])
            updates.append(r.json_dict())
            completed_tasks.append(d["task_id"])

        # TODO: sometimes it should be update, and others its add
        ret = self.storage.update_results(updates)

        return completed_tasks, [], []


# ----------------------------------------------------------------------------


class OptimizationTasks(SingleResultTasks):
    """
    Optimization task manipulation
    """

    def parse_input(self, data, duplicate_id="hash_index"):
        """

        json_data = {
            "meta": {
                "procedure": "optimization",
                "option": "default",
                "program": "geometric",
                "qc_meta": {
                    "driver": "energy",
                    "method": "HF",
                    "basis": "sto-3g",
                    "keywords": "default",
                    "program": "psi4"
                },
            },
            "data": ["mol_id_1", "mol_id_2", ...],
        }

        qc_schema_input = {
            "molecule": {
                "geometry": [
                    0.0,  0.0, -0.6,
                    0.0,  0.0,  0.6,
                ],
                "symbols": ["H", "H"],
                "connectivity": [[0, 1, 1]]
            },
            "driver": "gradient",
            "model": {
                "method": "HF",
                "basis": "sto-3g"
            },
            "keywords": {},
        }
        json_data = {
            "keywords": {
                "coordsys": "tric",
                "maxiter": 100,
                "program": "psi4"
            },
        }

        """

        # Unpack all molecules
        intitial_molecule_list = self.storage.get_add_molecules_mixed(data.data)["data"]

        # Unpack keywords
        if data.meta["keywords"] is None:
            opt_keywords = {}
        else:
            opt_keywords = data.meta["keywords"]
        opt_keywords["program"] = data.meta["qc_spec"]["program"]

        qc_spec = QCSpecification(**data.meta["qc_spec"])
        if qc_spec.keywords:
            qc_keywords = self.storage.get_add_keywords_mixed([meta["keywords"]])["data"][0]
            qc_keywords = keyword_set["values"]

        else:
            qc_keywords = None

        tag = data.meta.pop("tag", None)

        new_tasks = []
        results_ids = []
        existing_ids = []
        for initial_molecule in intitial_molecule_list:
            if initial_molecule is None:
                results_ids.append(None)
                continue
            initial_molecule = Molecule(**initial_molecule)


            doc = OptimizationRecord(
                initial_molecule=initial_molecule.id,
                qc_spec=qc_spec,
                keywords=opt_keywords,
                program=data.meta["program"])

            inp = doc.build_schema_input(initial_molecule=initial_molecule, qc_keywords=qc_keywords)
            inp.input_specification.extras["_qcfractal_tags"] = {"program": qc_spec.program, "keywords": qc_spec.keywords}

            ret = self.storage.add_procedures([doc.json_dict()])
            base_id = ret["data"][0]
            results_ids.append(base_id)

            # Task is complete
            if len(ret["meta"]["duplicates"]):
                existing_ids.append(base_id)
                continue

            # Build task object
            task = {
                "spec": {
                    "function": "qcengine.compute_procedure",
                    "args": [inp.json_dict(), data.meta["program"]],
                    "kwargs": {}
                },
                "hooks": [],
                "tag": tag,
                "parser": "optimization",
                "base_result": ("procedure", base_id)
            }

            new_tasks.append(task)

        return new_tasks, results_ids, existing_ids, []

    def parse_output(self, data):
        """Save the results of the procedure.
        It must make sure to save the results in the results table
        including the task_id in the TaskQueue table
        """

        new_procedures = {}


        completed_tasks = []
        updates = []
        for d in data:
            rec = self.storage.get_procedures(id=d["base_result"]["id"])["data"][0]
            rec = OptimizationRecord(**rec)

            procedure = d["result"]

            # Add initial and final molecules
            update_dict = {}
            initial_mol, final_mol = self.storage.add_molecules(
                [procedure["initial_molecule"], procedure["final_molecule"]])["data"]
            assert initial_mol == rec.initial_molecule
            update_dict["final_molecule"] = final_mol

            # Parse trajectory computations and add task_id
            traj_dict = {k: v for k, v in enumerate(procedure["trajectory"])}
            results = parse_single_tasks(self.storage, traj_dict)
            for k, v in results.items():
                v["task_id"] = d["task_id"]
                res = ResultRecord(**v)

            # Add trajectory results and return ids
            ret = self.storage.add_results(list(results.values()))
            update_dict["trajectory"] = ret["data"]
            update_dict["energies"] = procedure["energies"]

            rec = OptimizationRecord(**{**rec.dict(), **update_dict})
            updates.append(rec.json_dict())
            completed_tasks.append(d["task_id"])

        # TODO: sometimes it should be update, and others its add
        ret = self.storage.update_procedures(updates)

        return completed_tasks, [], []



# ----------------------------------------------------------------------------

supported_procedures = Union[SingleResultTasks, OptimizationTasks]


def get_procedure_parser(procedure_type: str, storage, logger) -> supported_procedures:
    """A factory methods that returns the approperiate parser class
    for the supported procedure types (like single and optimization)

    Parameters
    ---------
    procedure_type: str, 'single' or 'optimization'
    storage: storage socket object
        such as MongoengineSocket object

    Returns
    -------
    A parser class corresponding to the procedure_type:
        'single' --> SingleResultTasks
        'optimization' --> OptimizationTasks
    """

    if procedure_type == 'single':
        return SingleResultTasks(storage, logger)
    elif procedure_type == 'optimization':
        return OptimizationTasks(storage, logger)
    else:
        raise KeyError("Procedure type ({}) is not suported yet.".format(procedure_type))
