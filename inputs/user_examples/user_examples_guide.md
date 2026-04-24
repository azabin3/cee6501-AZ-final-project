# User Example Guide

## Files in this folder

- `truss_example_for_user.json`
- `beam_example_for_user.json`

These are small starter models for a first time user.

## truss_example_for_user.json

This file is meant to show

- node coordinates
- one material
- one section
- truss connectivity
- support definition
- nodal loading

Good things to change first

- node coordinates in `nodes`
- bar area in `sections`
- support conditions in `supports`
- the applied nodal load in `nodal_loads`

Important note

This truss example restrains rotations at all nodes because the project uses a mixed global 6 degree of freedom format. That keeps the truss example stable in the solver.

## beam_example_for_user.json

This file is meant to show

- frame element input
- frame section properties
- fixed support input
- member load input
- a simple cantilever beam response

Good things to change first

- beam length in `nodes`
- frame section properties in `sections`
- the distributed load in `member_loads`

Important note

In this project, a beam is modeled with `3D_frame` elements.

## Units reminder

The solver does not convert units automatically.

If a file uses `ft` and `kip`, every value in that file must be consistent with `ft` and `kip`.
