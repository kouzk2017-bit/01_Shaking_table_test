"""Create 2015 figures from existing result CSV files without reading raw data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parents[3] / "common" / "python"
sys.path.insert(0, str(COMMON))

from plot_csv_results import plot_case  # noqa: E402
from workflow_config import SPEC  # noqa: E402

CONFIG = Path(__file__).resolve().parents[3] / "common" / "config" / "plot_config.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="20", help="Case index or unique part of the case name")
    parser.add_argument("--config", type=Path, default=CONFIG, help="Plot configuration JSON")
    args = parser.parse_args()
    case = SPEC.case(args.case)
    outputs = plot_case(SPEC.result_directory(case), case.name, args.config, year=SPEC.year)
    print(f"Created {len(outputs)} figures from CSV only: {case.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
