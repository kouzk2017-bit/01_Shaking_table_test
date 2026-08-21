"""Compare generated 2018 CSV files with archived MATLAB workbooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parents[3] / "common" / "python"
sys.path.insert(0, str(COMMON))

from matlab_baseline import validate_case  # noqa: E402
from workflow_config import SPEC  # noqa: E402


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--case", default="20")
args = parser.parse_args()
report = validate_case(SPEC, SPEC.case(args.case))
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["deterministic_checks_pass"] else 1)
