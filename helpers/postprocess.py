import numpy as np

try:
    from helpers.elements_3d import (
        get_element_stiffness_data,
        get_element_fixed_end_force_local,
        get_element_fixed_end_force_global,
    )
except ImportError:
    from elements_3d import (
        get_element_stiffness_data,
        get_element_fixed_end_force_local,
        get_element_fixed_end_force_global,
    )


def extract_element_global_displacements(U, dof_map):
    """
    Extract the 12 component global displacement vector for one element.
    """
    return np.array([U[d] for d in dof_map], dtype=float)


def recover_element_response(model, elem_id, U):
    """
    Recover displacement and force response for one element.
    """
    elem_data = get_element_stiffness_data(model, elem_id)

    dof_map = elem_data["dof_map"]
    T = elem_data["T"]
    k_local = elem_data["k_local"]
    k_global = elem_data["k_global"]

    qf_local = get_element_fixed_end_force_local(model, elem_id)
    qf_global = get_element_fixed_end_force_global(model, elem_id)

    u_global_elem = extract_element_global_displacements(U, dof_map)
    v_local_elem = T @ u_global_elem

    q_local_elem = k_local @ v_local_elem + qf_local
    f_global_elem = k_global @ u_global_elem + qf_global

    response = {
        "elem_id": elem_id,
        "type": elem_data["type"],
        "dof_map": dof_map,
        "u_global_elem": u_global_elem,
        "v_local_elem": v_local_elem,
        "qf_local": qf_local,
        "qf_global": qf_global,
        "q_local_elem": q_local_elem,
        "f_global_elem": f_global_elem,
        "k_local": k_local,
        "k_global": k_global,
        "L": elem_data["L"],
    }
    return response


def recover_all_element_responses(model, data, U):
    """
    Recover response for all elements in the model.
    """
    responses = []

    for elem_id in data["element_ids"]:
        response = recover_element_response(model, elem_id, U)
        responses.append(response)

    return responses