# Future Project: Printago Plate-Sliced File Prep

This is a separate project idea, not part of the Gridfinity bin batcher.

## Goal

Create a general-purpose tool that turns arbitrary print files into
Printago-ready, printer-prefixed `.gcode.3mf` packages.

## Why Separate

The Gridfinity bin batcher has a narrow job:

- generate known Gridfinity bin sizes
- apply fixed bin defaults
- place each bin consistently on a Bambu plate
- slice with approved printer profiles

A general Printago prep tool has a broader job and should not be coupled to
Gridfinity naming, OpenSCAD parameters, or bin geometry.

## Possible Scope

- Accept STL, OBJ, plain 3MF, or Bambu project 3MF inputs.
- Apply placement rules such as front-margin offsets and rotation policies.
- Slice each input with one or more Bambu Studio printer presets.
- Stamp matching printer metadata into generated `.gcode.3mf` packages.
- Validate ZIP structure, embedded G-code, printer profile metadata, and
  Printago import behavior.
- Produce searchable file names for print-on-demand libraries.

## Reusable Pieces From This Repo

- Bambu CLI slicing orchestration from `batch_slice_gcode_3mf.py`
- `.gcode.3mf` packaging and metadata stamping from `package_gcode_3mf.py`
- Bambu project wrapping ideas from `make_bambu_project_3mf.py`
- Front-placement and package metadata validation commands from `README.md`
- The output convention of separating source meshes, Bambu projects, and final
  printer-specific `.gcode.3mf` packages

## Open Questions

- Should the general tool preserve original model orientation or auto-orient by
  bounding box?
- Should it create Bambu project 3MF files first, or slice source meshes
  directly where possible?
- How should printer profiles and filament profiles be configured for teams?
- Should generated packages be stored in GitHub Releases, object storage, or a
  Printago import staging folder?
- Should CAD Viewer thumbnails become the default preview renderer, with Pillow
  thumbnails retained as a no-browser fallback?
