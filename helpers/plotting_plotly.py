from pathlib import Path

import numpy as np
import plotly.graph_objects as go
try:
    from helpers.elements_3d import get_element_basic_3d_data
except ImportError:
    from elements_3d import get_element_basic_3d_data

def get_node_translation(U, data, node_id):
    dof_map = data["node_dof_map"][node_id]
    return np.array([
        U[dof_map["ux"]],
        U[dof_map["uy"]],
        U[dof_map["uz"]],
    ], dtype=float)


def get_node_position(model, node_id):
    return np.array(model["nodes"][node_id], dtype=float)


def get_deformed_node_position(model, data, U, node_id, scale=1.0):
    x0 = get_node_position(model, node_id)
    if U is None:
        return x0.copy()
    du = get_node_translation(U, data, node_id)
    return x0 + scale * du

def hermite_shape_functions(xi, L):
    H1 = 1.0 - 3.0 * xi**2 + 2.0 * xi**3
    H2 = L * (xi - 2.0 * xi**2 + xi**3)
    H3 = 3.0 * xi**2 - 2.0 * xi**3
    H4 = L * (-xi**2 + xi**3)
    return H1, H2, H3, H4


def sample_deformed_frame_centerline(model, data, U, elem_id, scale=1.0, n_points=21):
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

    x_i_global = get_node_position(model, ni)

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


def build_line_trace(
    model,
    data,
    U=None,
    scale=1.0,
    element_ids=None,
    name="shape",
    color="gray",
    dash="solid",
    width=4,
    frame_curve_points=21,
):
    xs = []
    ys = []
    zs = []

    for elem_id in element_ids:
        elem = model["elements"][elem_id]
        elem_type = elem["type"]
        ni, nj = elem["nodes"]

        # Curved deformed plotting for frame elements only
        if U is not None and elem_type == "3D_frame":
            pts = sample_deformed_frame_centerline(
                model,
                data,
                U,
                elem_id,
                scale=scale,
                n_points=frame_curve_points,
            )

            for p in pts:
                xs.append(p[0])
                ys.append(p[1])
                zs.append(p[2])

            xs.append(None)
            ys.append(None)
            zs.append(None)

        else:
            # Straight line for undeformed geometry and all truss members
            if U is None:
                xi = get_node_position(model, ni)
                xj = get_node_position(model, nj)
            else:
                xi = get_deformed_node_position(model, data, U, ni, scale=scale)
                xj = get_deformed_node_position(model, data, U, nj, scale=scale)

            xs.extend([xi[0], xj[0], None])
            ys.extend([xi[1], xj[1], None])
            zs.extend([xi[2], xj[2], None])

    return go.Scatter3d(
        x=xs,
        y=ys,
        z=zs,
        mode="lines",
        name=name,
        hoverinfo="skip",
        line=dict(color=color, width=width, dash=dash),
    )


def build_element_hover_trace(model, data, U=None, scale=1.0, element_ids=None, name="element info"):
    xm = []
    ym = []
    zm = []
    texts = []

    for elem_id in element_ids:
        elem = model["elements"][elem_id]
        ni, nj = elem["nodes"]

        if U is None:
            xi = get_node_position(model, ni)
            xj = get_node_position(model, nj)
        else:
            xi = get_deformed_node_position(model, data, U, ni, scale=scale)
            xj = get_deformed_node_position(model, data, U, nj, scale=scale)

        xc = 0.5 * (xi + xj)

        xm.append(xc[0])
        ym.append(xc[1])
        zm.append(xc[2])

        texts.append(
            f"Element {elem_id}<br>"
            f"type = {elem['type']}<br>"
            f"nodes = {elem['nodes'][0]} to {elem['nodes'][1]}<br>"
            f"section = {elem['section']}"
        )

    return go.Scatter3d(
        x=xm,
        y=ym,
        z=zm,
        mode="markers",
        name=name,
        marker=dict(size=5, color="black", opacity=0.35),
        text=texts,
        hovertemplate="%{text}<extra></extra>",
    )


def build_node_trace(model, data, U=None, scale=1.0, node_ids=None, name="nodes", color="black", size=4):
    x = []
    y = []
    z = []
    texts = []

    for node_id in node_ids:
        if U is None:
            xi = get_node_position(model, node_id)
        else:
            xi = get_deformed_node_position(model, data, U, node_id, scale=scale)

        x.append(xi[0])
        y.append(xi[1])
        z.append(xi[2])

        texts.append(f"Node {node_id}")

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="markers",
        name=name,
        marker=dict(size=size, color=color),
        text=texts,
        hovertemplate="%{text}<extra></extra>",
    )


def build_node_label_trace(model, data, U=None, scale=1.0, node_ids=None, name="node labels"):
    x = []
    y = []
    z = []
    texts = []

    for node_id in node_ids:
        if U is None:
            xi = get_node_position(model, node_id)
        else:
            xi = get_deformed_node_position(model, data, U, node_id, scale=scale)

        x.append(xi[0])
        y.append(xi[1])
        z.append(xi[2])
        texts.append(str(node_id))

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="text",
        name=name,
        text=texts,
        textposition="top center",
        hoverinfo="skip",
    )
def build_vector_line_and_tip_traces(
    starts,
    vectors,
    texts,
    name,
    color="blue",
    shaft_width=6,
    tip_size=6,
):
    """
    Build Plotly 3D vector traces using line shafts plus cone tips.
    """
    if len(starts) == 0:
        return []

    xs = []
    ys = []
    zs = []

    tip_x = []
    tip_y = []
    tip_z = []
    tip_u = []
    tip_v = []
    tip_w = []
    tip_text = []

    for start, vec, text in zip(starts, vectors, texts):
        end = start + vec

        xs.extend([start[0], end[0], None])
        ys.extend([start[1], end[1], None])
        zs.extend([start[2], end[2], None])

        tip_x.append(end[0])
        tip_y.append(end[1])
        tip_z.append(end[2])

        tip_u.append(vec[0])
        tip_v.append(vec[1])
        tip_w.append(vec[2])

        tip_text.append(text)

    line_trace = go.Scatter3d(
        x=xs,
        y=ys,
        z=zs,
        mode="lines",
        name=name,
        hoverinfo="skip",
        line=dict(color=color, width=shaft_width),
    )

    cone_trace = go.Cone(
        x=tip_x,
        y=tip_y,
        z=tip_z,
        u=tip_u,
        v=tip_v,
        w=tip_w,
        name=f"{name} tips",
        text=tip_text,
        hovertemplate="%{text}<extra></extra>",
        colorscale=[[0, color], [1, color]],
        showscale=False,
        sizemode="absolute",
        sizeref=tip_size,
        anchor="tail",
    )

    return [line_trace, cone_trace]


def build_nodal_load_traces(model, data, load_scale=100.0, color="blue"):
    """
    Build translational nodal load arrow traces.
    Rotational nodal loads are ignored in this first version.
    """
    starts = []
    vectors = []
    texts = []

    for item in model["nodal_loads"]:
        node_id = item["node"]
        vals = np.array(item["values"][:3], dtype=float)

        if np.linalg.norm(vals) <= 0.0:
            continue

        start = get_node_position(model, node_id)
        vec = load_scale * vals

        starts.append(start)
        vectors.append(vec)
        texts.append(
            f"Nodal load at node {node_id}<br>"
            f"Fx = {vals[0]}<br>"
            f"Fy = {vals[1]}<br>"
            f"Fz = {vals[2]}"
        )

    return build_vector_line_and_tip_traces(
        starts,
        vectors,
        texts,
        name="nodal loads",
        color=color,
        shaft_width=7,
        tip_size=4,
    )


def build_reaction_traces(model, data, R, reaction_scale=1.0, color="green", tol=1e-12):
    """
    Build translational support reaction arrow traces from the global residual vector.
    Rotational reactions are ignored in this first version.
    """
    starts = []
    vectors = []
    texts = []

    for node_id in sorted(model["supports"].keys()):
        dof_map = data["node_dof_map"][node_id]

        vals = np.array([
            R[dof_map["ux"]],
            R[dof_map["uy"]],
            R[dof_map["uz"]],
        ], dtype=float)

        if np.linalg.norm(vals) <= tol:
            continue

        start = get_node_position(model, node_id)
        vec = reaction_scale * vals

        starts.append(start)
        vectors.append(vec)
        texts.append(
            f"Reaction at node {node_id}<br>"
            f"Rx = {vals[0]}<br>"
            f"Ry = {vals[1]}<br>"
            f"Rz = {vals[2]}"
        )

    return build_vector_line_and_tip_traces(
        starts,
        vectors,
        texts,
        name="reactions",
        color=color,
        shaft_width=7,
        tip_size=4,
    )

def get_member_load_global_vector(model, elem_id, item):
    """
    Convert a supported member load direction to a global vector.

    Returns
    v_global
        3-component global direction vector scaled by the load magnitude
    load_family
        "uniform" or "point_midspan"
    magnitude_label
        "w" or "P"
    magnitude_value
        numeric value of the load
    """
    elem_data = get_element_basic_3d_data(model, elem_id)
    R = elem_data["R"]

    load_type = item["type"]

    if load_type == "uniform_local_y":
        magnitude_value = float(item["w"])
        v_local = np.array([0.0, magnitude_value, 0.0], dtype=float)
        load_family = "uniform"
        magnitude_label = "w"

    elif load_type == "uniform_local_z":
        magnitude_value = float(item["w"])
        v_local = np.array([0.0, 0.0, magnitude_value], dtype=float)
        load_family = "uniform"
        magnitude_label = "w"

    elif load_type == "point_local_y_midspan":
        magnitude_value = float(item["P"])
        v_local = np.array([0.0, magnitude_value, 0.0], dtype=float)
        load_family = "point_midspan"
        magnitude_label = "P"

    elif load_type == "point_local_z_midspan":
        magnitude_value = float(item["P"])
        v_local = np.array([0.0, 0.0, magnitude_value], dtype=float)
        load_family = "point_midspan"
        magnitude_label = "P"

    else:
        return None, None, None, None

    v_global = R.T @ v_local
    return v_global, load_family, magnitude_label, magnitude_value


def build_member_load_traces(
    model,
    data,
    selector_element_ids,
    member_load_scale=1.0,
    n_arrows=5,
    color="purple",
):
    """
    Build member load arrows for supported uniform and midpoint point loads.
    """
    traces = []
    selector_set = set(selector_element_ids)

    for item in model["member_loads"]:
        elem_id = item["element"]

        if elem_id not in selector_set:
            continue

        v_global, load_family, magnitude_label, magnitude_value = get_member_load_global_vector(
            model, elem_id, item
        )
        if v_global is None:
            continue

        elem = model["elements"][elem_id]
        ni, nj = elem["nodes"]
        xi = get_node_position(model, ni)
        xj = get_node_position(model, nj)

        if load_family == "uniform":
            sample_points = np.linspace(0.1, 0.9, n_arrows)
        elif load_family == "point_midspan":
            sample_points = [0.5]
        else:
            continue

        for s in sample_points:
            start = (1.0 - s) * xi + s * xj
            vec = member_load_scale * v_global
            end = start + vec

            text = (
                f"Member load on element {elem_id}<br>"
                f"type = {item['type']}<br>"
                f"{magnitude_label} = {magnitude_value}"
            )

            traces.append(
                go.Scatter3d(
                    x=[start[0], end[0]],
                    y=[start[1], end[1]],
                    z=[start[2], end[2]],
                    mode="lines",
                    line=dict(color=color, width=6),
                    text=[text, text],
                    hovertemplate="%{text}<extra></extra>",
                    showlegend=False,
                )
            )

    return traces


def plot_structure_plotly(
    model,
    data,
    U=None,
    scale=1.0,
    selector="all",
    show_undeformed=True,
    show_deformed=True,
    show_nodes=False,
    show_node_labels=False,
    show_element_hover=True,
    show_nodal_loads=False,
    show_reactions=False,
    show_member_loads=False,
    R=None,
    load_scale=1.0,
    reaction_scale=1.0,
    member_load_scale=1.0,
    title="Structure plot",
    save_html=None,
    save_png=None,
):
    element_ids = select_element_ids(model, data, selector=selector)
    node_ids = sorted(model["nodes"].keys())

    fig = go.Figure()

    if show_undeformed:
        fig.add_trace(
            build_line_trace(
                model,
                data,
                U=None,
                scale=1.0,
                element_ids=element_ids,
                name="undeformed",
                color="gray",
                dash="solid",
                width=4,
            )
        )

    if show_deformed and U is not None:
        fig.add_trace(
            build_line_trace(
                model,
                data,
                U=U,
                scale=scale,
                element_ids=element_ids,
                name="deformed",
                color="red",
                dash="solid",
                width=5,
            )
        )

    if show_element_hover:
        fig.add_trace(
            build_element_hover_trace(
                model,
                data,
                U=None,
                scale=1.0,
                element_ids=element_ids,
                name="element info",
            )
        )

    if show_nodes:
        fig.add_trace(
            build_node_trace(
                model,
                data,
                U=None,
                scale=1.0,
                node_ids=node_ids,
                name="nodes",
                color="black",
                size=3,
            )
        )

    if show_node_labels:
        fig.add_trace(
            build_node_label_trace(
                model,
                data,
                U=None,
                scale=1.0,
                node_ids=node_ids,
                name="node labels",
            )
        )
    if show_nodal_loads:
        for tr in build_nodal_load_traces(
            model,
            data,
            load_scale=load_scale,
            color="blue",
        ):
            fig.add_trace(tr)
    if show_member_loads:
        for tr in build_member_load_traces(
            model,
            data,
            selector_element_ids=element_ids,
            member_load_scale=member_load_scale,
            n_arrows=5,
            color="purple",
        ):
            fig.add_trace(tr)          

    if show_reactions:
        if R is None:
            raise ValueError("R must be provided when show_reactions=True.")
        for tr in build_reaction_traces(
            model,
            data,
            R=R,
            reaction_scale=reaction_scale,
            color="green",
        ):
            fig.add_trace(tr)

    fig.update_layout(
        title=title,
        showlegend=True,
        scene=dict(
            xaxis_title="x",
            yaxis_title="y",
            zaxis_title="z",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    if save_html is not None:
        save_html = Path(save_html)
        save_html.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(save_html))

    if save_png is not None:
        save_png = Path(save_png)
        save_png.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig.write_image(str(save_png), width=1400, height=900, scale=2)
        except Exception as e:
            print(f"PNG export skipped due to Kaleido error: {e}")
    return fig

import plotly.graph_objects as go
from pathlib import Path
import numpy as np


def build_displacement_node_trace(model, data, U, scale=1.0, name="displacement contour"):
    x = []
    y = []
    z = []
    color_vals = []
    texts = []

    for node_id in sorted(model["nodes"].keys(), key=lambda k: int(k)):
        xyz0 = np.array(model["nodes"][node_id], dtype=float)
        dof_map = data["node_dof_map"][node_id]

        ux = float(U[dof_map["ux"]])
        uy = float(U[dof_map["uy"]])
        uz = float(U[dof_map["uz"]])

        disp_mag = float(np.sqrt(ux**2 + uy**2 + uz**2))
        xyz = xyz0 + scale * np.array([ux, uy, uz], dtype=float)

        x.append(xyz[0])
        y.append(xyz[1])
        z.append(xyz[2])
        color_vals.append(disp_mag)
        texts.append(
            f"Node {node_id}<br>"
            f"ux = {ux}<br>"
            f"uy = {uy}<br>"
            f"uz = {uz}<br>"
            f"|u| = {disp_mag}"
        )

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="markers",
        name=name,
        text=texts,
        hovertemplate="%{text}<extra></extra>",
        marker=dict(
            size=6,
            color=color_vals,
            colorscale="Viridis",
            colorbar=dict(title="|u|"),
            showscale=True,
        ),
    )


def plot_displacement_contour_plotly(
    model,
    data,
    U,
    scale=1.0,
    selector="all",
    title="Displacement contour",
    save_html=None,
    save_png=None,
):
    element_ids = select_element_ids(model, data, selector=selector)

    fig = go.Figure()

    fig.add_trace(
        build_line_trace(
            model,
            data,
            U=None,
            scale=1.0,
            element_ids=element_ids,
            name="undeformed",
            color="lightgray",
            dash="solid",
            width=4,
        )
    )

    fig.add_trace(
        build_line_trace(
            model,
            data,
            U=U,
            scale=scale,
            element_ids=element_ids,
            name="deformed",
            color="gray",
            dash="solid",
            width=5,
        )
    )

    fig.add_trace(
        build_displacement_node_trace(
            model=model,
            data=data,
            U=U,
            scale=scale,
            name="displacement contour",
        )
    )

    fig.update_layout(
        title=title,
        showlegend=True,
        scene=dict(
            xaxis_title="x",
            yaxis_title="y",
            zaxis_title="z",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    if save_html is not None:
        save_html = Path(save_html)
        save_html.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(save_html))

    if save_png is not None:
        save_png = Path(save_png)
        save_png.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig.write_image(str(save_png), width=1400, height=900, scale=2)
        except Exception as e:
            print(f"PNG export skipped due to Kaleido error {e}")

    return fig

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from pathlib import Path


def _value_to_color(value, vmin, vmax, colorscale="Viridis"):
    if vmax <= vmin:
        t = 0.5
    else:
        t = (value - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, t))
    return sample_colorscale(colorscale, [t])[0]


def build_colored_element_traces(
    model,
    data,
    U,
    scale,
    element_ids,
    element_value_map,
    value_label="value",
    colorscale="Viridis",
    default_color="lightgray",
    width=8,
):
    traces = []

    if len(element_value_map) == 0:
        vmin = 0.0
        vmax = 1.0
    else:
        vals = list(element_value_map.values())
        vmin = min(vals)
        vmax = max(vals)

    for elem_id in element_ids:
        elem = model["elements"][elem_id]
        ni, nj = elem["nodes"]

        xi = np.array(model["nodes"][ni], dtype=float)
        xj = np.array(model["nodes"][nj], dtype=float)

        if U is None:
            pi = xi
            pj = xj
        else:
            dof_i = data["node_dof_map"][ni]
            dof_j = data["node_dof_map"][nj]

            ui = np.array([
                float(U[dof_i["ux"]]),
                float(U[dof_i["uy"]]),
                float(U[dof_i["uz"]]),
            ])
            uj = np.array([
                float(U[dof_j["ux"]]),
                float(U[dof_j["uy"]]),
                float(U[dof_j["uz"]]),
            ])

            pi = xi + scale * ui
            pj = xj + scale * uj

      
        elem_key = str(elem_id)
        value = element_value_map.get(elem_key, element_value_map.get(elem_id, None))

        if value is None:
            color = default_color
            text = f"Element {elem_id}<br>{value_label} = n/a"
        else:
            color = _value_to_color(value, vmin, vmax, colorscale=colorscale)
            text = f"Element {elem_id}<br>{value_label} = {value}"

        traces.append(
            go.Scatter3d(
                x=[pi[0], pj[0]],
                y=[pi[1], pj[1]],
                z=[pi[2], pj[2]],
                mode="lines",
                line=dict(color=color, width=width),
                name=f"{elem_id}",
                text=[text, text],
                hovertemplate="%{text}<extra></extra>",
                showlegend=False,
            )
        )

    return traces


def plot_member_response_highlight_plotly(
    model,
    data,
    U,
    element_value_map,
    scale=1.0,
    selector="all",
    title="Member response highlight",
    value_label="value",
    colorscale="Viridis",
    save_html=None,
    save_png=None,
):
    element_ids = select_element_ids(model, data, selector=selector)

    fig = go.Figure()

    fig.add_trace(
        build_line_trace(
            model,
            data,
            U=None,
            scale=1.0,
            element_ids=element_ids,
            name="undeformed",
            color="lightgray",
            dash="solid",
            width=4,
        )
    )

    colored_traces = build_colored_element_traces(
        model=model,
        data=data,
        U=U,
        scale=scale,
        element_ids=element_ids,
        element_value_map=element_value_map,
        value_label=value_label,
        colorscale=colorscale,
        default_color="lightgray",
        width=8,
    )

    for tr in colored_traces:
        fig.add_trace(tr)

    if len(element_value_map) > 0:
        vals = list(element_value_map.values())
        vmin = min(vals)
        vmax = max(vals)
    else:
        vmin = 0.0
        vmax = 1.0

    fig.add_trace(
        go.Scatter3d(
            x=[None],
            y=[None],
            z=[None],
            mode="markers",
            marker=dict(
                size=0.1,
                color=[vmin, vmax],
                colorscale=colorscale,
                showscale=True,
                colorbar=dict(title=value_label),
            ),
            hoverinfo="none",
            showlegend=False,
        )
    )

    fig.update_layout(
        title=title,
        showlegend=True,
        scene=dict(
            xaxis_title="x",
            yaxis_title="y",
            zaxis_title="z",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    if save_html is not None:
        save_html = Path(save_html)
        save_html.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(save_html))

    if save_png is not None:
        save_png = Path(save_png)
        save_png.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig.write_image(str(save_png), width=1400, height=900, scale=2)
        except Exception as e:
            print(f"PNG export skipped due to Kaleido error {e}")

    return fig