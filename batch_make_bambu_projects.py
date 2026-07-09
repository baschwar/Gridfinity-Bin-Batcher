#!/usr/bin/env python3
"""Wrap all source 3MF bins into Bambu Studio project 3MF files."""

from __future__ import annotations

import argparse
from pathlib import Path

from make_bambu_project_3mf import create_project, fmt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("exports/3mf/source"))
    parser.add_argument("--output-dir", type=Path, default=Path("exports/3mf/bambu"))
    parser.add_argument("--template", type=Path, default=Path("templates/bambu/gridfinity_bin_template.3mf"))
    parser.add_argument("--front-margin", default=5.0, type=float)
    parser.add_argument("--plate-width", default=256.0, type=float)
    parser.add_argument("--rotate-z", default=90, type=int, choices=(0, 90, 180, 270))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    sources = sorted(args.source_dir.glob("bin_*.3mf"))
    if not sources:
        raise FileNotFoundError(f"No bin_*.3mf files found in {args.source_dir}")
    if not args.template.exists():
        raise FileNotFoundError(args.template)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(sources, start=1):
        output = args.output_dir / source.name
        if output.exists() and not args.force:
            print(f"[{index}/{len(sources)}] skip existing {output}", flush=True)
            continue

        stats = create_project(args.template, source, output, args.front_margin, args.plate_width, args.rotate_z)
        print(
            f"[{index}/{len(sources)}] wrote {output} "
            f"span={fmt(stats['span_x'])}x{fmt(stats['span_y'])}x{fmt(stats['span_z'])} "
            f"front_y={fmt(stats['front_edge_y'])} rotate_z={fmt(stats['rotate_z'])}",
            flush=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
