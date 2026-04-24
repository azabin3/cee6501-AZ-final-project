import numpy as np

try:
    from helpers.assembly import (
        partition_matrix,
        assemble_global_stiffness,
        assemble_global_fixed_end_force_vector,
    )
    from helpers.postprocess import recover_all_element_responses
except ImportError:
    from assembly import (
        partition_matrix,
        assemble_global_stiffness,
        assemble_global_fixed_end_force_vector,
    )
    from postprocess import recover_all_element_responses


def build_restrained_displacement_vector(data):
    """
    Build the restrained displacement vector in the same order as
    data["restrained_dofs"].
    """
    ur = np.zeros(len(data["restrained_dofs"]), dtype=float)

    prescribed = data["prescribed_displacements"]
    restrained_dofs = data["restrained_dofs"]

    for i, gdof in enumerate(restrained_dofs):
        if gdof in prescribed:
            ur[i] = float(prescribed[gdof])

    return ur


def build_partitioned_force_vectors(data, FEF_global):
    """
    Partition the global nodal load vector and the global fixed end force vector.
    """
    F = data["nodal_load_vector"]
    free_dofs = data["free_dofs"]
    restrained_dofs = data["restrained_dofs"]

    Ff = F[free_dofs]
    Fr = F[restrained_dofs]

    FEFf = FEF_global[free_dofs]
    FEFr = FEF_global[restrained_dofs]

    return Ff, Fr, FEFf, FEFr


def reconstruct_full_displacement_vector(data, Uf, Ur):
    """
    Rebuild the full global displacement vector.
    """
    U = np.zeros(data["ndof"], dtype=float)

    for i, gdof in enumerate(data["free_dofs"]):
        U[gdof] = Uf[i]

    for i, gdof in enumerate(data["restrained_dofs"]):
        U[gdof] = Ur[i]

    return U


def solve_linear_system(K_global, data, FEF_global=None):
    """
    Solve the partitioned linear DSM system.

    Current version uses
    - nodal loads
    - prescribed displacements
    - fixed end force effects from implemented element actions
    """
    if FEF_global is None:
        FEF_global = np.zeros(data["ndof"], dtype=float)

    free_dofs = data["free_dofs"]
    restrained_dofs = data["restrained_dofs"]

    K_ff, K_fr, K_rf, K_rr = partition_matrix(
        K_global,
        free_dofs,
        restrained_dofs,
    )

    Ff, Fr, FEFf, FEFr = build_partitioned_force_vectors(data, FEF_global)
    Ur = build_restrained_displacement_vector(data)

    rhs = Ff - K_fr @ Ur - FEFf
    Uf = np.linalg.solve(K_ff, rhs)

    U = reconstruct_full_displacement_vector(data, Uf, Ur)

    Q = K_global @ U + FEF_global
    R = Q - data["nodal_load_vector"]

    results = {
        "K_ff": K_ff,
        "K_fr": K_fr,
        "K_rf": K_rf,
        "K_rr": K_rr,
        "Ff": Ff,
        "Fr": Fr,
        "FEFf": FEFf,
        "FEFr": FEFr,
        "Ur": Ur,
        "Uf": Uf,
        "U": U,
        "Q": Q,
        "R": R,
        "FEF_global": FEF_global,
        "reactions_at_restrained_dofs": R[restrained_dofs],
    }
    return results


def solve_complete_model(model, data):
    """
    Run the full current analysis flow for a model.
    """
    K_global, element_data_list = assemble_global_stiffness(model, data)
    FEF_global = assemble_global_fixed_end_force_vector(model, data)
    results = solve_linear_system(K_global, data, FEF_global=FEF_global)
    element_responses = recover_all_element_responses(model, data, results["U"])

    package = {
        "K_global": K_global,
        "FEF_global": FEF_global,
        "element_data_list": element_data_list,
        "results": results,
        "element_responses": element_responses,
    }
    return package