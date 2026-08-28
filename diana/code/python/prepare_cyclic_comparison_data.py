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
DRIFT_PER_LOAD_FACTOR_RAD = 0.005
YIELD_STRAIN = 0.002
STEP_PATTERN = re.compile(r"Load-step\s+(\d+)")


@dataclass(frozen=True)
class Condition:
    name: str
    raw_folder: str
    beam_file: str
    column_file: str
    shear_file: str


CONDITIONS = (
    Condition(
        name="origin",
        raw_folder="origin",
        beam_file="EXX_node_1628.csv",
        column_file="EZZ_node_1985.csv",
        shear_file="NX_node_524.csv",
    ),
    Condition(
        name="50pct_axial_force",
        raw_folder="50pct_axial_force",
        beam_file="EXX_node_1628.csv",
        column_file="EZZ_node_1985.csv",
        shear_file="NX_node_524.csv",
    ),
    Condition(
        name="changed_column_longitudinal_rebar",
        raw_folder="改变柱纵筋",
        beam_file="EXX_node_1628.csv",
        column_file="EZZ_node_1845.csv",
        shear_file="NX_node_524.csv",
    ),
    Condition(
        name="four_layer_stirrups",
        raw_folder="四层箍筋",
        beam_file="EXX_node_1628.csv",
        column_file="EZZ_node_1985.csv",
        shear_file="NX_node_524.csv",
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


def verified_response_columns(
    headers: Iterable[str],
    rows: list[dict[str, str]],
) -> tuple[str, ...]:
    """Return verified identical response columns, preserving export order."""
    identifiers = {"case label", "case id", "load factor"}
    columns = tuple(
        header
        for header in headers
        if header not in identifiers
        and any(as_float(row.get(header)) is not None for row in rows)
    )
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
    return columns


def first_response_column(headers: Iterable[str], rows: list[dict[str, str]]) -> str:
    """Return the canonical first response after generic duplicate verification."""
    return verified_response_columns(headers, rows)[0]

def indexed_rows(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    values = {case_id(row): row for row in rows}
    if len(values) != len(rows):
        raise ValueError("Duplicate DIANA case id found")
    return values


def prepare_condition(raw_root: Path, processed_root: Path, condition: Condition, dry_run: bool) -> Path:
    """Create one aligned, plot-ready response table for a loading condition."""
    source = raw_root / condition.raw_folder
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

    individual_outputs = {
        "beam_rebar_response.csv": ("beam_strain", "beam_strain_over_0p002"),
        "column_rebar_response.csv": ("column_strain", "column_strain_over_0p002"),
        "story_shear_response.csv": ("story_shear_kN",),
    }
    shared_columns = ("case_id", "load_factor", "story_drift_rad")
    for filename, response_columns in individual_outputs.items():
        response_output = output.parent / filename
        fieldnames = [*shared_columns, *response_columns]
        with response_output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows({key: row[key] for key in fieldnames} for row in prepared)
        print(f"Wrote {len(prepared)} rows: {response_output}")

    print(f"Wrote {len(prepared)} rows: {output}")
    return output



JOINT_STIRRUP_SOURCES = {
    "origin": ("EXX_node_2375.csv", 2375, "EXX node 2375 element 1359", "EXX node 2375 element 1360"),
    "50pct_axial_force": ("EXX_node_2375.csv", 2375, "EXX node 2375 element 1359", "EXX node 2375 element 1360"),
    "changed_column_longitudinal_rebar": ("EXX_node_2151.csv", 2151, "EXX node 2151 element 1143", "EXX node 2151 element 1144"),
    "four_layer_stirrups": ("EXX_node_2375.csv", 2375, "EXX node 2375 element 1359", "EXX node 2375 element 1360"),
}

def prepare_joint_stirrup_condition(
    raw_root: Path,
    processed_root: Path,
    condition: Condition,
    dry_run: bool,
) -> Path:
    """Standardize the canonical first response after exact duplicate checking."""
    filename, node_tag, first, duplicate = JOINT_STIRRUP_SOURCES[condition.name]
    source = raw_root / condition.raw_folder / filename
    headers, rows = load_diana_rows(source)
    missing = [column for column in (first, duplicate) if column not in headers]
    if missing:
        raise ValueError(f"Missing joint-stirrup response columns in {source}: {missing}")

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
            "node_tag": node_tag,
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
            f"node={node_tag}; canonical={first}; duplicate={duplicate}"
        )
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(prepared[0]))
        writer.writeheader()
        writer.writerows(prepared)


    print(f"Wrote {len(prepared)} rows: {output}")
    return output


CURVE_SOURCE_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "results"
    / "diana"
    / "curve-source-registry.csv"
)
CONDITION_LABELS = {
    "origin": "原轴力",
    "50pct_axial_force": "50%减轴力",
    "changed_column_longitudinal_rebar": "改变柱纵筋",
    "four_layer_stirrups": "四层箍筋",
}


def _node_element_metadata(header: str) -> tuple[str, str]:
    match = re.search(r"node\s+(\d+)\s+element\s+(\d+)", header, re.IGNORECASE)
    return (match.group(1), match.group(2)) if match else ("", "")


def _registry_row(
    raw_root: Path,
    condition: Condition,
    curve: str,
    filename: str,
    output_csv: str,
    conversion: str,
) -> dict[str, str]:
    source = raw_root / condition.raw_folder / filename
    headers, rows = load_diana_rows(source)
    columns = verified_response_columns(headers, rows)
    selected = columns[0]
    node_tag, element_tag = _node_element_metadata(selected)
    return {
        "工况": CONDITION_LABELS[condition.name],
        "工况代码": condition.name,
        "曲线": curve,
        "原始CSV": source.relative_to(raw_root.parent.parent).as_posix(),
        "处理后CSV": f"data/processed/{condition.name}/{output_csv}",
        "选用响应列": selected,
        "节点": node_tag,
        "单元": element_tag,
        "有效响应列数": str(len(columns)),
        "重复响应列": "; ".join(columns[1:]),
        "重复列核验": "所有Load-step逐行完全一致",
        "保留工况步": "11–850",
        "排除工况步": "1–10（轴力加载）",
        "换算/归一化": conversion,
    }


def write_curve_source_registry(raw_root: Path) -> Path:
    """Rewrite the filterable skill-owned curve mapping registry from raw exports."""
    rows: list[dict[str, str]] = []
    for condition in CONDITIONS:
        rows.extend((
            _registry_row(raw_root, condition, "层剪力—层间位移角", condition.shear_file, "story_shear_response.csv", "剪力 N → kN；层间位移角 = load factor × 0.005 rad"),
            _registry_row(raw_root, condition, "梁纵筋应变", condition.beam_file, "beam_rebar_response.csv", "应变 / 0.002"),
            _registry_row(raw_root, condition, "柱纵筋应变", condition.column_file, "column_rebar_response.csv", "应变 / 0.002"),
            _registry_row(raw_root, condition, "节点箍筋应变", JOINT_STIRRUP_SOURCES[condition.name][0], "joint_stirrup_response.csv", "EXX / 0.002"),
        ))
    CURVE_SOURCE_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with CURVE_SOURCE_REGISTRY.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated curve-source registry: {CURVE_SOURCE_REGISTRY}")
    return CURVE_SOURCE_REGISTRY

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
    if not args.dry_run:
        write_curve_source_registry(raw_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
