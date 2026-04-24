import json
from pathlib import Path
from copy import deepcopy

import numpy as np

try:
    from helpers.model_checks import run_all_model_checks
except ImportError:
    from model_checks import run_all_model_checks

TOP_LEVEL_KEYS = [
    "model_name",
    "units",
    "nodes",
    "materials",
    "sections",
    "elements",
    "supports",
    "nodal_loads",
    "member_loads",
    "prescribed_displacements",
    "temperature_loads",
    "fabrication_errors",
]

DOF_LABELS = ["ux", "uy", "uz", "rx", "ry", "rz"]
DOF_INDEX = {label: i for i, label in enumerate(DOF_LABELS)}


def load_model_json(filepath):
    """
    Read a JSON model file and return the raw model dictionary.
    """
    filepath = Path(filepath)
    with filepath.open("r", encoding="utf-8") as f:
        model = json.load(f)
    return model


def check_required_top_level_keys(model):
    """
    Check that all required top level keys exist.
    Raises ValueError if any are missing.
    """
    missing = [key for key in TOP_LEVEL_KEYS if key not in model]
    if missing:
        raise ValueError(f"Missing top level keys: {missing}")


def normalize_model(model):
    """
    Return a cleaned copy of the model with integer node and element ids
    where appropriate, while keeping the overall JSON structure unchanged.
    """
    clean = deepcopy(model)

    clean["nodes"] = {int(k): v for k, v in clean["nodes"].items()}
    clean["elements"] = {int(k): v for k, v in clean["elements"].items()}
    clean["supports"] = {int(k): v for k, v in clean["supports"].items()}

    return clean


def global_dof_number(node_id, dof_label):
    """
    Return the zero based global DOF number for a node and DOF label.
    """
    return 6 * (node_id - 1) + DOF_INDEX[dof_label]


def build_node_dof_map(model):
    """
    Build a dictionary mapping each node id to its 6 global DOF numbers.
    """
    node_ids = sorted(model["nodes"].keys())
    node_dof_map = {}

    for node_id in node_ids:
        node_dof_map[node_id] = {
            label: global_dof_number(node_id, label)
            for label in DOF_LABELS
        }

    return node_dof_map


def build_restrained_dofs(model):
    """
    Convert support definitions into a sorted list of restrained global DOFs.
    """
    restrained = []

    for node_id, dofs in model["supports"].items():
        for dof_label in dofs:
            restrained.append(global_dof_number(node_id, dof_label))

    return sorted(set(restrained))


def build_prescribed_displacement_map(model):
    """
    Convert prescribed displacement records into a global DOF to value map.
    """
    prescribed = {}

    for item in model["prescribed_displacements"]:
        gdof = global_dof_number(item["node"], item["dof"])
        prescribed[gdof] = float(item["value"])

    return prescribed


def build_nodal_load_vector(model):
    """
    Assemble the global nodal load vector from nodal load records only.
    """
    ndof = 6 * len(model["nodes"])
    F_nodal = np.zeros(ndof, dtype=float)

    for load in model["nodal_loads"]:
        node_id = load["node"]
        values = load["values"]

        for i, value in enumerate(values):
            gdof = 6 * (node_id - 1) + i
            F_nodal[gdof] += float(value)

    return F_nodal


def build_preprocessed_data(model):
    """
    Build the first analysis ready data package from the cleaned model.
    """
    node_ids = sorted(model["nodes"].keys())
    element_ids = sorted(model["elements"].keys())
    ndof = 6 * len(node_ids)

    node_dof_map = build_node_dof_map(model)
    restrained_dofs = build_restrained_dofs(model)
    prescribed_displacements = build_prescribed_displacement_map(model)
    nodal_load_vector = build_nodal_load_vector(model)

    all_dofs = list(range(ndof))
    free_dofs = [d for d in all_dofs if d not in set(restrained_dofs)]

    data = {
        "node_ids": node_ids,
        "element_ids": element_ids,
        "ndof": ndof,
        "dof_labels": DOF_LABELS.copy(),
        "node_dof_map": node_dof_map,
        "restrained_dofs": restrained_dofs,
        "free_dofs": free_dofs,
        "prescribed_displacements": prescribed_displacements,
        "nodal_load_vector": nodal_load_vector,
    }
    return data


def build_model_summary(model, data):
    """
    Build a lightweight summary of the model contents.
    """
    n_truss = sum(
        1 for e in model["elements"].values()
        if e.get("type") == "3D_truss"
    )
    n_frame = sum(
        1 for e in model["elements"].values()
        if e.get("type") == "3D_frame"
    )

    summary = {
        "model_name": model["model_name"],
        "n_nodes": len(model["nodes"]),
        "n_elements": len(model["elements"]),
        "n_truss_elements": n_truss,
        "n_frame_elements": n_frame,
        "ndof_total": data["ndof"],
        "n_free_dofs": len(data["free_dofs"]),
        "n_restrained_dofs": len(data["restrained_dofs"]),
        "n_support_nodes": len(model["supports"]),
        "n_nodal_loads": len(model["nodal_loads"]),
        "n_member_loads": len(model["member_loads"]),
        "n_prescribed_displacements": len(model["prescribed_displacements"]),
        "n_temperature_loads": len(model["temperature_loads"]),
        "n_fabrication_errors": len(model["fabrication_errors"]),
    }
    return summary


def preprocess_model(filepath):
    """
    Main preprocessing entry point for the project.

    Current behavior
    1. load raw JSON
    2. check required top level keys
    3. normalize ids
    4. run model validation checks
    5. convert supports, nodal loads, and prescribed displacements
    6. build a simple summary

    Returns
    raw_model
    clean_model
    data
    summary
    """
    raw_model = load_model_json(filepath)
    check_required_top_level_keys(raw_model)
    clean_model = normalize_model(raw_model)
    run_all_model_checks(clean_model)
    data = build_preprocessed_data(clean_model)
    summary = build_model_summary(clean_model, data)
    return raw_model, clean_model, data, summary