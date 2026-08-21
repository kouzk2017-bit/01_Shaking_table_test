"""Export the 2015 10-story 4F/6F result figures as 600 dpi PNG files.

All drift, joint-deformation, shear, and strain curves are read from workbook
cells.  The contribution bars are recalculated from the selected time-history
peaks; embedded Excel chart caches are not used.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_DIRECTORY = SCRIPT_DIRECTORY.parents[1]
COMMON_PYTHON = WORKSPACE_DIRECTORY / "common" / "python"
ARCHIVED_2015_RESULTS = (
    WORKSPACE_DIRECTORY
    / "results"
    / "archive"
    / "2026-07-30_before_cleanup"
    / "2015"
)
sys.path.insert(0, str(COMMON_PYTHON))

from publication_style import (  # noqa: E402
    COLORS,
    apply_style,
    format_axis,
    save_figure,
)
from plot_csv_results import (  # noqa: E402
    draw_contribution_bars,
    draw_selected_peak_markers,
    format_hysteresis_limits,
    format_time_history_limits,
    plot_rebar_strain_figure,
    select_peaks,
)


DEFAULT_WORKBOOK = (
    ARCHIVED_2015_RESULTS / "deliverables" / "spreadsheets" / "10_story.xlsx"
)
DEFAULT_STRAIN_WORKBOOK = (
    ARCHIVED_2015_RESULTS
    / "spreadsheets"
    / "Strain_Grouped_75_104_180_184"
    / "Strain_Grouped_75_104_180_184_20151211-2(JMAKobe100%).xlsx"
)
CASE_NAME_2015 = "20151211-2(JMAKobe100%)"
DEFAULT_OUTPUT = WORKSPACE_DIRECTORY / "results" / "2015" / CASE_NAME_2015


@dataclass(frozen=True)
class StrainSeries:
    member: str
    excel_columns: tuple[str, str]
    source_columns: tuple[int, int]
    labels: tuple[str, str]
    colors: tuple[str, str] = (COLORS["accent"], COLORS["primary"])


# Only change this block when the strain source layout changes.
STRAIN_SHEET = "ExternalStrain"
HEADER_ROW = 1
DATA_START_ROW = 2
TIME_COLUMN = "A"
STRAIN_SERIES = (
    StrainSeries(
        member="4F",
        excel_columns=("B", "C"),
        source_columns=(44, 105),
        labels=("Beam longitudinal rebar", "Column longitudinal rebar"),
    ),
    StrainSeries(
        member="6F",
        excel_columns=("D", "E"),
        source_columns=(179, 185),
        labels=("Beam longitudinal rebar", "Column longitudinal rebar"),
    ),
)

# Descriptive titles replace the workbook's blank chart titles.
CHART_TITLES = {
    1: f"{CASE_NAME_2015} 4F Joint Deformation and Story Drift",
    2: f"{CASE_NAME_2015} 6F Joint Deformation and Story Drift",
    3: f"{CASE_NAME_2015} 4F Joint-Deformation Contribution",
    4: f"{CASE_NAME_2015} 6F Joint-Deformation Contribution",
    5: f"{CASE_NAME_2015} 4F Story Drift-Shear Force Relationship",
    6: f"{CASE_NAME_2015} 6F Story Drift-Shear Force Relationship",
}


def parse_index_spec(value: str) -> set[int]:
    """Parse ``1-8,12,15-17`` into positive chart indices."""
    result: set[int] = set()
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start <= 0 or end < start:
                raise ValueError(f"Invalid chart range: {token}")
            result.update(range(start, end + 1))
        else:
            index = int(token)
            if index <= 0:
                raise ValueError(f"Chart indices must be positive: {token}")
            result.add(index)
    if not result:
        raise ValueError("At least one chart index is required")
    return result


def _safe_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" ._")
    return cleaned[:100] or "untitled"


def _save_figure(fig, output_stem: Path) -> tuple[Path, ...]:
    """Save one publication figure as a 600 dpi PNG and vector PDF."""
    return save_figure(fig, output_stem, formats=("png", "pdf"), mode="paper")


def four_consecutive_peaks(
    time: np.ndarray,
    drift: np.ndarray,
    direction: int,
) -> np.ndarray:
    """Return the shared first four significant, separated peaks."""
    if direction not in (-1, 1):
        raise ValueError("Peak direction must be -1 or 1")
    selected, _ = select_peaks(
        time,
        drift,
        mode="max" if direction > 0 else "min",
        count=4,
        time_window=(10.0, 30.0),
        significance_fraction=0.30,
        minimum_separation_s=0.50,
    )
    return selected


def draw_time_history(
    time: np.ndarray,
    joint: np.ndarray,
    drift: np.ndarray,
    peaks: np.ndarray,
    title: str,
    output_stem: Path,
) -> tuple[Path]:
    style = apply_style("paper")
    fig, ax = plt.subplots(figsize=style.figure_size)
    ax.plot(time, joint, color=COLORS["primary"], label="Joint deformation")
    ax.plot(time, drift, color=COLORS["accent"], linestyle="--", label="Story drift")
    format_axis(ax, xlabel="Time (s)", ylabel="Drift (rad)", title=title, legend=True)
    format_time_history_limits(ax)
    draw_selected_peak_markers(ax, time, drift, peaks, mode="min")
    return _save_figure(fig, output_stem)


def draw_contribution(
    joint: np.ndarray,
    drift: np.ndarray,
    peaks: np.ndarray,
    title: str,
    output_stem: Path,
) -> tuple[Path]:
    style = apply_style("paper")
    contribution = np.abs(joint[peaks] / drift[peaks])
    fig, ax = plt.subplots(figsize=style.figure_size)
    draw_contribution_bars(ax, contribution, labels="ABCD", title=title)
    return _save_figure(fig, output_stem)


def draw_hysteresis(
    drift: np.ndarray,
    shear: np.ndarray,
    title: str,
    output_stem: Path,
) -> tuple[Path]:
    style = apply_style("paper")
    fig, ax = plt.subplots(figsize=style.figure_size)
    ax.plot(drift, shear, color=COLORS["primary"])
    format_axis(ax, xlabel="Story drift (rad)", ylabel="Shear force (kN)", title=title, legend=False)
    format_hysteresis_limits(ax)
    return _save_figure(fig, output_stem)


def _relationship_target(archive: ZipFile, rels_path: str, relationship_id: str) -> str:
    root = ET.fromstring(archive.read(rels_path))
    for relationship in root:
        if relationship.attrib.get("Id") == relationship_id:
            return relationship.attrib["Target"]
    raise ValueError(f"Relationship {relationship_id!r} was not found in {rels_path}")


def _worksheet_path(archive: ZipFile, sheet_name: str) -> str:
    workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
    relationship_id = None
    for sheet in workbook_root.findall(".//{*}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            relationship_id = sheet.attrib.get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            )
            break
    if relationship_id is None:
        available = [item.attrib.get("name", "") for item in workbook_root.findall(".//{*}sheet")]
        raise ValueError(f"Sheet {sheet_name!r} was not found. Available sheets: {available}")
    target = _relationship_target(archive, "xl/_rels/workbook.xml.rels", relationship_id)
    target = target.replace("\\", "/").lstrip("/")
    return target if target.startswith("xl/") else f"xl/{target}"


def _shared_strings(archive: ZipFile) -> tuple[str, ...]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return ()
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return tuple(
        "".join(node.text or "" for node in item.findall(".//{*}t"))
        for item in root.findall("{*}si")
    )


def _column_number(column_letters: str) -> int:
    result = 0
    for character in column_letters.strip().upper():
        if not "A" <= character <= "Z":
            raise ValueError(f"Invalid Excel column: {column_letters!r}")
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def read_numeric_columns(
    workbook_path: Path,
    sheet_name: str,
    columns: tuple[str, ...],
    data_start_row: int,
) -> dict[str, list[float]]:
    """Read selected numeric columns without assuming that data starts at A1."""
    requested = {column.upper(): [] for column in columns}
    column_numbers = {column: _column_number(column) for column in requested}
    with ZipFile(workbook_path, "r") as archive:
        worksheet = ET.fromstring(archive.read(_worksheet_path(archive, sheet_name)))
        shared = _shared_strings(archive)
        for row in worksheet.findall(".//{*}row"):
            row_number = int(row.attrib.get("r", "0"))
            if row_number < data_start_row:
                continue
            row_values: dict[str, float] = {}
            for cell in row.findall("{*}c"):
                reference = cell.attrib.get("r", "")
                match = re.match(r"([A-Z]+)", reference)
                if not match:
                    continue
                column = match.group(1)
                if column not in requested:
                    continue
                value_node = cell.find("{*}v")
                if value_node is None or value_node.text is None:
                    continue
                raw = value_node.text
                if cell.attrib.get("t") == "s":
                    raw = shared[int(raw)]
                try:
                    row_values[column] = float(raw)
                except ValueError:
                    continue
            if all(column in row_values for column in requested):
                for column in requested:
                    requested[column].append(row_values[column])

    if not requested or not all(requested.values()):
        details = ", ".join(
            f"{column} (column {column_numbers[column]})" for column in requested
        )
        raise ValueError(
            f"No complete numeric rows were found in {sheet_name!r}, starting at row "
            f"{data_start_row}, for {details}"
        )
    return requested


def draw_strain_figure(
    time_values: list[float],
    series_values: tuple[list[float], list[float]],
    series: StrainSeries,
    case_name: str,
    output_stem: Path,
) -> tuple[Path]:
    return plot_rebar_strain_figure(
        np.asarray(time_values, dtype=float),
        np.asarray(series_values[0], dtype=float),
        np.asarray(series_values[1], dtype=float),
        output_stem,
        title=f"{case_name} - {series.member}",
    )


def render_mode(
    workbook: Path,
    strain_workbook: Path,
    output_root: Path,
    chart_indices: set[int],
    strain_sheet: str,
    data_start_row: int,
    time_column: str,
) -> list[Path]:
    if not workbook.is_file():
        raise FileNotFoundError(f"Main workbook not found: {workbook}")
    if not strain_workbook.is_file():
        raise FileNotFoundError(f"Strain workbook not found: {strain_workbook}")

    output_dir = output_root / "png"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    drift_columns = read_numeric_columns(
        workbook,
        "Drift_2015",
        ("A", "B", "C", "E", "F", "G"),
        4,
    )
    joint_time = np.asarray(drift_columns["A"], dtype=float)
    drift_time = np.asarray(drift_columns["E"], dtype=float)
    if joint_time.shape != drift_time.shape or not np.allclose(joint_time, drift_time, rtol=0.0, atol=1e-12):
        raise ValueError("2015 joint-deformation and story-drift time axes do not match")

    shear_columns = read_numeric_columns(
        workbook,
        "Drift_Shear_2015",
        ("B", "C", "F", "G"),
        4,
    )
    floor_columns = {
        4: ("B", "F", "B", "F"),
        6: ("C", "G", "C", "G"),
    }
    for offset, floor in enumerate((4, 6)):
        joint_column, drift_column, hysteresis_drift_column, shear_column = floor_columns[floor]
        joint = np.asarray(drift_columns[joint_column], dtype=float)
        drift = np.asarray(drift_columns[drift_column], dtype=float)
        peaks = four_consecutive_peaks(drift_time, drift, direction=-1)

        time_chart_index = 1 + offset
        if time_chart_index in chart_indices:
            title = CHART_TITLES[time_chart_index]
            outputs.extend(
                draw_time_history(
                    drift_time,
                    joint,
                    drift,
                    peaks,
                    title,
                    output_dir / f"chart_{time_chart_index:03d}_{_safe_name(title)}",
                )
            )

        contribution_chart_index = 3 + offset
        if contribution_chart_index in chart_indices:
            title = CHART_TITLES[contribution_chart_index]
            outputs.extend(
                draw_contribution(
                    joint,
                    drift,
                    peaks,
                    title,
                    output_dir / f"chart_{contribution_chart_index:03d}_{_safe_name(title)}",
                )
            )

        hysteresis_chart_index = 5 + offset
        if hysteresis_chart_index in chart_indices:
            title = CHART_TITLES[hysteresis_chart_index]
            outputs.extend(
                draw_hysteresis(
                    np.asarray(shear_columns[hysteresis_drift_column], dtype=float),
                    np.asarray(shear_columns[shear_column], dtype=float),
                    title,
                    output_dir / f"chart_{hysteresis_chart_index:03d}_{_safe_name(title)}",
                )
            )

        contribution = np.abs(joint[peaks] / drift[peaks])
        print(
            f"2015 {floor}F peaks: "
            + ", ".join(
                f"{label}={drift_time[index]:.2f}s ({value:.1%})"
                for label, index, value in zip("ABCD", peaks, contribution)
            )
        )

    requested_columns = [time_column]
    for strain_series in STRAIN_SERIES:
        requested_columns.extend(strain_series.excel_columns)
    column_data = read_numeric_columns(
        strain_workbook,
        strain_sheet,
        tuple(dict.fromkeys(column.upper() for column in requested_columns)),
        data_start_row,
    )
    time_values = column_data[time_column.upper()]
    case_name = CASE_NAME_2015
    for strain_series in STRAIN_SERIES:
        values = tuple(column_data[column] for column in strain_series.excel_columns)
        stem = output_dir / f"{case_name}_{strain_series.member}"
        outputs.extend(
            draw_strain_figure(
                time_values, values, strain_series, case_name, stem
            )
        )
    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--strain-workbook", type=Path, default=DEFAULT_STRAIN_WORKBOOK)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chart-indices", default="1-6", help="2015 charts; default: 1-6")
    parser.add_argument("--strain-sheet", default=STRAIN_SHEET)
    parser.add_argument("--header-row", type=int, default=HEADER_ROW)
    parser.add_argument("--data-start-row", type=int, default=DATA_START_ROW)
    parser.add_argument("--time-column", default=TIME_COLUMN)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.data_start_row <= args.header_row:
        raise ValueError("--data-start-row must be below --header-row")
    chart_indices = parse_index_spec(args.chart_indices)
    non_2015_indices = sorted(chart_indices - set(range(1, 7)))
    if non_2015_indices:
        raise ValueError(
            f"Only the 2015 charts 1-6 are allowed; remove: {non_2015_indices}"
        )
    outputs = render_mode(
        workbook=args.workbook.resolve(),
        strain_workbook=args.strain_workbook.resolve(),
        output_root=args.output_dir.resolve(),
        chart_indices=chart_indices,
        strain_sheet=args.strain_sheet,
        data_start_row=args.data_start_row,
        time_column=args.time_column.upper(),
    )
    folder = args.output_dir.resolve() / "png"
    print(f"Generated {len(outputs)} PNG files in {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
