"""Command-line entry for the 2018 raw-data-to-CSV workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parents[3] / "common" / "python"
sys.path.insert(0, str(COMMON))

from ten_story_pipeline import list_available_cases, run_case  # noqa: E402
from workflow_config import SPEC  # noqa: E402

PLOT_CONFIG = Path(__file__).resolve().parents[3] / "common" / "config" / "plot_config.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--case", help="Case index or unique part of the case name")
    group.add_argument("--all-loading", action="store_true", help="Process all main loading cases with raw data")
    group.add_argument("--all-available", action="store_true", help="Process every case that has raw data")
    group.add_argument("--list-cases", action="store_true", help="List cases and available JB files")
    parser.add_argument("--then-plot", action="store_true", help="After calculation, explicitly run the separate CSV plotting stage")
    parser.add_argument("--analyses", nargs="+", default=None, choices=("acceleration", "displacement", "joint", "rebar"))
    args = parser.parse_args()
    if args.list_cases:
        print(json.dumps(list_available_cases(SPEC), ensure_ascii=False, indent=2))
        return 0
    if args.all_loading:
        cases = [SPEC.case(index) for index in SPEC.loading_indices if SPEC.raw_directory(SPEC.case(index)).is_dir()]
    elif args.all_available:
        cases = [SPEC.case(item["index"]) for item in list_available_cases(SPEC)]
    else:
        cases = [SPEC.case(args.case or 20)]
    for case in cases:
        metadata = run_case(SPEC, case, args.analyses or ("acceleration", "displacement", "joint", "rebar"))
        print(f"Completed {case.index}: {case.name}")
        for name, reason in metadata["skipped_analyses"].items():
            print(f"  skipped {name}: {reason}")
        if args.then_plot:
            from plot_csv_results import plot_case
            plot_case(SPEC.result_directory(case), case.name, PLOT_CONFIG, year=SPEC.year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
