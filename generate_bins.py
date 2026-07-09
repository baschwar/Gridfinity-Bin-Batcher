#!/usr/bin/env python3
"""Generate Gridfinity Extended bin files from a small CSV."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


DEFAULT_SCAD = "gridfinity_extended_openscad/gridfinity_basic_cup.scad"
CORE_3MF_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def openscad_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(openscad_value(item) for item in value) + "]"
    return json.dumps(str(value))


def safe_name(value: str) -> str:
    cleaned = []
    for char in value.strip().lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in (" ", "-", "_", "."):
            cleaned.append("_")
    name = "".join(cleaned).strip("_")
    return name or "bin"


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "y", "on"):
        return True
    if normalized in ("0", "false", "no", "n", "off"):
        return False
    raise ValueError(f"Expected a boolean value, got {value!r}")


def parse_cell(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value.lower() in ("true", "false", "yes", "no", "on", "off"):
        return parse_bool(value)
    try:
        number = float(value)
    except ValueError:
        return value
    if number.is_integer():
        return int(number)
    return number


def load_defaults(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def read_bins(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            parsed = {
                key: parse_cell(value)
                for key, value in row.items()
                if key is not None and value is not None and value.strip() != ""
            }
            rows.append(parsed)
    return rows


def row_to_parameters(defaults: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    params = dict(defaults)
    try:
        columns = row.pop("grid_columns")
        rows = row.pop("grid_rows")
        height = row.pop("height")
    except KeyError as error:
        raise ValueError(f"Missing required CSV column: {error.args[0]}") from error

    params["width"] = [columns, 0]
    params["depth"] = [rows, 0]
    params["height"] = [height, 0]

    row.pop("name", None)
    params.update(row)
    return params


def build_command(openscad: str, scad: Path, output: Path, params: dict[str, Any]) -> list[str]:
    command = [openscad, "--enable=textmetrics", "-o", str(output)]
    if output.suffix.lower() == ".3mf":
        command.extend(["-O", "export-3mf/unit=millimeter"])
    for key in sorted(params):
        command.extend(["-D", f"{key}={openscad_value(params[key])}"])
    command.append(str(scad))
    return command


def output_name(name: str, columns: Any, rows: Any, height: Any, extension: str) -> str:
    size = f"{columns}x{rows}x{height}"
    safe = safe_name(name)
    if safe.endswith(size):
        return f"{safe}.{extension}"
    return f"{safe}_{size}.{extension}"


def positioned_scad_source(scad: Path, x: float, y: float, rotation_degrees: int) -> str:
    source = scad.read_text(encoding="utf-8")
    marker = "set_environment("
    index = source.rfind(marker)
    if index == -1:
        raise ValueError(f"Could not find final {marker!r} call in {scad}")
    transform = f"translate([{x}, {y}, 0])\n"
    if rotation_degrees:
        transform += f"rotate([0, 0, {rotation_degrees}])\n"
    return source[:index] + transform + source[index:]


def parse_formats(value: str) -> list[str]:
    formats = []
    for item in value.split(","):
        normalized = item.strip().lower().lstrip(".")
        if normalized:
            formats.append(normalized)
    unsupported = sorted(set(formats) - {"stl", "3mf"})
    if unsupported:
        raise ValueError(f"Unsupported format(s): {', '.join(unsupported)}")
    return formats


def normalize_3mf_to_build_transform(path: Path) -> None:
    """Move mesh coordinate offsets into the 3MF build item transform."""
    if path.suffix.lower() != ".3mf":
        return

    model_name = "3D/3dmodel.model"
    with zipfile.ZipFile(path, "r") as source:
        files = {name: source.read(name) for name in source.namelist()}

    root = ET.fromstring(files[model_name])
    ns = {"m": CORE_3MF_NS}
    vertices = root.findall(".//m:vertex", ns)
    if not vertices:
        return

    min_x = min(float(vertex.attrib["x"]) for vertex in vertices)
    min_y = min(float(vertex.attrib["y"]) for vertex in vertices)
    min_z = min(float(vertex.attrib["z"]) for vertex in vertices)

    for vertex in vertices:
        vertex.attrib["x"] = f"{float(vertex.attrib['x']) - min_x:.6f}"
        vertex.attrib["y"] = f"{float(vertex.attrib['y']) - min_y:.6f}"
        vertex.attrib["z"] = f"{float(vertex.attrib['z']) - min_z:.6f}"

    item = root.find(".//m:build/m:item", ns)
    if item is not None:
        item.attrib["transform"] = (
            f"1 0 0 {min_x:.6f} "
            f"0 1 0 {min_y:.6f} "
            f"0 0 1 {min_z:.6f}"
        )

    ET.register_namespace("", CORE_3MF_NS)
    files[model_name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    temp_path = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, data in files.items():
            target.writestr(name, data)
    temp_path.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="bins.csv", type=Path)
    parser.add_argument("--defaults", default="defaults.json", type=Path)
    parser.add_argument("--scad", default=DEFAULT_SCAD, type=Path)
    parser.add_argument("--output-dir", default="output", type=Path)
    parser.add_argument("--formats", default="stl,3mf")
    parser.add_argument(
        "--plate-position",
        choices=("model", "front"),
        default="model",
        help="Use 'front' to offset exported geometry toward the front of a plate.",
    )
    parser.add_argument("--plate-width", default=256.0, type=float)
    parser.add_argument("--plate-depth", default=256.0, type=float)
    parser.add_argument("--front-margin", default=5.0, type=float)
    parser.add_argument(
        "--orientation",
        choices=("rotate-90", "widest-y", "csv"),
        default="rotate-90",
        help="Use 'rotate-90' to rotate every bin 90 degrees on the plate.",
    )
    parser.add_argument("--openscad", default="openscad")
    parser.add_argument(
        "--openscad-prefix",
        default="",
        help="Optional command prefix, for example 'arch -x86_64' on macOS.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    defaults = load_defaults(args.defaults)
    formats = parse_formats(args.formats)
    bins = read_bins(args.csv)
    if not bins:
        print(f"No rows found in {args.csv}", file=sys.stderr)
        return 1

    openscad_parts = args.openscad_prefix.split() + [args.openscad]
    openscad_path = shutil.which(args.openscad)
    if openscad_path is None and not args.dry_run:
        print(
            f"OpenSCAD executable {args.openscad!r} was not found. "
            "Install OpenSCAD Developer Version or pass --openscad /path/to/openscad. "
            "Use --dry-run to preview commands.",
            file=sys.stderr,
        )
        return 1

    if not args.scad.exists() and not args.dry_run:
        print(
            f"SCAD file not found: {args.scad}. "
            "Clone https://github.com/ostat/gridfinity_extended_openscad into "
            "gridfinity_extended_openscad/ or pass --scad.",
            file=sys.stderr,
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("XDG_CACHE_HOME", str(args.output_dir / ".cache"))
    wrapper_parent = args.scad.parent.resolve()
    with ExitStack() as stack:
        temp_files: list[Path] = []
        stack.callback(lambda: [path.unlink(missing_ok=True) for path in temp_files])
        for row in bins:
            row_copy = dict(row)
            raw_name = str(row_copy.get("name", "bin"))
            columns = row_copy.get("grid_columns")
            rows = row_copy.get("grid_rows")
            height = row_copy.get("height")
            params = row_to_parameters(defaults, row_copy)

            scad = args.scad
            if args.plate_position == "front":
                width_mm = float(columns) * 42.0
                depth_mm = float(rows) * 42.0
                rotation_degrees = 0
                if args.orientation == "rotate-90":
                    rotation_degrees = -90
                elif args.orientation == "widest-y" and width_mm > depth_mm:
                    rotation_degrees = -90

                rotated = rotation_degrees in (-90, 90, 270, -270)
                placed_width = depth_mm if rotated else width_mm
                x_offset = args.plate_width / 2.0 - placed_width / 2.0
                y_offset = args.front_margin + (width_mm if rotation_degrees == -90 else 0)
                params["render_position"] = "zero"
                handle = tempfile.NamedTemporaryFile(
                    "w",
                    encoding="utf-8",
                    dir=wrapper_parent,
                    prefix=f".gridfinity-batch-{safe_name(raw_name)}-",
                    suffix=".scad",
                    delete=False,
                )
                wrapper = Path(handle.name)
                temp_files.append(wrapper)
                with handle:
                    handle.write(positioned_scad_source(args.scad, x_offset, y_offset, rotation_degrees))
                scad = wrapper

            for export_format in formats:
                output = args.output_dir / output_name(raw_name, columns, rows, height, export_format)
                command = build_command(openscad_path or args.openscad, scad, output, params)
                command = openscad_parts[:-1] + command
                print(" ".join(command))
                if not args.dry_run:
                    subprocess.run(command, check=True, env=env)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
