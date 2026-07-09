#!/usr/bin/env python3
"""Write a CSV for unique 1x1 through 5x5 bins at heights 6, 12, and 18."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="bins-unique-1x1-through-5x5.csv", type=Path)
    parser.add_argument("--min-size", default=1, type=int)
    parser.add_argument("--max-size", default=5, type=int)
    parser.add_argument("--heights", default="6,12,18")
    args = parser.parse_args()

    heights = [int(value.strip()) for value in args.heights.split(",") if value.strip()]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "grid_columns", "grid_rows", "height"])
        writer.writeheader()
        for height in heights:
            for columns in range(args.min_size, args.max_size + 1):
                for rows in range(columns, args.max_size + 1):
                    writer.writerow(
                        {
                            "name": f"bin_{columns}x{rows}x{height}",
                            "grid_columns": columns,
                            "grid_rows": rows,
                            "height": height,
                        }
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
