import numpy as np

FULL_RELEASE_SET = {"rx", "ry", "rz"}


def global_dof_number(node_id, local_index):
    """
    Zero based global DOF number for a node and local DOF index.
    local_index should be 0 to 5.
    """
    return 6 * (node_id - 1) + local_index


def element_dof_map_3d(node_i, node_j):
    """
    Full 12 DOF map for a 3D two node element.

    Order
    [uxi, uyi, uzi, rxi, ryi, rzi, uxj, uyj, uzj, rxj, ryj, rzj]
    """
    dofs_i = [global_dof_number(node_i, k) for k in range(6)]
    dofs_j = [global_dof_number(node_j, k) for k in range(6)]
    return dofs_i + dofs_j


def node_coordinates(model, node_id):
    """
    Return node coordinates as a NumPy array.
    """
    return np.array(model["nodes"][node_id], dtype=float)


def element_end_coordinates(model, element):
    """
    Return xi and xj coordinate vectors for an element record.
    """
    node_i, node_j = element["nodes"]
    xi = node_coordinates(model, node_i)
    xj = node_coordinates(model, node_j)
    return xi, xj


def element_vector_length_and_xaxis(model, element):
    """
    Return the element vector, length, and local x axis unit vector.
    """
    xi, xj = element_end_coordinates(model, element)
    vec = xj - xi
    L = np.linalg.norm(vec)

    if L <= 0.0:
        raise ValueError("Element has zero length.")

    ex = vec / L
    return vec, L, ex


def choose_reference_vector(ex):
    """
    Choose a reference vector that is not nearly parallel to the local x axis.
    """
    global_z = np.array([0.0, 0.0, 1.0], dtype=float)
    global_y = np.array([0.0, 1.0, 0.0], dtype=float)

    if abs(np.dot(ex, global_z)) < 0.9:
        return global_z
    return global_y


def rotation_matrix_3d_basic(model, element):
    """
    Build the basic 3x3 rotation matrix using the course style construction.

    Rows of R are the local unit vectors expressed in global coordinates.
    """
    _, _, ex = element_vector_length_and_xaxis(model, element)

    ref = choose_reference_vector(ex)

    ey = np.cross(ref, ex)
    ey_norm = np.linalg.norm(ey)
    if ey_norm <= 0.0:
        raise ValueError("Failed to construct local y axis.")
    ey = ey / ey_norm

    ez = np.cross(ex, ey)
    ez_norm = np.linalg.norm(ez)
    if ez_norm <= 0.0:
        raise ValueError("Failed to construct local z axis.")
    ez = ez / ez_norm

    R = np.vstack([ex, ey, ez])
    return R


def transformation_matrix_12x12(R):
    """
    Build the 12x12 transformation matrix from the 3x3 rotation matrix.
    """
    T = np.zeros((12, 12), dtype=float)
    T[0:3, 0:3] = R
    T[3:6, 3:6] = R
    T[6:9, 6:9] = R
    T[9:12, 9:12] = R
    return T


def get_element_basic_3d_data(model, elem_id):
    """
    Return the basic geometry and transformation data for one element.
    """
    element = model["elements"][elem_id]
    node_i, node_j = element["nodes"]

    vec, L, ex = element_vector_length_and_xaxis(model, element)
    R = rotation_matrix_3d_basic(model, element)
    T = transformation_matrix_12x12(R)
    dof_map = element_dof_map_3d(node_i, node_j)

    data = {
        "elem_id": elem_id,
        "type": element["type"],
        "node_i": node_i,
        "node_j": node_j,
        "vector": vec,
        "L": L,
        "ex": ex,
        "R": R,
        "T": T,
        "dof_map": dof_map,
    }
    return data


def get_element_material_section(model, elem_id):
    """
    Return the material and section dictionaries for an element.
    """
    element = model["elements"][elem_id]
    material = model["materials"][element["material"]]
    section = model["sections"][element["section"]]
    return material, section


def get_frame_release_dofs_local(model, elem_id):
    """
    Current implementation supports only
    no release
    full release at start
    full release at end
    full release at both ends
    """
    element = model["elements"][elem_id]
    release = element.get("release", {"start": [], "end": []})

    start_set = set(release.get("start", []))
    end_set = set(release.get("end", []))

    release_dofs = []

    if start_set == FULL_RELEASE_SET:
        release_dofs.extend([3, 4, 5])

    if end_set == FULL_RELEASE_SET:
        release_dofs.extend([9, 10, 11])

    return release_dofs


def apply_release_condensation(k_local_unreleased, qf_local_unreleased, release_dofs):
    """
    Apply static condensation to released DOFs.

    Returns a modified full size local stiffness matrix and
    a modified full size local fixed end force vector.
    """
    if len(release_dofs) == 0:
        return k_local_unreleased.copy(), qf_local_unreleased.copy()

    keep_dofs = [i for i in range(12) if i not in release_dofs]

    k_cc = k_local_unreleased[np.ix_(keep_dofs, keep_dofs)]
    k_cr = k_local_unreleased[np.ix_(keep_dofs, release_dofs)]
    k_rc = k_local_unreleased[np.ix_(release_dofs, keep_dofs)]
    k_rr = k_local_unreleased[np.ix_(release_dofs, release_dofs)]

    qf_c = qf_local_unreleased[keep_dofs]
    qf_r = qf_local_unreleased[release_dofs]

    k_rr_inv_k_rc = np.linalg.solve(k_rr, k_rc)
    k_cc_mod = k_cc - k_cr @ k_rr_inv_k_rc

    k_rr_inv_qf_r = np.linalg.solve(k_rr, qf_r)
    qf_c_mod = qf_c - k_cr @ k_rr_inv_qf_r

    k_mod = np.zeros((12, 12), dtype=float)
    qf_mod = np.zeros(12, dtype=float)

    for i, I in enumerate(keep_dofs):
        qf_mod[I] = qf_c_mod[i]
        for j, J in enumerate(keep_dofs):
            k_mod[I, J] = k_cc_mod[i, j]

    return k_mod, qf_mod


def k_local_3d_truss(model, elem_id):
    """
    Local 12x12 stiffness matrix for a 3D truss element embedded in the
    12 DOF mixed element format.

    Only the local axial translation DOFs are active.
    """
    basic = get_element_basic_3d_data(model, elem_id)
    material, section = get_element_material_section(model, elem_id)

    E = float(material["E"])
    A = float(section["A"])
    L = basic["L"]

    k = np.zeros((12, 12), dtype=float)
    axial = (E * A / L) * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float)

    k[0, 0] = axial[0, 0]
    k[0, 6] = axial[0, 1]
    k[6, 0] = axial[1, 0]
    k[6, 6] = axial[1, 1]

    return k


def k_global_3d_truss(model, elem_id):
    """
    Global 12x12 stiffness matrix for a 3D truss element.
    """
    basic = get_element_basic_3d_data(model, elem_id)
    k_local = k_local_3d_truss(model, elem_id)
    T = basic["T"]
    k_global = T.T @ k_local @ T
    return k_global


def get_truss_element_stiffness_data(model, elem_id):
    """
    Return basic data plus local and global stiffness matrices for one
    3D truss element.
    """
    basic = get_element_basic_3d_data(model, elem_id)
    k_local = k_local_3d_truss(model, elem_id)
    k_global = k_global_3d_truss(model, elem_id)

    data = {
        **basic,
        "k_local": k_local,
        "k_global": k_global,
    }
    return data


def k_local_3d_frame_unreleased(model, elem_id):
    """
    Unreleased local 12x12 stiffness matrix for a 3D frame element.

    Local DOF order
    [uxi, uyi, uzi, rxi, ryi, rzi, uxj, uyj, uzj, rxj, ryj, rzj]
    """
    basic = get_element_basic_3d_data(model, elem_id)
    material, section = get_element_material_section(model, elem_id)

    E = float(material["E"])
    G = float(material["G"])
    A = float(section["A"])
    Iy = float(section["Iy"])
    Iz = float(section["Iz"])
    J = float(section["J"])
    L = basic["L"]

    k = np.zeros((12, 12), dtype=float)

    a = E * A / L
    k[0, 0] = a
    k[0, 6] = -a
    k[6, 0] = -a
    k[6, 6] = a

    t = G * J / L
    k[3, 3] = t
    k[3, 9] = -t
    k[9, 3] = -t
    k[9, 9] = t

    cz = E * Iz / (L ** 3)
    kz = cz * np.array([
        [12.0,  6.0 * L, -12.0,  6.0 * L],
        [6.0 * L, 4.0 * L * L, -6.0 * L, 2.0 * L * L],
        [-12.0, -6.0 * L, 12.0, -6.0 * L],
        [6.0 * L, 2.0 * L * L, -6.0 * L, 4.0 * L * L],
    ], dtype=float)

    idx_z = [1, 5, 7, 11]
    for i in range(4):
        for j in range(4):
            k[idx_z[i], idx_z[j]] += kz[i, j]

    cy = E * Iy / (L ** 3)
    ky = cy * np.array([
        [12.0, -6.0 * L, -12.0, -6.0 * L],
        [-6.0 * L, 4.0 * L * L, 6.0 * L, 2.0 * L * L],
        [-12.0, 6.0 * L, 12.0, 6.0 * L],
        [-6.0 * L, 2.0 * L * L, 6.0 * L, 4.0 * L * L],
    ], dtype=float)

    idx_y = [2, 4, 8, 10]
    for i in range(4):
        for j in range(4):
            k[idx_y[i], idx_y[j]] += ky[i, j]

    return k


def k_local_3d_frame(model, elem_id):
    """
    Released local 12x12 stiffness matrix for a 3D frame element.

    Current implementation follows the class logic
    MT = 0 normal frame
    MT = 3 both-end full rotational release -> pure axial member

    MT = 1 and MT = 2 still use the current condensation approach for now.
    """
    mt = get_frame_release_case(model, elem_id)

    if mt == 0:
        return k_local_3d_frame_unreleased(model, elem_id)

    if mt == 3:
       
        return k_local_3d_truss(model, elem_id)

    k_unreleased = k_local_3d_frame_unreleased(model, elem_id)
    q_zero = np.zeros(12, dtype=float)
    release_dofs = get_frame_release_dofs_local(model, elem_id)
    k_mod, _ = apply_release_condensation(k_unreleased, q_zero, release_dofs)
    return k_mod


def k_global_3d_frame(model, elem_id):
    """
    Global 12x12 stiffness matrix for a 3D frame element.
    """
    basic = get_element_basic_3d_data(model, elem_id)
    k_local = k_local_3d_frame(model, elem_id)
    T = basic["T"]
    k_global = T.T @ k_local @ T
    return k_global


def get_frame_element_stiffness_data(model, elem_id):
    """
    Return basic data plus local and global stiffness matrices for one
    3D frame element.
    """
    basic = get_element_basic_3d_data(model, elem_id)
    k_local = k_local_3d_frame(model, elem_id)
    k_global = k_global_3d_frame(model, elem_id)

    data = {
        **basic,
        "k_local": k_local,
        "k_global": k_global,
    }
    return data


def get_element_stiffness_data(model, elem_id):
    """
    Dispatch stiffness data generation by element type.
    """
    elem_type = model["elements"][elem_id]["type"]

    if elem_type == "3D_truss":
        return get_truss_element_stiffness_data(model, elem_id)

    if elem_type == "3D_frame":
        return get_frame_element_stiffness_data(model, elem_id)

    raise ValueError(f"Unsupported element type '{elem_type}'.")


def q_local_uniform_temperature(model, elem_id, deltaT):
    """
    Local fixed end force vector for a uniform temperature change.

    Current implementation uses the axial thermal strain effect only.
    """
    material, section = get_element_material_section(model, elem_id)

    E = float(material["E"])
    A = float(section["A"])
    alpha = float(material.get("alpha", 0.0))

    Nth = E * A * alpha * float(deltaT)

    qf = np.zeros(12, dtype=float)
    qf[0] = Nth
    qf[6] = -Nth
    return qf


def q_local_fabrication_length_error(model, elem_id, deltaL):
    """
    Local fixed end force vector for fabrication length error.

    Current sign convention
    positive deltaL means the fabricated member is too long
    and must be shortened to fit the structure
    """
    basic = get_element_basic_3d_data(model, elem_id)
    material, section = get_element_material_section(model, elem_id)

    E = float(material["E"])
    A = float(section["A"])
    L = basic["L"]

    Nf = E * A * float(deltaL) / L

    qf = np.zeros(12, dtype=float)
    qf[0] = Nf
    qf[6] = -Nf
    return qf


def q_local_uniform_load_y(model, elem_id, w):
    basic = get_element_basic_3d_data(model, elem_id)
    L = basic["L"]
    w = float(w)

    qf = np.zeros(12, dtype=float)
    qf[1] = -w * L / 2.0
    qf[5] = -w * L * L / 12.0
    qf[7] = -w * L / 2.0
    qf[11] = w * L * L / 12.0
    return qf


def q_local_uniform_load_z(model, elem_id, w):
    basic = get_element_basic_3d_data(model, elem_id)
    L = basic["L"]
    w = float(w)

    qf = np.zeros(12, dtype=float)
    qf[2] =- w * L / 2.0
    qf[4] = w * L * L / 12.0
    qf[8] = -w * L / 2.0
    qf[10] = w * L * L / 12.0
    return qf


 
def get_element_fixed_end_force_local_unreleased(model, elem_id):
    """
    Sum all currently implemented local fixed end force effects for one element
    before any frame release modification.
    """
    qf_local = np.zeros(12, dtype=float)

    for item in model["temperature_loads"]:
        if item["element"] == elem_id:
            qf_local += q_local_uniform_temperature(model, elem_id, item["deltaT"])

    for item in model["fabrication_errors"]:
        if item["element"] == elem_id:
            qf_local += q_local_fabrication_length_error(model, elem_id, item["deltaL"])

    for item in model["member_loads"]:
        if item["element"] == elem_id:
            if item["type"] == "uniform_local_y":
                qf_local += q_local_uniform_load_y(model, elem_id, item["w"])
            elif item["type"] == "uniform_local_z":
                qf_local += q_local_uniform_load_z(model, elem_id, item["w"])
            elif item["type"] == "point_local_y_midspan":
                qf_local += q_local_point_load_y_midspan(model, elem_id, item["P"])
            elif item["type"] == "point_local_z_midspan":
                qf_local += q_local_point_load_z_midspan(model, elem_id, item["P"])
        
    return qf_local


def get_element_fixed_end_force_local(model, elem_id):
    """
    Sum all currently implemented local fixed end force effects for one element
    and apply current frame release logic when needed.
    """
    qf_unreleased = get_element_fixed_end_force_local_unreleased(model, elem_id)
    elem_type = model["elements"][elem_id]["type"]

    if elem_type == "3D_frame":
        mt = get_frame_release_case(model, elem_id)

        if mt == 0:
            return qf_unreleased

        if mt == 3:
           
            return np.zeros(12, dtype=float)

        k_unreleased = k_local_3d_frame_unreleased(model, elem_id)
        release_dofs = get_frame_release_dofs_local(model, elem_id)
        _, qf_mod = apply_release_condensation(k_unreleased, qf_unreleased, release_dofs)
        return qf_mod

    return qf_unreleased

def get_element_fixed_end_force_global(model, elem_id):
    """
    Convert the local fixed end force vector to the global system.
    """
    elem_data = get_element_basic_3d_data(model, elem_id)
    qf_local = get_element_fixed_end_force_local(model, elem_id)
    qf_global = elem_data["T"].T @ qf_local
    return qf_global

def get_frame_release_case(model, elem_id):
    """
    Map the current frame release input to the course release cases.

    MT = 0 no releases
    MT = 1 full rotational release at start
    MT = 2 full rotational release at end
    MT = 3 full rotational release at both ends
    """
    element = model["elements"][elem_id]
    release = element.get("release", {"start": [], "end": []})

    start_set = set(release.get("start", []))
    end_set = set(release.get("end", []))

    start_full = start_set == FULL_RELEASE_SET
    end_full = end_set == FULL_RELEASE_SET

    if not start_full and not end_full:
        return 0
    if start_full and not end_full:
        return 1
    if not start_full and end_full:
        return 2
    return 3



def q_local_point_load_y_midspan(model, elem_id, P):
    basic = get_element_basic_3d_data(model, elem_id)
    L = basic["L"]
    P = float(P)

    qf = np.zeros(12, dtype=float)
    qf[1] = -P / 2.0
    qf[5] =- P * L / 8.0
    qf[7] = -P / 2.0
    qf[11] = P * L / 8.0
    return qf


def q_local_point_load_z_midspan(model, elem_id, P):
    basic = get_element_basic_3d_data(model, elem_id)
    L = basic["L"]
    P = float(P)

    qf = np.zeros(12, dtype=float)
    qf[2] = -P / 2.0
    qf[4] = P * L / 8.0
    qf[8] = -P / 2.0
    qf[10] = P * L / 8.0
   