"""Read archived MATLAB workbooks and compare them with generated CSV files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np

from ten_story_pipeline import Case, ProjectSpec, load_csv


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference).group(0)
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - ord("A") + 1
    return value - 1


def read_xlsx_sheet(path: Path, sheet_name: str) -> tuple[list[str], np.ndarray]:
    """Read values from one worksheet using only Python's standard library."""
    with ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{{{MAIN_NS}}}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t")))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relation_id = None
        for sheet in workbook.find(f"{{{MAIN_NS}}}sheets"):
            if sheet.attrib.get("name") == sheet_name:
                relation_id = sheet.attrib[f"{{{REL_NS}}}id"]
                break
        if relation_id is None:
            raise KeyError(f"Worksheet {sheet_name!r} not found in {path.name}")
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = None
        for relation in relationships.findall(f"{{{PKG_REL_NS}}}Relationship"):
            if relation.attrib.get("Id") == relation_id:
                target = relation.attrib["Target"].lstrip("/")
                break
        if target is None:
            raise KeyError(f"Worksheet relationship missing for {sheet_name}")
        xml_path = target if target.startswith("xl/") else f"xl/{target}"
        root = ET.fromstring(archive.read(xml_path))
        rows: list[list[object]] = []
        for row in root.iter(f"{{{MAIN_NS}}}row"):
            values: dict[int, object] = {}
            for cell in row.findall(f"{{{MAIN_NS}}}c"):
                reference = cell.attrib.get("r", "A1")
                index = _column_index(reference)
                cell_type = cell.attrib.get("t")
                value_node = cell.find(f"{{{MAIN_NS}}}v")
                if cell_type == "inlineStr":
                    inline = cell.find(f"{{{MAIN_NS}}}is")
                    value = "" if inline is None else "".join(
                        node.text or "" for node in inline.iter(f"{{{MAIN_NS}}}t")
                    )
                elif value_node is None or value_node.text is None:
                    value = None
                elif cell_type == "s":
                    value = shared[int(value_node.text)]
                elif cell_type in {"str", "b"}:
                    value = value_node.text
                else:
                    value = float(value_node.text)
                values[index] = value
            if values:
                width = max(values) + 1
                rows.append([values.get(index) for index in range(width)])
        if not rows:
            raise ValueError(f"Worksheet {sheet_name} is empty")
        width = max(len(row) for row in rows)
        rows = [row + [None] * (width - len(row)) for row in rows]
        headers = ["" if value is None else str(value) for value in rows[0]]
        numeric = np.full((len(rows) - 1, width), np.nan, dtype=float)
        for row_index, row in enumerate(rows[1:]):
            for column_index, value in enumerate(row):
                if value is not None and value != "":
                    numeric[row_index, column_index] = float(value)
        keep = np.any(np.isfinite(numeric), axis=1)
        return headers, numeric[keep]


def _safe_matlab_name(name: str) -> str:
    return re.sub(r"[^\w]", "_", name)


def _compare(csv_path: Path, workbook: Path, sheet: str) -> dict:
    csv_headers, csv_values = load_csv(csv_path)
    xlsx_headers, xlsx_values = read_xlsx_sheet(workbook, sheet)
    width = min(csv_values.shape[1], xlsx_values.shape[1])
    rows = min(csv_values.shape[0], xlsx_values.shape[0])
    shape_match = csv_values.shape == xlsx_values.shape
    difference = np.abs(csv_values[:rows, :width] - xlsx_values[:rows, :width])
    finite = np.isfinite(difference)
    maximum = float(np.max(difference[finite])) if np.any(finite) else None
    mean = float(np.mean(difference[finite])) if np.any(finite) else None
    return {
        "csv": str(csv_path),
        "workbook": str(workbook),
        "sheet": sheet,
        "csv_shape": list(csv_values.shape),
        "matlab_shape": list(xlsx_values.shape),
        "shape_match": shape_match,
        "header_match": csv_headers == xlsx_headers,
        "max_absolute_difference": maximum,
        "mean_absolute_difference": mean,
        "allclose_atol_1e-10_rtol_1e-9": bool(
            shape_match
            and np.allclose(csv_values, xlsx_values, atol=1e-10, rtol=1e-9, equal_nan=True)
        ),
    }


def validate_case(spec: ProjectSpec, case: Case) -> dict:
    result = spec.result_directory(case)
    csv_directory = result / "csv"
    checks: list[dict] = []
    if spec.year == 2015:
        safe = _safe_matlab_name(case.name)
        spreadsheets = spec.baseline_root / "spreadsheets"
        acceleration = spreadsheets / f"Acceleration_{safe}.xlsx"
        drift = spreadsheets / f"Drift_Results_{safe}.xlsx"
        joint = spreadsheets / f"Joint_{case.name}.xlsx"
        foundation = spreadsheets / f"SLP_Displacement_{safe}.xlsx"
        rebar = spreadsheets / "Strain_Grouped_75_104_180_184" / f"Strain_Grouped_75_104_180_184_{case.name}.xlsx"
    else:
        spreadsheets = spec.baseline_root / "matlab" / "spreadsheets"
        acceleration = spreadsheets / f"Acceleration_{case.name}.xlsx"
        drift = spreadsheets / f"Drift_Results_{case.name}.xlsx"
        joint = spreadsheets / f"Joint_{case.name}.xlsx"
        foundation = Path("__not_applicable__")
        rebar = spreadsheets / f"Rebar_Strain_{case.name}.xlsx"
    mappings = []
    if acceleration.is_file():
        mappings.extend([
            ("floor_acceleration_x.csv", acceleration, "Accx"),
            ("floor_acceleration_y.csv", acceleration, "Accy"),
            ("floor_acceleration_z.csv", acceleration, "Accz"),
            ("story_shear_x.csv", acceleration, "ShearFx"),
            ("story_shear_y.csv", acceleration, "ShearFy"),
            ("table_acceleration.csv", acceleration, "TBL_Response"),
        ])
        if spec.year == 2015:
            mappings.extend([
                ("foundation_acceleration_bf1.csv", acceleration, "Acc_BF1"),
                ("foundation_acceleration_bf2.csv", acceleration, "Acc_BF2"),
            ])
    if drift.is_file():
        mappings.extend([
            ("story_displacement_x.csv", drift, "RelDispX"),
            ("story_displacement_y.csv", drift, "RelDispY"),
            ("absolute_displacement_x.csv", drift, "AbsDispX"),
            ("absolute_displacement_y.csv", drift, "AbsDispY"),
            ("story_drift_x.csv", drift, "RadX"),
            ("story_drift_y.csv", drift, "RadY"),
            ("total_story_displacement_x.csv", drift, "TotalRelDispX"),
            ("total_story_displacement_y.csv", drift, "TotalRelDispY"),
            ("total_absolute_displacement_x.csv", drift, "TotalAbsDispX"),
            ("total_absolute_displacement_y.csv", drift, "TotalAbsDispY"),
            ("total_story_drift_x.csv", drift, "TotalRadX"),
            ("total_story_drift_y.csv", drift, "TotalRadY"),
        ])
    if joint.is_file():
        mappings.append(("joint_rotation.csv", joint, "NodeRotation"))
    if foundation.is_file():
        mappings.extend([
            ("foundation_displacement_x.csv", foundation, "Disp_X"),
            ("foundation_displacement_y.csv", foundation, "Disp_Y"),
        ])
    if rebar.is_file():
        mappings.append((
            "rebar_strain_selected.csv",
            rebar,
            "ExternalStrain" if spec.year == 2015 else "EssentialStrainData",
        ))
    for csv_name, workbook, sheet in mappings:
        csv_path = csv_directory / csv_name
        if csv_path.is_file():
            category = (
                "stateful"
                if csv_name.startswith("total_")
                or (spec.year == 2015 and csv_name == "rebar_strain_selected.csv")
                else "deterministic"
            )
            try:
                check = _compare(csv_path, workbook, sheet)
                check["category"] = category
                check["comparison_available"] = True
                checks.append(check)
            except KeyError as exc:
                checks.append({
                    "csv": str(csv_path),
                    "workbook": str(workbook),
                    "sheet": sheet,
                    "category": category,
                    "comparison_available": False,
                    "reason": str(exc),
                })
    comparable = [item for item in checks if item.get("comparison_available")]
    deterministic = [item for item in comparable if item["category"] == "deterministic"]
    stateful = [item for item in comparable if item["category"] == "stateful"]
    report = {
        "project_year": spec.year,
        "case": case.name,
        "checks": checks,
        "check_count": len(checks),
        "deterministic_checks_pass": bool(deterministic) and all(
            item["allclose_atol_1e-10_rtol_1e-9"] for item in deterministic
        ),
        "stateful_checks_pass": bool(stateful) and all(
            item["allclose_atol_1e-10_rtol_1e-9"] for item in stateful
        ),
        "all_checks_pass": bool(comparable) and all(
            item["allclose_atol_1e-10_rtol_1e-9"] for item in comparable
        ),
    }
    output = result / "validation_against_matlab.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
