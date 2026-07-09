# Roadmap

## Keep This Repo Focused

Gridfinity Bin Batcher should remain an opinionated tool for generating and
packaging Gridfinity Extended bins:

- read bin sizes from CSV
- generate Gridfinity Extended STL and source 3MF files
- wrap source 3MF files as Bambu Studio project 3MF files
- slice/package printer-specific Printago-ready `.gcode.3mf` files
- document the required local OpenSCAD, Bambu Studio, and printer preset setup

## Near-Term Improvements

- Add friendlier validation commands or a single validation script.
- Improve generated thumbnails, likely by using CAD Viewer renders.
- Add clearer examples for custom `bins.csv` files.
- Add optional release artifact packaging for generated STL, 3MF, and
  `.gcode.3mf` batches.

## Spin-Out Project

The generic Printago plate-sliced file prep idea should become a separate repo,
not a large refactor inside this one.

See `FUTURE_PRINTAGO_AUTOMATION.md` for the current spin-out notes.

The future project should focus on arbitrary print files rather than
Gridfinity-specific generation:

- accept STL, OBJ, plain 3MF, and Bambu project 3MF inputs
- apply reusable placement and rotation policies
- slice each input with one or more Bambu Studio printer profiles
- package Printago-compatible `.gcode.3mf` files
- validate package structure, embedded G-code, metadata, and Printago import
  behavior

Useful extraction candidates from this repo:

- `batch_slice_gcode_3mf.py`
- `package_gcode_3mf.py`
- Bambu project wrapping logic from `make_bambu_project_3mf.py`
- package validation and bbox/front-placement checks from `README.md`
