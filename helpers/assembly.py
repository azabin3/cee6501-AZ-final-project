import numpy as np

try:
    from helpers.elements_3d import (
        get_element_stiffness_data,
        get_element_fixed_end_force_global,
    )
except ImportError:
    from elements_3d import (
        get_element_stiffness_data,
        get_element_fixed_end_force_global,
    )


def assemble_global_stiffness(model, data):
    """
    Assemble the full global stiffness matrix from all elements.

    Returns
    K_global
    element_data_list
    """
    ndof = data["ndof"]
    K_global = np.zeros((ndof, ndof), dtype=float)
    element_data_list = []

    for elem_id in data["element_ids"]:
        elem_data = get_element_stiffness_data(model, elem_id)
        dof_map = elem_data["dof_map"]
        k_global_elem = elem_data["k_global"]

        for a in range(12):
            A = dof_map[a]
            for b in range(12):
                B = dof_map[b]
                K_global[A, B] += k_global_elem[a, b]

        element_data_list.append(elem_data)

    return K_global, element_data_list


def assemble_global_fixed_end_force_vector(model, data):
    """
    Assemble the full global fixed end force vector from all currently
    implemented element effects.
    """
    ndof = data["ndof"]
    FEF_global = np.zeros(ndof, dtype=float)

    for elem_id in data["element_ids"]:
        dof_map = get_element_stiffness_data(model, elem_id)["dof_map"]
        qf_global_elem = get_element_fixed_end_force_global(model, elem_id)

        for a in range(12):
            A = dof_map[a]
            FEF_global[A] += qf_global_elem[a]

    return FEF_global


def partition_matrix(K_global, free_dofs, restrained_dofs):
    """
    Partition the global stiffness matrix into free and restrained blocks.

    Returns
    K_ff, K_fr, K_rf, K_rr
    """
    K_ff = K_global[np.ix_(free_dofs, free_dofs)]
    K_fr = K_global[np.ix_(free_dofs, restrained_dofs)]
    K_rf = K_global[np.ix_(restrained_dofs, free_dofs)]
    K_rr = K_global[np.ix_(restrained_dofs, restrained_dofs)]

    return K_ff, K_fr, K_rf, K_rr