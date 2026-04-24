from numbers import Number

VALID_DOF_LABELS = ["ux", "uy", "uz", "rx", "ry", "rz"]
VALID_RELEASE_LABELS = ["rx", "ry", "rz"]
VALID_ELEMENT_TYPES = ["3D_truss", "3D_frame"]
VALID_MEMBER_LOAD_TYPES = [
    "uniform_local_y",
    "uniform_local_z",
    "point_local_y_midspan",
    "point_local_z_midspan",
]


def _require_dict(obj, name):
    if not isinstance(obj, dict):
        raise ValueError(f"{name} must be a dictionary.")


def _require_list(obj, name):
    if not isinstance(obj, list):
        raise ValueError(f"{name} must be a list.")


def _require_numeric(value, name):
    if not isinstance(value, Number):
        raise ValueError(f"{name} must be numeric.")


def check_nodes_block(model):
    nodes = model["nodes"]
    _require_dict(nodes, "nodes")

    for node_id, coords in nodes.items():
        if not isinstance(coords, list) or len(coords) != 3:
            raise ValueError(
                f"Node {node_id} must have exactly 3 coordinates."
            )
        for i, value in enumerate(coords):
            _require_numeric(value, f"nodes[{node_id}][{i}]")


def check_materials_block(model):
    materials = model["materials"]
    _require_dict(materials, "materials")

    for name, props in materials.items():
        _require_dict(props, f"materials['{name}']")

        if "E" not in props:
            raise ValueError(f"Material '{name}' is missing E.")
        _require_numeric(props["E"], f"materials['{name}']['E']")

        if "G" in props:
            _require_numeric(props["G"], f"materials['{name}']['G']")

        if "alpha" in props:
            _require_numeric(props["alpha"], f"materials['{name}']['alpha']")


def check_sections_block(model):
    sections = model["sections"]
    _require_dict(sections, "sections")

    for name, props in sections.items():
        _require_dict(props, f"sections['{name}']")


def check_elements_block(model):
    elements = model["elements"]
    nodes = model["nodes"]
    materials = model["materials"]
    sections = model["sections"]

    _require_dict(elements, "elements")

    for elem_id, elem in elements.items():
        _require_dict(elem, f"elements[{elem_id}]")

        elem_type = elem.get("type")
        if elem_type not in VALID_ELEMENT_TYPES:
            raise ValueError(
                f"Element {elem_id} has invalid type '{elem_type}'."
            )

        elem_nodes = elem.get("nodes")
        if not isinstance(elem_nodes, list) or len(elem_nodes) != 2:
            raise ValueError(
                f"Element {elem_id} must reference exactly 2 nodes."
            )

        for node_id in elem_nodes:
            if node_id not in nodes:
                raise ValueError(
                    f"Element {elem_id} references undefined node {node_id}."
                )

        material_name = elem.get("material")
        if material_name not in materials:
            raise ValueError(
                f"Element {elem_id} references undefined material '{material_name}'."
            )

        section_name = elem.get("section")
        if section_name not in sections:
            raise ValueError(
                f"Element {elem_id} references undefined section '{section_name}'."
            )

        mat = materials[material_name]
        sec = sections[section_name]

        if "E" not in mat:
            raise ValueError(
                f"Material '{material_name}' used by element {elem_id} is missing E."
            )

        if "A" not in sec:
            raise ValueError(
                f"Section '{section_name}' used by element {elem_id} is missing A."
            )
        _require_numeric(sec["A"], f"sections['{section_name}']['A']")

        if elem_type == "3D_frame":
            for key in ["Iy", "Iz", "J"]:
                if key not in sec:
                    raise ValueError(
                        f"Section '{section_name}' used by frame element {elem_id} is missing {key}."
                    )
                _require_numeric(sec[key], f"sections['{section_name}']['{key}']")

            if "G" not in mat:
                raise ValueError(
                    f"Material '{material_name}' used by frame element {elem_id} is missing G."
                )

            release = elem.get("release", {"start": [], "end": []})
            _check_release_record(release, elem_id)

        elif elem_type == "3D_truss":
            if "release" in elem:
                raise ValueError(
                    f"Truss element {elem_id} should not define a release record."
                )


def _check_release_record(release, elem_id):
    _require_dict(release, f"elements[{elem_id}]['release']")

    allowed_sets = [set(), set(VALID_RELEASE_LABELS)]

    for end_name in ["start", "end"]:
        if end_name not in release:
            raise ValueError(
                f"Element {elem_id} release is missing '{end_name}'."
            )

        end_list = release[end_name]
        _require_list(end_list, f"elements[{elem_id}]['release']['{end_name}']")

        if len(end_list) != len(set(end_list)):
            raise ValueError(
                f"Element {elem_id} release '{end_name}' contains duplicate DOF labels."
            )

        for dof in end_list:
            if dof not in VALID_RELEASE_LABELS:
                raise ValueError(
                    f"Element {elem_id} release '{end_name}' has invalid DOF '{dof}'."
                )

        if set(end_list) not in allowed_sets:
            raise ValueError(
                f"Element {elem_id} release '{end_name}' currently supports only [] or ['rx', 'ry', 'rz']."
            )


def check_supports_block(model):
    supports = model["supports"]
    nodes = model["nodes"]

    _require_dict(supports, "supports")

    for node_id, dofs in supports.items():
        if node_id not in nodes:
            raise ValueError(
                f"Support references undefined node {node_id}."
            )

        _require_list(dofs, f"supports[{node_id}]")

        if len(dofs) != len(set(dofs)):
            raise ValueError(
                f"Support at node {node_id} contains duplicate DOF labels."
            )

        for dof in dofs:
            if dof not in VALID_DOF_LABELS:
                raise ValueError(
                    f"Support at node {node_id} has invalid DOF '{dof}'."
                )


def check_nodal_loads_block(model):
    loads = model["nodal_loads"]
    nodes = model["nodes"]

    _require_list(loads, "nodal_loads")

    for i, load in enumerate(loads):
        _require_dict(load, f"nodal_loads[{i}]")

        node_id = load.get("node")
        if node_id not in nodes:
            raise ValueError(
                f"nodal_loads[{i}] references undefined node {node_id}."
            )

        values = load.get("values")
        if not isinstance(values, list) or len(values) != 6:
            raise ValueError(
                f"nodal_loads[{i}] must have 6 load components."
            )

        for j, value in enumerate(values):
            _require_numeric(value, f"nodal_loads[{i}]['values'][{j}]")


def check_member_loads_block(model):
    loads = model["member_loads"]
    elements = model["elements"]

    _require_list(loads, "member_loads")

    for i, load in enumerate(loads):
        _require_dict(load, f"member_loads[{i}]")

        elem_id = load.get("element")
        if elem_id not in elements:
            raise ValueError(
                f"member_loads[{i}] references undefined element {elem_id}."
            )

        elem_type = elements[elem_id]["type"]
        if elem_type != "3D_frame":
            raise ValueError(
                f"member_loads[{i}] can currently be applied only to 3D_frame elements."
            )

        load_type = load.get("type")
        if load_type not in VALID_MEMBER_LOAD_TYPES:
            raise ValueError(
                f"member_loads[{i}] has invalid type '{load_type}'."
            )

        if "w" in load:
            _require_numeric(load["w"], f"member_loads[{i}]['w']")
        if "P" in load:
            _require_numeric(load["P"], f"member_loads[{i}]['P']")

        if "w" not in load and "P" not in load:
            raise ValueError(
                f"member_loads[{i}] must define either 'w' or 'P'."
            )


def check_prescribed_displacements_block(model):
    items = model["prescribed_displacements"]
    nodes = model["nodes"]
    supports = model["supports"]

    _require_list(items, "prescribed_displacements")

    for i, item in enumerate(items):
        _require_dict(item, f"prescribed_displacements[{i}]")

        node_id = item.get("node")
        if node_id not in nodes:
            raise ValueError(
                f"prescribed_displacements[{i}] references undefined node {node_id}."
            )

        dof = item.get("dof")
        if dof not in VALID_DOF_LABELS:
            raise ValueError(
                f"prescribed_displacements[{i}] has invalid DOF '{dof}'."
            )

        if node_id not in supports or dof not in supports[node_id]:
            raise ValueError(
                f"prescribed_displacements[{i}] must be applied at a restrained DOF."
            )

        if "value" not in item:
            raise ValueError(
                f"prescribed_displacements[{i}] is missing value."
            )
        _require_numeric(item["value"], f"prescribed_displacements[{i}]['value']")

def check_temperature_loads_block(model):
    items = model["temperature_loads"]
    elements = model["elements"]

    _require_list(items, "temperature_loads")

    for i, item in enumerate(items):
        _require_dict(item, f"temperature_loads[{i}]")

        elem_id = item.get("element")
        if elem_id not in elements:
            raise ValueError(
                f"temperature_loads[{i}] references undefined element {elem_id}."
            )

        if "deltaT" not in item:
            raise ValueError(
                f"temperature_loads[{i}] is missing deltaT."
            )
        _require_numeric(item["deltaT"], f"temperature_loads[{i}]['deltaT']")


def check_fabrication_errors_block(model):
    items = model["fabrication_errors"]
    elements = model["elements"]

    _require_list(items, "fabrication_errors")

    for i, item in enumerate(items):
        _require_dict(item, f"fabrication_errors[{i}]")

        elem_id = item.get("element")
        if elem_id not in elements:
            raise ValueError(
                f"fabrication_errors[{i}] references undefined element {elem_id}."
            )

        if "deltaL" not in item:
            raise ValueError(
                f"fabrication_errors[{i}] is missing deltaL."
            )
        _require_numeric(item["deltaL"], f"fabrication_errors[{i}]['deltaL']")


def run_all_model_checks(model):
    """
    Run all current model validation checks.
    Raises ValueError if any check fails.
    """
    check_nodes_block(model)
    check_materials_block(model)
    check_sections_block(model)
    check_elements_block(model)
    check_supports_block(model)
    check_nodal_loads_block(model)
    check_member_loads_block(model)
    check_prescribed_displacements_block(model)
    check_temperature_loads_block(model)
    check_fabrication_errors_block(model)