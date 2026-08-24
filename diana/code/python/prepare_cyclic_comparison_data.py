"""Prepare standard DIANA cyclic-test CSV data for later comparison plotting.

The script is deliberately data-only: it never creates a figure.  It removes
the first ten axial-load steps and writes one normalized response table per
condition under ``diana/data/processed``.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


AXIAL_LOAD_STEPS = 10
DRIFT_PER_LOAD_FACTOR_RAD = 0.025
YIELD_STRAIN = 0.002
STEP_PATTERN = re.compile(r"Load-step\s+(\d+)")


@dataclass(frozen=True)
class Condition:
    name: str
    beam_file: str
    column_file: str
    shear_file: str


CONDITIONS = (
    Condition(
        name="origin",
        beam_file="Beam_rebar_strain_origin.csv",
        column_file="Column_rebar_strain_origin.csv",
        shear_file="story_shear_force_origin.csv",
    ),
    Condition(
        name="50pct_axial_force",
        beam_file="Beam_rebar_strain_50%axialforce.csv",
        column_file="Column_rebar_strain_50%axialforce.csv",
        shear_file="story_shear_force_50%axialforce.csv",
    ),
)


def as_float(value: str | None) -> float | None:
    """Convert a DIANA CSV field to float, retaining missing values as None."""
    if value is None or not value.strip():
        return None
    return float(value)


def load_diana_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a DIANA CSV and discard its units row and non-analysis records."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        rows = [
            row
            for row in reader
            if (row.get("case label") or "").startswith("Load-step")
        ]
    if not rows:
        raise ValueError(f"No DIANA Load-step rows found in {path}")
    return headers, rows


def case_id(row: dict[str, str]) -> int:
    """Use DIANA's case id when present, otherwise parse it from case label."""
    explicit_id = as_float(row.get("case id"))
    if explicit_id is not None:
        return int(explicit_id)
    match = STEP_PATTERN.search(row.get("case label", ""))
    if not match:
        raise ValueError(f"Cannot determine case id from {row.get('case label')!r}")
    return int(match.group(1))


def first_response_column(headers: Iterable[str], rows: list[dict[str, str]]) -> str:
    """Return the first response only after every populated response column matches."""
    identifiers = {"case label", "case id", "load factor"}
    columns = [
        header
        for header in headers
        if header not in identifiers
        and any(as_float(row.get(header)) is not None for row in rows)
    ]
    if not columns:
        raise ValueError("No populated response column found")
    canonical = columns[0]
    canonical_values = [as_float(row.get(canonical)) for row in rows]
    if any(value is None for value in canonical_values):
        raise ValueError(f"Missing response data in canonical column {canonical!r}")
    for header in columns[1:]:
        values = [as_float(row.get(header)) for row in rows]
        if any(value is None for value in values):
            raise ValueError(f"Missing response data in column {header!r}")
        mismatch = next(
            (
                case_id(row)
                for row, first, other in zip(rows, canonical_values, values)
                if first != other
            ),
            None,
        )
        if mismatch is not None:
            raise ValueError(
                f"Populated response columns differ: {canonical!r} and {header!r}; "
                f"explicit mapping required (first mismatching case ID: {mismatch})"
            )
    return canonical

def indexed_rows(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    values = {case_id(row): row for row in rows}
    if len(values) != len(rows):
        raise ValueError("Duplicate DIANA case id found")
    return values


def prepare_condition(raw_root: Path, processed_root: Path, condition: Condition, dry_run: bool) -> Path:
    """Create one aligned, plot-ready response table for a loading condition."""
    source = raw_root / condition.name
    beam_headers, beam_rows = load_diana_rows(source / condition.beam_file)
    column_headers, column_rows = load_diana_rows(source / condition.column_file)
    shear_headers, shear_rows = load_diana_rows(source / condition.shear_file)

    beam_column = first_response_column(beam_headers, beam_rows)
    column_column = first_response_column(column_headers, column_rows)
    shear_column = first_response_column(shear_headers, shear_rows)
    beam_by_case = indexed_rows(beam_rows)
    column_by_case = indexed_rows(column_rows)
    shear_by_case = indexed_rows(shear_rows)
    common_cases = sorted(set(beam_by_case) & set(column_by_case) & set(shear_by_case))
    analysis_cases = [value for value in common_cases if value > AXIAL_LOAD_STEPS]
    if not analysis_cases:
        raise ValueError(f"No cyclic cases remain for {condition.name}")

    prepared: list[dict[str, float | int]] = []
    for identifier in analysis_cases:
        shear_row = shear_by_case[identifier]
        load_factor = as_float(shear_row.get("load factor"))
        beam_strain = as_float(beam_by_case[identifier].get(beam_column))
        column_strain = as_float(column_by_case[identifier].get(column_column))
        shear_force_n = as_float(shear_row.get(shear_column))
        if None in (load_factor, beam_strain, column_strain, shear_force_n):
            raise ValueError(f"Missing response data at case {identifier} in {condition.name}")
        prepared.append({
            "case_id": identifier,
            "load_factor": load_factor,
            "story_drift_rad": load_factor * DRIFT_PER_LOAD_FACTOR_RAD,
            "story_shear_kN": shear_force_n / 1000.0,
            "beam_strain": beam_strain,
            "beam_strain_over_0p002": beam_strain / YIELD_STRAIN,
            "column_strain": column_strain,
            "column_strain_over_0p002": column_strain / YIELD_STRAIN,
        })

    output = processed_root / condition.name / "cyclic_response.csv"
    if dry_run:
        print(
            f"Validated {condition.name}: {len(prepared)} cyclic rows; "
            f"beam={beam_column!r}; column={column_column!r}; shear={shear_column!r}"
        )
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(prepared[0]))
        writer.writeheader()
        writer.writerows(prepared)
    print(f"Wrote {len(prepared)} rows: {output}")
    return output



JOINT_STIRRUP_FILES = {
    "origin": "Joint_stirrup_strain_origin.csv",
    "50pct_axial_force": "Joint_stirrup_strain_50%axialforce.csv",
}
JOINT_STIRRUP_COLUMNS = (
    "EXX node 2375 element 1359",
    "EXX node 2375 element 1360",
)


def prepare_joint_stirrup_condition(
    raw_root: Path,
    processed_root: Path,
    condition: Condition,
    dry_run: bool,
) -> Path:
    """Standardize the canonical first response after exact duplicate checking."""
    source = raw_root / condition.name / JOINT_STIRRUP_FILES[condition.name]
    headers, rows = load_diana_rows(source)
    missing = [column for column in JOINT_STIRRUP_COLUMNS if column not in headers]
    if missing:
        raise ValueError(f"Missing joint-stirrup response columns in {source}: {missing}")
    first, duplicate = JOINT_STIRRUP_COLUMNS
    mismatches = [
        case_id(row)
        for row in rows
        if as_float(row.get(first)) != as_float(row.get(duplicate))
    ]
    if mismatches:
        raise ValueError(
            f"Joint-stirrup response columns differ in {source}; explicit mapping required "
            f"(first mismatching case ID: {mismatches[0]})"
        )
    by_case = indexed_rows(rows)
    cyclic_cases = sorted(case for case in by_case if case > AXIAL_LOAD_STEPS)
    if not cyclic_cases:
        raise ValueError(f"No cyclic joint-stirrup cases remain for {condition.name}")
    prepared = [
        {
            "case_id": identifier,
            "node_tag": 2375,
            "joint_stirrup_exx": as_float(by_case[identifier].get(first)),
        }
        for identifier in cyclic_cases
    ]
    if any(row["joint_stirrup_exx"] is None for row in prepared):
        raise ValueError(f"Missing joint-stirrup response data in {condition.name}")
    output = processed_root / condition.name / "joint_stirrup_response.csv"
    if dry_run:
        print(
            f"Validated {condition.name} joint stirrup: {len(prepared)} cyclic rows; "
            f"node=2375; canonical={first}; duplicate={duplicate}"
        )
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(prepared[0]))
        writer.writeheader()
        writer.writerows(prepared)
    print(f"Wrote {len(prepared)} rows: {output}")
    return output

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without writing CSV files")
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    raw_root = workspace / "diana" / "data" / "raw"
    processed_root = workspace / "diana" / "data" / "processed"
    for condition in CONDITIONS:
        prepare_condition(raw_root, processed_root, condition, args.dry_run)
        prepare_joint_stirrup_condition(raw_root, processed_root, condition, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
