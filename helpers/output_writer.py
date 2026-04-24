from pathlib import Path
from datetime import datetime
import json
import math
import pandas as pd


def _sorted_int_keys(d):
    return sorted(d.keys(), key=lambda x: int(x))


def _node_xyz(clean_model, node_id):
    xyz = clean_model["nodes"][node_id]
    return float(xyz[0]), float(xyz[1]), float(xyz[2])


def _element_length(clean_model, elem):
    ni, nj = elem["nodes"]
    xi, yi, zi = _node_xyz(clean_model, ni)
    xj, yj, zj = _node_xyz(clean_model, nj)
    return math.sqrt((xj - xi) ** 2 + (yj - yi) ** 2 + (zj - zi) ** 2)


def _safe_float(v):
    if v is None:
        return 0.0
    return float(v)


def _vector12(vec):
    if vec is None:
        return [0.0] * 12
    return [float(x) for x in vec]


def build_model_summary_rows(clean_model, summary, node_rows):
    max_node = None
    max_disp = -1.0

    for row in node_rows:
        if row["disp_mag"] > max_disp:
            max_disp = row["disp_mag"]
            max_node = row["node_id"]

    return [{
        "model_name": summary["model_name"],
        "length_unit": clean_model.get("units", {}).get("length", ""),
        "force_unit": clean_model.get("units", {}).get("force", ""),
        "n_nodes": summary.get("n_nodes"),
        "n_elements": summary.get("n_elements"),
        "n_truss_elements": summary.get("n_truss_elements"),
        "n_frame_elements": summary.get("n_frame_elements"),
        "n_free_dofs": summary.get("n_free_dofs"),
        "n_restrained_dofs": summary.get("n_restrained_dofs"),
        "max_displacement_node": max_node,
        "max_displacement_magnitude": max_disp,
    }]


def build_dof_summary_obj(data, summary, clean_model):
    return {
        "model_name": summary["model_name"],
        "ndof_total": data.get("ndof_total"),
        "free_dofs": data.get("free_dofs", []),
        "restrained_dofs": data.get("restrained_dofs", []),
        "n_free_dofs": summary.get("n_free_dofs"),
        "n_restrained_dofs": summary.get("n_restrained_dofs"),
        "prescribed_displacements": clean_model.get("prescribed_displacements", []),
    }


def build_nodal_load_rows(clean_model):
    rows = []

    for item in clean_model.get("nodal_loads", []):
        vals = item["values"]
        rows.append({
            "node_id": item["node"],
            "Fx": float(vals[0]),
            "Fy": float(vals[1]),
            "Fz": float(vals[2]),
            "Mx": float(vals[3]),
            "My": float(vals[4]),
            "Mz": float(vals[5]),
        })

    return rows


def build_node_displacement_rows(clean_model, data, U):
    rows = []

    for node_id in _sorted_int_keys(clean_model["nodes"]):
        x, y, z = _node_xyz(clean_model, node_id)
        dof_map = data["node_dof_map"][node_id]

        ux = float(U[dof_map["ux"]])
        uy = float(U[dof_map["uy"]])
        uz = float(U[dof_map["uz"]])
        rx = float(U[dof_map["rx"]])
        ry = float(U[dof_map["ry"]])
        rz = float(U[dof_map["rz"]])

        disp_mag = math.sqrt(ux ** 2 + uy ** 2 + uz ** 2)
        rot_mag = math.sqrt(rx ** 2 + ry ** 2 + rz ** 2)

        rows.append({
            "node_id": node_id,
            "x": x,
            "y": y,
            "z": z,
            "ux": ux,
            "uy": uy,
            "uz": uz,
            "rx": rx,
            "ry": ry,
            "rz": rz,
            "disp_mag": disp_mag,
            "rot_mag": rot_mag,
        })

    return rows


def build_support_reaction_rows(clean_model, data, R):
    rows = []

    support_nodes = _sorted_int_keys(clean_model["supports"])

    for node_id in support_nodes:
        x, y, z = _node_xyz(clean_model, node_id)
        dof_map = data["node_dof_map"][node_id]
        restrained_labels = set(clean_model["supports"][node_id])

        Rx = float(R[dof_map["ux"]]) if "ux" in restrained_labels else 0.0
        Ry = float(R[dof_map["uy"]]) if "uy" in restrained_labels else 0.0
        Rz = float(R[dof_map["uz"]]) if "uz" in restrained_labels else 0.0
        Mx = float(R[dof_map["rx"]]) if "rx" in restrained_labels else 0.0
        My = float(R[dof_map["ry"]]) if "ry" in restrained_labels else 0.0
        Mz = float(R[dof_map["rz"]]) if "rz" in restrained_labels else 0.0

        reaction_force_mag = math.sqrt(Rx ** 2 + Ry ** 2 + Rz ** 2)
        reaction_moment_mag = math.sqrt(Mx ** 2 + My ** 2 + Mz ** 2)

        rows.append({
            "node_id": node_id,
            "x": x,
            "y": y,
            "z": z,
            "Rx": Rx,
            "Ry": Ry,
            "Rz": Rz,
            "Mx": Mx,
            "My": My,
            "Mz": Mz,
            "reaction_force_mag": reaction_force_mag,
            "reaction_moment_mag": reaction_moment_mag,
        })

    return rows

def build_element_basic_data_rows(clean_model):
    rows = []

    for elem_id in _sorted_int_keys(clean_model["elements"]):
        elem = clean_model["elements"][elem_id]
        ni, nj = elem["nodes"]

        material_name = elem["material"]
        section_name = elem["section"]

        material = clean_model["materials"][material_name]
        section = clean_model["sections"][section_name]

        rows.append({
            "elem_id": elem_id,
            "type": elem["type"],
            "node_i": ni,
            "node_j": nj,
            "material": material_name,
            "section": section_name,
            "L": _element_length(clean_model, elem),
            "E": _safe_float(material.get("E")),
            "G": _safe_float(material.get("G")),
            "alpha": _safe_float(material.get("alpha")),
            "A": _safe_float(section.get("A")),
            "Iy": _safe_float(section.get("Iy")),
            "Iz": _safe_float(section.get("Iz")),
            "J": _safe_float(section.get("J")),
        })

    return rows


def build_element_local_displacement_rows(clean_model, package):
    rows = []

    for resp in package["element_responses"]:
        elem_id = resp["elem_id"]
        elem = clean_model["elements"][elem_id]
        ni, nj = elem["nodes"]
        u = _vector12(resp.get("u_local_elem"))

        rows.append({
            "elem_id": elem_id,
            "type": resp["type"],
            "node_i": ni,
            "node_j": nj,
            "ux_i_local": u[0],
            "uy_i_local": u[1],
            "uz_i_local": u[2],
            "rx_i_local": u[3],
            "ry_i_local": u[4],
            "rz_i_local": u[5],
            "ux_j_local": u[6],
            "uy_j_local": u[7],
            "uz_j_local": u[8],
            "rx_j_local": u[9],
            "ry_j_local": u[10],
            "rz_j_local": u[11],
        })

    return rows


def build_element_local_end_force_rows(clean_model, package):
    rows = []

    for resp in package["element_responses"]:
        elem_id = resp["elem_id"]
        elem = clean_model["elements"][elem_id]
        ni, nj = elem["nodes"]
        q = _vector12(resp.get("q_local_elem"))

        rows.append({
            "elem_id": elem_id,
            "type": resp["type"],
            "node_i": ni,
            "node_j": nj,
            "Fx_i_local": q[0],
            "Fy_i_local": q[1],
            "Fz_i_local": q[2],
            "Mx_i_local": q[3],
            "My_i_local": q[4],
            "Mz_i_local": q[5],
            "Fx_j_local": q[6],
            "Fy_j_local": q[7],
            "Fz_j_local": q[8],
            "Mx_j_local": q[9],
            "My_j_local": q[10],
            "Mz_j_local": q[11],
        })

    return rows


def build_element_global_end_force_rows(clean_model, package):
    rows = []

    for resp in package["element_responses"]:
        elem_id = resp["elem_id"]
        elem = clean_model["elements"][elem_id]
        ni, nj = elem["nodes"]
        q = _vector12(resp.get("q_global_elem"))

        rows.append({
            "elem_id": elem_id,
            "type": resp["type"],
            "node_i": ni,
            "node_j": nj,
            "Fx_i_global": q[0],
            "Fy_i_global": q[1],
            "Fz_i_global": q[2],
            "Mx_i_global": q[3],
            "My_i_global": q[4],
            "Mz_i_global": q[5],
            "Fx_j_global": q[6],
            "Fy_j_global": q[7],
            "Fz_j_global": q[8],
            "Mx_j_global": q[9],
            "My_j_global": q[10],
            "Mz_j_global": q[11],
        })

    return rows


def build_element_derived_rows(clean_model, package):
    rows = []

    for resp in package["element_responses"]:
        elem_id = resp["elem_id"]
        elem = clean_model["elements"][elem_id]
        ni, nj = elem["nodes"]
        q = _vector12(resp.get("q_local_elem"))

        section = clean_model["sections"][elem["section"]]
        A = _safe_float(section.get("A"))
        L = _element_length(clean_model, elem)

        axial_i = q[0]
        axial_j = q[6]

        axial_abs_max = max(abs(axial_i), abs(axial_j))
        shear_y_abs_max = max(abs(q[1]), abs(q[7]))
        shear_z_abs_max = max(abs(q[2]), abs(q[8]))
        torsion_abs_max = max(abs(q[3]), abs(q[9]))
        moment_y_abs_max = max(abs(q[4]), abs(q[10]))
        moment_z_abs_max = max(abs(q[5]), abs(q[11]))
        moment_abs_max = max(moment_y_abs_max, moment_z_abs_max)

        if A > 0.0:
            stress_axial_i = axial_i / A
            stress_axial_j = axial_j / A
            stress_axial_abs_max = max(abs(stress_axial_i), abs(stress_axial_j))
        else:
            stress_axial_i = 0.0
            stress_axial_j = 0.0
            stress_axial_abs_max = 0.0

        rows.append({
            "elem_id": elem_id,
            "type": resp["type"],
            "node_i": ni,
            "node_j": nj,
            "L": L,
            "axial_i_local": axial_i,
            "axial_j_local": axial_j,
            "axial_abs_max": axial_abs_max,
            "shear_y_abs_max": shear_y_abs_max,
            "shear_z_abs_max": shear_z_abs_max,
            "torsion_abs_max": torsion_abs_max,
            "moment_y_abs_max": moment_y_abs_max,
            "moment_z_abs_max": moment_z_abs_max,
            "moment_abs_max": moment_abs_max,
            "stress_axial_i": stress_axial_i,
            "stress_axial_j": stress_axial_j,
            "stress_axial_abs_max": stress_axial_abs_max,
        })

    return rows

def build_global_summary(clean_model, summary, node_rows, element_derived_rows):
    max_node = None
    max_disp = -1.0

    for row in node_rows:
        if row["disp_mag"] > max_disp:
            max_disp = row["disp_mag"]
            max_node = row["node_id"]

    truss_items = []
    frame_items = []

    for row in element_derived_rows:
        if row["type"] == "3D_truss":
            truss_items.append({
                "elem_id": row["elem_id"],
                "axial_abs_max": row["axial_abs_max"],
                "stress_axial_abs_max": row["stress_axial_abs_max"],
            })
        elif row["type"] == "3D_frame":
            frame_items.append({
                "elem_id": row["elem_id"],
                "moment_abs_max": row["moment_abs_max"],
                "moment_y_abs_max": row["moment_y_abs_max"],
                "moment_z_abs_max": row["moment_z_abs_max"],
            })

    truss_items.sort(key=lambda x: x["axial_abs_max"], reverse=True)
    frame_items.sort(key=lambda x: x["moment_abs_max"], reverse=True)

    return {
        "model_name": summary["model_name"],
        "units": clean_model.get("units", {}),
        "n_nodes": summary.get("n_nodes"),
        "n_elements": summary.get("n_elements"),
        "n_truss_elements": summary.get("n_truss_elements"),
        "n_frame_elements": summary.get("n_frame_elements"),
        "n_free_dofs": summary.get("n_free_dofs"),
        "n_restrained_dofs": summary.get("n_restrained_dofs"),
        "max_displacement_node": max_node,
        "max_displacement_magnitude": max_disp,
        "top_truss_members": truss_items[:5],
        "top_frame_members": frame_items[:5],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

def write_json(obj, filepath):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def write_summary_md(clean_model, summary_obj, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Run summary")
    lines.append("")
    lines.append("## Model")
    lines.append(f"- model name  `{summary_obj['model_name']}`")
    lines.append("")
    lines.append("## Units")
    for k, v in summary_obj["units"].items():
        lines.append(f"- {k}  `{v}`")
    lines.append("")
    lines.append("## Model size")
    lines.append(f"- nodes  {summary_obj['n_nodes']}")
    lines.append(f"- elements  {summary_obj['n_elements']}")
    lines.append(f"- truss elements  {summary_obj['n_truss_elements']}")
    lines.append(f"- frame elements  {summary_obj['n_frame_elements']}")
    lines.append(f"- free DOFs  {summary_obj['n_free_dofs']}")
    lines.append(f"- restrained DOFs  {summary_obj['n_restrained_dofs']}")
    lines.append("")
    lines.append("## Maximum displacement")
    lines.append(f"- node  {summary_obj['max_displacement_node']}")
    lines.append(f"- magnitude  {summary_obj['max_displacement_magnitude']}")
    lines.append("")
    lines.append("## Saved files")
    lines.append("- `global_summary.json`")
    lines.append("- `dof_summary.json`")
    lines.append("- `nodal_loads.csv`")
    lines.append("- `node_displacements.csv`")
    lines.append("- `support_reactions.csv`")
    lines.append("- `element_basic_data.csv`")
    lines.append("- `element_local_displacements.csv`")
    lines.append("- `element_local_end_forces.csv`")
    lines.append("- `element_global_end_forces.csv`")
    lines.append("- `element_derived_results.csv`")
    lines.append("- `run_log.txt`")
    lines.append("")

    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_run_log(clean_model, model_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("Run log")
    lines.append("")
    lines.append(f"timestamp  {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"model_name  {clean_model.get('model_name', 'unknown')}")
    lines.append(f"model_path  {model_path}")
    lines.append(f"output_folder  {output_dir}")

    (output_dir / "run_log.txt").write_text("\n".join(lines), encoding="utf-8")


def build_output_tables(clean_model, data, summary, package):
    U = package["results"]["U"]
    R = package["results"]["R"]

    nodal_load_rows = build_nodal_load_rows(clean_model)
    node_rows = build_node_displacement_rows(clean_model, data, U)
    reaction_rows = build_support_reaction_rows(clean_model, data, R)
    element_basic_rows = build_element_basic_data_rows(clean_model)
    element_local_disp_rows = build_element_local_displacement_rows(clean_model, package)
    element_local_force_rows = build_element_local_end_force_rows(clean_model, package)
    element_global_force_rows = build_element_global_end_force_rows(clean_model, package)
    element_derived_rows = build_element_derived_rows(clean_model, package)
    model_summary_rows = build_model_summary_rows(clean_model, summary, node_rows)

    global_summary = build_global_summary(
        clean_model, summary, node_rows, element_derived_rows
    )
    dof_summary = build_dof_summary_obj(data, summary, clean_model)

    tables = {
        "model_summary": pd.DataFrame(model_summary_rows),
        "nodal_loads": pd.DataFrame(nodal_load_rows),
        "node_displacements": pd.DataFrame(node_rows),
        "support_reactions": pd.DataFrame(reaction_rows),
        "element_basic_data": pd.DataFrame(element_basic_rows),
        "element_local_displacements": pd.DataFrame(element_local_disp_rows),
        "element_local_end_forces": pd.DataFrame(element_local_force_rows),
        "element_global_end_forces": pd.DataFrame(element_global_force_rows),
        "element_derived_results": pd.DataFrame(element_derived_rows),
    }

    return tables, global_summary, dof_summary


def write_run_outputs(clean_model, data, summary, package, model_path="unknown", output_root="outputs/runs"):
    model_name = summary["model_name"]
    output_dir = Path(output_root) / model_name
    output_dir.mkdir(parents=True, exist_ok=True)

    tables, global_summary, dof_summary = build_output_tables(
        clean_model=clean_model,
        data=data,
        summary=summary,
        package=package,
    )

    tables["nodal_loads"].to_csv(output_dir / "nodal_loads.csv", index=False)
    tables["node_displacements"].to_csv(output_dir / "node_displacements.csv", index=False)
    tables["support_reactions"].to_csv(output_dir / "support_reactions.csv", index=False)
    tables["element_basic_data"].to_csv(output_dir / "element_basic_data.csv", index=False)
    tables["element_local_displacements"].to_csv(output_dir / "element_local_displacements.csv", index=False)
    tables["element_local_end_forces"].to_csv(output_dir / "element_local_end_forces.csv", index=False)
    tables["element_global_end_forces"].to_csv(output_dir / "element_global_end_forces.csv", index=False)
    tables["element_derived_results"].to_csv(output_dir / "element_derived_results.csv", index=False)

    write_json(global_summary, output_dir / "global_summary.json")
    write_json(dof_summary, output_dir / "dof_summary.json")
    write_summary_md(clean_model, global_summary, output_dir)
    write_run_log(clean_model, model_path, output_dir)

    return output_dir, tables, global_summary, dof_summary