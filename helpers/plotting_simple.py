from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

try:
    from helpers.elements_3d import get_element_basic_3d_data
except ImportError:
    from elements_3d import get_element_basic_3d_data


def get_node_translation(U, data, node_id):
    """
    Return translational displacement vector [ux, uy, uz] for one node.
    """
    dof_map = data["node_dof_map"][node_id]
    return np.array([
        U[dof_map["ux"]],
        U[dof_map["uy"]],
        U[dof_map["uz"]],
    ], dtype=float)


def get_node_position(model, node_id):
    """
    Return original node position as a NumPy array.
    """
    return np.array(model["nodes"][node_id], dtype=float)


def get_deformed_node_position(model, data, U, node_id, scale=1.0):
    """
    Return deformed node position using translational DOFs only.
    """
    x0 = get_node_position(model, node_id)
    if U is None:
        return x0.copy()

    du = get_node_translation(U, data, node_id)
    return x0 + scale * du


def hermite_shape_functions(xi, L):
    """
    Cubic Hermite shape functions for beam bending.
    """
    H1 = 1.0 - 3.0 * xi**2 + 2.0 * xi**3
    H2 = L * (xi - 2.0 * xi**2 + xi**3)
    H3 = 3.0 * xi**2 - 2.0 * xi**3
    H4 = L * (-xi**2 + xi**3)
    return H1, H2, H3, H4


def sample_deformed_frame_centerline_simple(
    model,
    data,
    U,
    elem_id,
    scale=1.0,
    n_points=21,
):
    """
    Sample a curved deformed centerline for one 3D frame element.

    Uses
    - linear interpolation for axial displacement
    - cubic Hermite interpolation for local y and local z bending

    Note
    - local y displacement uses rotations about local z
    - local z displacement uses rotations about local y
    - torsion does not move the centerline, so rx is ignored here
    """
    elem = model["elements"][elem_id]
    ni, nj = elem["nodes"]

    basic = get_element_basic_3d_data(model, elem_id)
    R = basic["R"]
    T = basic["T"]
    L = basic["L"]
    dof_map = basic["dof_map"]

    x_i_global = np.array(model["nodes"][ni], dtype=float)

    u_global_elem = np.array([U[d] for d in dof_map], dtype=float)
    v_local = T @ u_global_elem

    uxi, uyi, uzi, rxi, ryi, rzi, uxj, uyj, uzj, rxj, ryj, rzj = v_local

    pts = []

    for xi in np.linspace(0.0, 1.0, n_points):
        x0 = L * xi

        # axial interpolation
        N1 = 1.0 - xi
        N2 = xi
        ux = N1 * uxi + N2 * uxj

        # local y bending uses uy and rz
        H1, H2, H3, H4 = hermite_shape_functions(xi, L)
        uy = H1 * uyi + H2 * rzi + H3 * uyj + H4 * rzj

        # local z bending uses uz and ry
        uz = H1 * uzi - H2 * ryi + H3 * uzj - H4 * ryj

        p_local = np.array([
            x0 + scale * ux,
            scale * uy,
            scale * uz,
        ], dtype=float)

        p_global = x_i_global + R.T @ p_local
        pts.append(p_global)

    return np.array(pts, dtype=float)


def select_element_ids(model, data, selector="all"):
    """
    Return a filtered list of element ids.

    selector options
    - "all"
    - "truss"
    - "frame"
    - "bridge_truss"
    - "floor_system"
    - explicit list of element ids
    """
    if isinstance(selector, (list, tuple, set)):
        return [int(eid) for eid in selector]

    selector = str(selector).lower()

    if selector == "all":
        return list(data["element_ids"])

    if selector == "truss":
        return [
            eid for eid in data["element_ids"]
            if model["elements"][eid]["type"] == "3D_truss"
        ]

    if selector == "frame":
        return [
            eid for eid in data["element_ids"]
            if model["elements"][eid]["type"] == "3D_frame"
        ]

    if selector == "bridge_truss":
        return [
            eid for eid in data["element_ids"]
            if model["elements"][eid]["type"] == "3D_truss"
        ]

    if selector == "floor_system":
        return [
            eid for eid in data["element_ids"]
            if model["elements"][eid]["type"] == "3D_frame"
        ]

    raise ValueError(f"Unknown selector '{selector}'.")


def apply_view(ax, view):
    if view == "iso":
        ax.view_init(elev=25, azim=-60)
    elif view == "x":
        ax.view_init(elev=0, azim=-90)
    elif view == "y":
        ax.view_init(elev=0, azim=0)
    elif view == "z":
        ax.view_init(elev=90, azim=-90)
    elif view == "xy":
        ax.view_init(elev=90, azim=-90)
    elif view == "xz":
        ax.view_init(elev=0, azim=-90)
    elif view == "yz":
        ax.view_init(elev=0, azim=0)
    else:
        raise ValueError(f"Unknown view '{view}'.")


def set_plot_extents(ax, model, pad_ratio=0.05, min_span=1.0):
    """
    Set safe 3D limits and aspect ratio.
    """
    xs = []
    ys = []
    zs = []

    for node_id in model["nodes"]:
        x = get_node_position(model, node_id)
        xs.append(x[0])
        ys.append(x[1])
        zs.append(x[2])

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    zmin, zmax = min(zs), max(zs)

    x_range = xmax - xmin
    y_range = ymax - ymin
    z_range = zmax - zmin

    if x_range < min_span:
        xmid = 0.5 * (xmin + xmax)
        xmin = xmid - 0.5 * min_span
        xmax = xmid + 0.5 * min_span
        x_range = min_span
    else:
        pad = pad_ratio * x_range
        xmin -= pad
        xmax += pad
        x_range = xmax - xmin

    if y_range < min_span:
        ymid = 0.5 * (ymin + ymax)
        ymin = ymid - 0.5 * min_span
        ymax = ymid + 0.5 * min_span
        y_range = min_span
    else:
        pad = pad_ratio * y_range
        ymin -= pad
        ymax += pad
        y_range = ymax - ymin

    if z_range < min_span:
        zmid = 0.5 * (zmin + zmax)
        zmin = zmid - 0.5 * min_span
        zmax = zmid + 0.5 * min_span
        z_range = min_span
    else:
        pad = pad_ratio * z_range
        zmin -= pad
        zmax += pad
        z_range = zmax - zmin

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_zlim(zmin, zmax)
    ax.set_box_aspect((x_range, y_range, z_range))


def plot_structure_simple(
    model,
    data,
    U=None,
    scale=1.0,
    selector="all",
    show_undeformed=True,
    show_deformed=True,
    show_node_labels=False,
    show_element_labels=False,
    title=None,
    view="iso",
    undeformed_kwargs=None,
    deformed_kwargs=None,
    save_path=None,
):
    """
    Simple 3D structure plotter for undeformed and deformed geometry.

    Notes
    - undeformed elements are always plotted as straight centerlines
    - deformed 3D truss elements are plotted as straight chords
    - deformed 3D frame elements are plotted with curved centerlines
    """
    element_ids = select_element_ids(model, data, selector=selector)

    if undeformed_kwargs is None:
        undeformed_kwargs = {
            "color": "0.55",
            "linestyle": "-",
            "linewidth": 1.2,
            "alpha": 0.9,
        }

    if deformed_kwargs is None:
        deformed_kwargs = {
            "color": "tab:red",
            "linestyle": "--",
            "linewidth": 2.0,
            "alpha": 0.95,
        }

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    if show_undeformed:
        for elem_id in element_ids:
            elem = model["elements"][elem_id]
            ni, nj = elem["nodes"]

            xi = get_node_position(model, ni)
            xj = get_node_position(model, nj)

            ax.plot(
                [xi[0], xj[0]],
                [xi[1], xj[1]],
                [xi[2], xj[2]],
                **undeformed_kwargs,
            )

    if show_deformed and U is not None:
        for elem_id in element_ids:
            elem = model["elements"][elem_id]
            elem_type = elem["type"]
            ni, nj = elem["nodes"]

            if elem_type == "3D_frame":
                pts = sample_deformed_frame_centerline_simple(
                    model,
                    data,
                    U,
                    elem_id,
                    scale=scale,
                    n_points=21,
                )

                ax.plot(
                    pts[:, 0],
                    pts[:, 1],
                    pts[:, 2],
                    **deformed_kwargs,
                )
            else:
                xi = get_deformed_node_position(model, data, U, ni, scale=scale)
                xj = get_deformed_node_position(model, data, U, nj, scale=scale)

                ax.plot(
                    [xi[0], xj[0]],
                    [xi[1], xj[1]],
                    [xi[2], xj[2]],
                    **deformed_kwargs,
                )

    if show_node_labels:
        for node_id in sorted(model["nodes"].keys()):
            x = get_node_position(model, node_id)
            ax.text(x[0], x[1], x[2], f"{node_id}", fontsize=8)

    if show_element_labels:
        for elem_id in element_ids:
            elem = model["elements"][elem_id]
            ni, nj = elem["nodes"]
            xi = get_node_position(model, ni)
            xj = get_node_position(model, nj)
            xm = 0.5 * (xi + xj)
            ax.text(xm[0], xm[1], xm[2], f"{elem_id}", fontsize=8)

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")

    if title is not None:
        ax.set_title(title)

    apply_view(ax, view)
    set_plot_extents(ax, model)
    ax.grid(True)

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()
    return fig, ax