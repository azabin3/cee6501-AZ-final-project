# CEE6501 Final Project

Mixed 3D truss and 3D frame structural analysis using the direct stiffness method.

## What this code does

This repository analyzes structures made of `3D_truss` and `3D_frame` elements using the direct stiffness method. The workflow is built so that a user defines the structure in a JSON file, runs the main notebook, and gets both notebook tables and saved result files. The same workflow is used for simple user examples, validation studies, and the final Fort Griffin bridge study.

## Main entry point

Run the project from

- `main.ipynb`

A user should not need to edit the solver files to run a model. In normal use, the only file that needs to be changed is the selected JSON input file path in the notebook.

## Repository map

- `main.ipynb`  
  top-level notebook used to run models

- `helpers/`  
  reusable analysis code for preprocessing, solving, postprocessing, output writing, and plotting

- `inputs/user_examples/`  
  starter files intended for a new user

- `inputs/validation/`  
  validation models used to verify the implementation

- `inputs/final_bridge/`  
  Fort Griffin bridge baseline and scenario files

- `outputs/runs/`  
  saved tables and summaries for each run

- `outputs/user_examples/simple_plots/`  
  saved Matplotlib figures for user examples

- `outputs/user_examples/plotly_plots/`  
  saved Plotly figures for user examples

- `report/`  
  final report files

- `presentation/`  
  final presentation files

## Install and run

1. Install the packages in `requirements.txt`
2. Open `main.ipynb`
3. Set the selected example name or the `model_path`
4. Run the notebook from top to bottom

## Sample files for a new user

The easiest place to start is

- `inputs/user_examples/truss_example_for_user.json`
- `inputs/user_examples/beam_example_for_user.json`

The truss example is a small starter model for axial-force behavior.

The beam example is a small starter frame model for bending behavior. In this project, a beam is modeled using `3D_frame` elements.
## Unit System and Conventions

The solver does not convert units automatically. Every model must be entered in one consistent unit system from start to finish.

The code only checks the numbers you provide. It does not know whether a value was intended to be in ft, m, kip, kN, or any other unit. Because of that, the user must keep all geometry, material properties, section properties, loads, and output interpretation in a single compatible system.

### How units work in this project

The unit system is declared in the JSON file under the `units` block. This block is mainly for documentation and readability. The solver still assumes that all values in the model are already consistent.

Example

```json id="xbkr1q"
"units": {
  "length": "ft",
  "force": "kip"
}
```

## Where the sample files are run

The sample files are intended to be selected directly from `main.ipynb` using a short example-selection cell near the top of the notebook. The user should be able to switch between sample models by changing only one line.

Example selections

- `truss_example_for_user`
- `beam_example_for_user`
- `validation_3d_truss`
- `validation_3d_frame`
- `fort_griffin_main_span_revised_deadload`

## What the notebook shows

After a run, the notebook shows quick tables such as

- model summary
- node displacements
- support reactions
- element derived results

These are useful for immediate interpretation inside Jupyter.

## What gets saved automatically

Each run writes an output folder to

- `outputs/runs/<model_name>/`

Typical saved files include

- `summary.md`
- `global_summary.json`
- `dof_summary.json`
- `nodal_loads.csv`
- `node_displacements.csv`
- `support_reactions.csv`
- `element_basic_data.csv`
- `element_local_displacements.csv`
- `element_local_end_forces.csv`
- `element_global_end_forces.csv`
- `element_derived_results.csv`
- `run_log.txt`

## Plot files and locations

For user examples, save figures to

- `outputs/user_examples/simple_plots/`
- `outputs/user_examples/plotly_plots/`

For larger studies such as the bridge, keep using the existing project output folders.

## Plot variations available in the notebook

The plotting helpers allow several useful display choices.

Simple Matplotlib plots can show

- undeformed only
- undeformed plus deformed
- optional node labels
- optional element labels

Plotly plots can show

- undeformed only
- undeformed plus deformed
- nodes
- node labels
- element hover information
- nodal loads
- support reactions
- member loads

## How to use the Plotly figure

The interactive Plotly figure is meant for visual inspection of the model and response. Use it to inspect geometry, deformation pattern, and element information through hover interaction. Keep the Plotly view for exploration and the saved PNG files for the report and presentation.

## How to derive additional values in Jupyter

The notebook can be used not only to run the model but also to create custom summaries. For example, a user can sort nodes by displacement magnitude, list the largest reactions, rank frame elements by end moment, or rank truss elements by axial force. This makes the notebook useful for both verification and interpretation.

## Supported input blocks

Each model JSON may contain these top-level blocks

- `model_name`
- `units`
- `nodes`
- `materials`
- `sections`
- `elements`
- `supports`
- `nodal_loads`
- `member_loads`
- `prescribed_displacements`
- `temperature_loads`
- `fabrication_errors`

## Supported load types currently used in the project

For member loads, the current supported types are

- `uniform_local_y`
- `uniform_local_z`
- `point_local_y_midspan`
- `point_local_z_midspan`

## Best way to make a new model

1. Copy one of the user example files
2. Rename it
3. Edit nodes, materials, sections, elements, supports, and loads
4. Point `model_path` to the new file in `main.ipynb`
5. Run the notebook
6. Review notebook tables and saved outputs