"""Standardize the solid joint model's exports (origin_2015) for comparison.

Model: beam ends on steel plates restrained along a mid-height y-line
(hinge), matching the shell model's pad-apex supports. Outputs, all with the
ten axial-load steps dropped:

- ``beam_bar_profile.csv`` / ``column_bar_profile.csv`` /
  ``joint_stirrup_profile.csv`` (x-direction leg, EXX) /
  ``joint_stirrup_y_profile.csv`` (y-direction leg, EYY; optional -- only
  when the export exists): every "node N element E" strain column of
  the along-bar exports, as ``n<N>_e<E>`` (raw strain) plus the shared
  ``case_id, load_factor, story_drift_rad``. The two bar elements sharing a
  solid node do not report identical strains, so nothing is collapsed.
- ``story_shear_response.csv``: composed-line section forces next to the
  plates, in kN -- NX of the two column lines (global X = story shear) and NZ
  of the two beam lines (global Z = beam shear). Both end nodes of each
  composed element are exported; they agree to the export's 3 significant
  digits, so the first node of each element is kept.

DIANA names multi-node exports after every node, which can exceed MAX_PATH,
so files are opened with the ``\\\\?\\`` prefix.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import pandas as pd

AXIAL_LOAD_STEPS = 10
DRIFT_PER_LOAD_FACTOR_RAD = 0.005
HEADER_PATTERN = re.compile(r"^[A-Z]+ node (\d+) element (\d+)$")
LOAD_FACTOR_PATTERN = re.compile(r"Load-factor\s+(-?[\d.]+(?:[eE][+-]?\d+)?)")

# output file -> raw file prefix
PROFILES = {
    "beam_bar_profile.csv": "EXX_nodes_10380_",
    "column_bar_profile.csv": "EZZ_nodes_11285_",  # right column bar (DIANA right = test west)
    "column_bar_left_profile.csv": "EZZ_nodes_11145_",  # left column bar (test east), exported from 2026-10-03
    "joint_stirrup_profile.csv": "EXX_nodes_1010",  # 10106_ (x-legs) or 10105_ (whole hoop)
    "joint_stirrup_y_profile.csv": "EYY_nodes_101",  # 10122_ (one y-leg) or 10105_ (whole hoop)
}
OPTIONAL_PROFILES = {"joint_stirrup_y_profile.csv", "column_bar_left_profile.csv"}
SHEAR_FILES = {"column": "NX_nodes_", "beam": "NZ_nodes_"}  # prefixes; a run may export only some of the nodes


def long_path(path: Path) -> str:
    resolved = str(path.resolve())
    return "\\\\?\\" + resolved if os.name == "nt" and not resolved.startswith("\\\\?\\") else resolved


def find_raw(directory: Path, prefix: str) -> Path:
    matches = [name for name in os.listdir(directory) if name.startswith(prefix)]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one '{prefix}*' export in {directory}, found {matches}")
    return directory / matches[0]


def load_export(path: Path) -> pd.DataFrame:
    with open(long_path(path), encoding="utf-8-sig") as stream:
        frame = pd.read_csv(stream, skiprows=[1])
    frame = frame[frame["case label"].str.startswith("Load-step", na=False)].reset_index(drop=True)
    frame.insert(0, "case_id", frame["case label"].str.extract(r"Load-step\s+(\d+)", expand=False).astype(int))
    frame.insert(1, "load_factor", frame["case label"].str.extract(LOAD_FACTOR_PATTERN, expand=False).astype(float))
    if frame["case_id"].duplicated().any():
        raise ValueError(f"Duplicate load step in {path.name}")
    return frame


def response_columns(frame: pd.DataFrame) -> dict[str, str]:
    renamed = {}
    for column in frame.columns:
        match = HEADER_PATTERN.match(column)
        if match:
            renamed[column] = f"n{match.group(1)}_e{match.group(2)}"
    if not renamed:
        raise ValueError("No 'node N element E' response columns found")
    return renamed


def standard(frame: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    out = frame[["case_id", "load_factor", *columns]].rename(columns=columns)
    out.insert(2, "story_drift_rad", out["load_factor"] * DRIFT_PER_LOAD_FACTOR_RAD)
    if out[list(columns.values())].isna().any().any():
        raise ValueError("Missing response values")
    return out[out["case_id"] > AXIAL_LOAD_STEPS].reset_index(drop=True)


def main() -> int:
    model_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=model_root / "data" / "raw" / "origin_2015")
    parser.add_argument("--output-dir", type=Path, default=model_root / "data" / "processed" / "origin_2015")
    parser.add_argument("--partial", action="store_true",
                        help="Skip any missing export (e.g. an interim check of a run still in progress)")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    available = os.listdir(args.input_dir)

    for output_name, prefix in PROFILES.items():
        if (output_name in OPTIONAL_PROFILES or args.partial) and not any(n.startswith(prefix) for n in available):
            print(f"Skipped {output_name}: no '{prefix}*' export")
            continue
        frame = load_export(find_raw(args.input_dir, prefix))
        table = standard(frame, response_columns(frame))
        table.to_csv(args.output_dir / output_name, index=False)
        print(f"Wrote {len(table)} rows x {table.shape[1] - 3} strain columns: {args.output_dir / output_name}")

    shear = None
    for member, prefix in SHEAR_FILES.items():
        if args.partial and not any(n.startswith(prefix) for n in available):
            print(f"Skipped {member} shear: no '{prefix}*' export")
            continue
        frame = load_export(find_raw(args.input_dir, prefix))
        columns = response_columns(frame)
        kept, seen = {}, set()
        for raw, short in columns.items():
            element = short.split("_e")[1]
            if element not in seen:
                seen.add(element)
                kept[raw] = f"{member}_e{element}_shear_kN"
        table = standard(frame, kept)
        table[list(kept.values())] = table[list(kept.values())] / 1000.0
        shear = table if shear is None else shear.merge(
            table.drop(columns=["load_factor", "story_drift_rad"]), on="case_id", validate="one_to_one")
    if shear is not None:
        shear.to_csv(args.output_dir / "story_shear_response.csv", index=False)
        print(f"Wrote {len(shear)} rows: {args.output_dir / 'story_shear_response.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
