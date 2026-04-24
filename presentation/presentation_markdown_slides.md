# Mixed 3D Truss and Frame Analysis of the Fort Griffin Iron Truss Bridge

Final Project Presentation

Anzara Zabin
CEE 6501 Final Project

![Elevation from south of the Fort Griffin Iron Truss Bridge](../report/Case%20study/images/ELEVATION%20FROM%20S.%20-%20Fort%20Griffin%20Iron%20Truss%20Bridge,%20Spanning%20Clear%20Fork%20of%20Brazos%20River%20at%20County%20Route%20188,%20Fort%20Griffin,%20Shackelford%20County,%20TX.png)

*Figure. Elevation from south of the Fort Griffin Iron Truss Bridge.*


---

# Roadmap

- Code goal and workflow
- Repository organization
- User example files and expected outputs
- Validation summary
- Fort Griffin bridge and why it was chosen
- Modeling assumptions, material properties, loads, and limitations
- Revised dead load baseline
- Missing diagonal scenario
- Weakened floor beam scenario
- Final comparison and takeaways

---

# Code Goal and Workflow

- One Python workflow for mixed `3D_truss` and `3D_frame` analysis
- User defines the structure through a JSON file
- `main.ipynb` reads the model and runs the analysis
- Preprocess, assemble, solve, recover results, save outputs
- Same workflow used for user examples, validation models, and final bridge cases


# Repository Organization

- `main.ipynb`
- `helpers/`
- `inputs/user_examples/`
- `inputs/validation/`
- `inputs/final_bridge/`
- `outputs/runs/`
- `outputs/user_examples/simple_plots/`
- `outputs/user_examples/plotly_plots/`
- `report/`
- `presentation/`

## Main design idea

A new user should only need to change the selected model or `model_path`, not the solver itself.

---

# Helper Files Used in the Project

## Core helper modules

- `helpers/preprocess.py`
- `helpers/elements_3d.py`
- `helpers/solver.py`
- `helpers/postprocess.py`
- `helpers/output_writer.py`
- `helpers/plotting_simple.py`
- `helpers/plotting_plotly.py`

## Design idea

The notebook controls the run, but the structural logic is stored in reusable helper files.

---

# What Each Helper File Contains

## `preprocess.py`
- reads the JSON file
- checks the model blocks
- builds node and element lookup data
- creates the global degree of freedom map
- identifies free and restrained DOFs

## `elements_3d.py`
- truss element routines
- frame element routines
- local stiffness and transformation logic
- element load and feature contributions

## `solver.py`
- global assembly
- partitioning of the global system
- solution for unknown displacements
- recovery of reactions

---

# What Each Helper File Contains

## `postprocess.py`
- recovers element level quantities after solving
- computes local and global end force results
- prepares derived structural response values

## `output_writer.py`
- organizes output tables
- writes CSV files and summary files
- creates the saved run folder in `outputs/runs/<model_name>/`

## `plotting_simple.py`
- static undeformed and deformed plots
- optional node and element labels

## `plotting_plotly.py`
- interactive 3D structural plots
- hover information
- saved HTML and PNG figures

---

# Main Notebook Workflow

## Step 1  select a model

- user picks `selected_example`
- notebook sets `model_path`

## Step 2  import helper modules

- notebook loads the helper files
- same helper files are reused for all models

## Step 3  preprocess the model

- `preprocess_model(model_path)`

## Step 4  solve the model

- `solve_complete_model(clean_model, data)`

---

# Workflow from Main to Outputs

## After solving

- `write_run_outputs(...)`
- saves tables and summaries in `outputs/runs/<model_name>/`

## Plot generation

- `plot_structure_simple(...)`
- `plot_structure_plotly(...)`

## Final products

- notebook tables
- CSV and JSON outputs
- static figures
- interactive Plotly views

---

# User Example Files

## Starter files for a new user

- `inputs/user_examples/truss_example_for_user.json`
- `inputs/user_examples/beam_example_for_user.json`

## What they show

### Truss example
- nodes
- truss connectivity
- supports
- nodal load input

### Beam example
- `3D_frame` input
- section properties
- member load input
- bending response

---

# What a User Gets After Running a Model

## In the notebook

- model summary
- node displacements
- support reactions
- element local end forces
- element derived results

## Saved output folder

- `outputs/runs/<model_name>/`

## Saved plots

- `outputs/user_examples/simple_plots/`
- `outputs/user_examples/plotly_plots/`

## Main output files

- `summary.md`
- `global_summary.json`
- `node_displacements.csv`
- `support_reactions.csv`
- `element_local_end_forces.csv`
- `element_derived_results.csv`

---


## Main design idea

A new user should only need to change the selected model or `model_path`, not the solver itself.

---

# User Example Files

## Starter files for a new user

- `inputs/user_examples/truss_example_for_user.json`
- `inputs/user_examples/beam_example_for_user.json`

## What they show

### Truss example
- nodes
- truss connectivity
- supports
- nodal load input

### Beam example
- `3D_frame` input
- section properties
- member load input
- bending response
  
---
# Github Repository

https://github.com/azabin3/cee6501-AZ-final-project

# Validation Summary

## Verified before bridge application

- 3D truss behavior
- 3D frame behavior
- member releases
- support displacement
- temperature loading
- fabrication error

![bg right:40% contain](../outputs/validation/plotly_plots/validation_3d_truss_with_loads_interactive_def+undef.png)

The bridge study was only done after the solver reproduced the required benchmark behaviors.

![bg right:42% contain](../outputs/validation/simple_plots/3D_frame_validation.png)

---

# Why Fort Griffin Bridge

- Real bridge with available photos, drawings, and case-study information
- Naturally combines truss action and frame action
- Side trusses are mainly axial-force dominated
- Floor beams and stringers are bending dominated
- Good final case for a mixed solver rather than a truss-only model
 
---
# Features

- Built in 1885 by the King Iron and Bridge Manufacturing Company
- Historic wrought iron pin-connected Pratt through truss in Shackelford County, Texas :contentReference[oaicite:0]{index=0}
- Main span length about 109 to 110 ft
- Overall width about 20 ft
- Clear roadway width about 13 ft 6 in
- Truss height about 18 ft 

---
![Barrel view from east of the Fort Griffin Iron Truss Bridge](../report/Case%20study/images/BARREL%20VIEW%20FROM%20E.%20-%20Fort%20Griffin%20Iron%20Truss%20Bridge,%20Spanning%20Clear%20Fork%20of%20Brazos%20River%20at%20County%20Route%20188,%20Fort%20Griffin,%20Shackelford%20County,%20TX.png)
*Figure. Barrel view from east of the Fort Griffin Iron Truss Bridge.*

---


![Elevation from south of the Fort Griffin Iron Truss Bridge](../report/Case%20study/images/ELEVATION%20FROM%20S.%20-%20Fort%20Griffin%20Iron%20Truss%20Bridge,%20Spanning%20Clear%20Fork%20of%20Brazos%20River%20at%20County%20Route%20188,%20Fort%20Griffin,%20Shackelford%20County,%20TX.png)

*Figure. Elevation from south of the Fort Griffin Iron Truss Bridge.*


---

# Model Setup and Assumptions

## Idealization

- Main span only
![Overall elevation of the bridge](../report/Case%20study/images/Overall%20elevation%20of%20the%20bridge.png)

*Figure. Overall elevation of the bridge.*

---

- Side trusses modeled with `3D_truss` elements
- Floor beams modeled with `3D_frame` elements
- Stringers modeled with `3D_frame` elements
- Top lateral bracing included as truss elements

## Coordinate system

- `x` along span
- `y` across width
- `z` vertical

## Units

- feet
- kips

---
---
# Material Properties, Loads, and Limitations

## Material assumption

- Single wrought iron material
- Linear elastic behavior

## Baseline load assumptions

- Redistributed dead load on modeled stringer lines
- Floor beam self weight surrogate
- Truss nodal dead load surrogate

## Main limitations

- Simplified supports
- Partly assumed member properties
- Deck not modeled explicitly
- Bottom lateral bracing not included
- Idealized connection behavior

---
![Case study 2D truss model](../report/Case%20study/images/Case%20study%202D%20truss%20model.png)

*Figure. Case study 2D truss model.*

---

![Fort Griffin revised baseline undeformed and deformed](../outputs/final_bridge/simple_plots/fort_griffin_revised_baseline_undeformed_plus_deformed.png)

*Figure. Fort Griffin revised baseline undeformed and deformed view.*

---
# Dead Load Baseline

## Main observations

- Floor system receives gravity load first
- Load is transferred into the two side trusses
- Largest displacement occurs in the central floor system region
- Response is physically reasonable for a mixed truss and frame bridge

## Key value

- Node 32 maximum vertical displacement  


![Fort Griffin revised dead-load baseline Plotly undeformed and deformed](../outputs/final_bridge/plotly_plots/fort_griffin_revised_deadload_undeformed_plus_deformed.png)

*Figure. Fort Griffin revised dead-load baseline Plotly undeformed and deformed view.*
---

# Scenario 1  Missing Diagonal

## Change from baseline

- One left side diagonal removed near midspan
- Geometry, supports, and loads otherwise unchanged
- Load changed in surrounding noads

![Extreme missing diagonals overload scenario undeformed and deformed](../outputs/final_bridge/simple_plots/scenario_extreme_missing_diagonals_overload_undeformed_plus_deformed.png)

![Scenario extreme missing diagonals overload undeformed and deformed](../outputs/final_bridge/plotly_plots/scenario_extreme_missing_diagonals_overload_undeformed_plus_deformed_2.png)

*Figure. Extreme missing diagonals overload case, undeformed and deformed view.*

![Scenario extreme missing diagonals overload undeformed and deformed](../outputs/final_bridge/plotly_plots/scenario_extreme_missing_diagonals_overload_undeformed_plus_deformed_3.png)

*Figure. Extreme missing diagonals overload case, showing relative displacement.*

## Main result

- Node 32 maximum vertical displacement  
  `9.1476 × 10^-5 ft`
- Change from baseline  
  `+0.6%`

## Interpretation

- Small change in global displacement
- More important for truss force redistribution than for visible bridge sag


---

# Scenario 2  Weakened Floor Beam

## Change from baseline

- Loaded floor beam line weakened
- Geometry, supports, and loads unchanged

## Main result

- Node 32 maximum vertical displacement  

- Change from baseline  
  `+22.2%`

## Interpretation

- Strong local floor system sensitivity
- Bridge remains globally stable
- Local deck level flexibility increases noticeably

![bg right:48% contain](../outputs/final_bridge/simple_plots/scenario_weakened_floor_beam_from_deadload_undeformed_plus_deformed.png)

---
![Weakened floor beam scenario Plotly undeformed and deformed](../outputs/final_bridge/plotly_plots/scenario_weakened_floor_beam_from_deadload_undeformed_plus_deformed.png)
---

# Key Findings

- The solver supports mixed `3D_truss` and `3D_frame` analysis in one workflow
- User input is organized through JSON files
- Validation confirmed the required structural behaviors before bridge application
- The Fort Griffin bridge shows a clear mixed truss and frame load path
- The baseline response is governed by floor system load transfer into the side trusses
- The missing diagonal case mainly changes the truss force path
- The weakened floor beam case produces the clearest local damage response

---

# Thank You

Questions
