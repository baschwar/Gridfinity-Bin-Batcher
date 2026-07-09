# Changelog

## Unreleased

### Changed

- Clarified that users must supply their own Bambu Studio printer preset JSON
  files and that automated part ejection depends on those presets already
  containing tested ejection G-code.
- Added a reference to the companion
  `baschwar/3D-Printed-Part-Ejection-GCode` repo for part-ejection setup.
- Added README attribution for `ostat/gridfinity_extended_openscad` and Zack
  Freedman / Voidstar Lab's Gridfinity work.

## [0.1.0] - 2026-07-09

Initial working release.

### Added

- CSV-driven Gridfinity Extended bin generation for STL and source 3MF outputs.
- Standard 45-bin library covering unique `1x1` through `5x5` sizes at heights
  `6`, `12`, and `18`.
- Bambu Studio project 3MF wrapping with 90 degree Z rotation and 5 mm front
  purge-line clearance.
- Bambu Studio CLI slicing for X1C and P2S printer profiles.
- Printago-compatible `.gcode.3mf` packaging with printer metadata and generated
  thumbnails.
- Documentation for dependencies, printer presets, validation, output layout,
  and future generic Printago automation work.
