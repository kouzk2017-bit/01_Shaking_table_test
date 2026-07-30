"""Export selected 2015 10-story figures as PNG files.

Charts 1--6 come from cached OOXML chart data in
``deliverables/spreadsheets/10_story.xlsx``.  The 4F and 6F strain histories
come from configurable cells in the migrated
``10-story_2015/results/spreadsheets`` workbook.  Only the 2015 charts 1--6
are exported.  The source workbooks are opened read-only and each result is
saved as one 600 dpi PNG.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_DIRECTORY = SCRIPT_DIRECTORY.parents[1]
PHD_ROOT = WORKSPACE_DIRECTORY.parents[1]
COMMON_PYTHON = PHD_ROOT / "03_Common_Code" / "plotting" / "python"
sys.path.insert(0, str(COMMON_PYTHON))

from excel_chart_renderer import ChartData, read_excel_charts  # noqa: E402
from plot_style import apply_plot_style, format_axis, resolve_plot_style  # noqa: E402


DEFAULT_WORKBOOK = (
    WORKSPACE_DIRECTORY / "deliverables" / "spreadsheets" / "10_story.xlsx"
)
DEFAULT_STRAIN_WORKBOOK = (
    WORKSPACE_DIRECTORY
    / "10-story_2015"
    / "results"
    / "spreadsheets"
    / "Strain_Grouped_75_104_180_184"
    / "Strain_Grouped_75_104_180_184_20151211-2(JMAKobe100%).xlsx"
)
DEFAULT_OUTPUT = (
    WORKSPACE_DIRECTORY / "deliverables" / "figures" / "10_story_2015"
)


@dataclass(frozen=True)
class StrainSeries:
    member: str
    excel_columns: tuple[str, str]
    source_columns: tuple[int, int]
    labels: tuple[str, str]
    colors: tuple[str, str] = ("#D7191C", "#2166AC")


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
    1: "2015 4F Joint Deformation and Story Drift",
    2: "2015 6F Joint Deformation and Story Drift",
    3: "2015 4F Joint-Deformation Contribution",
    4: "2015 6F Joint-Deformation Contribution",
    5: "2015 4F Story Drift-Shear Force Relationship",
    6: "2015 6F Story Drift-Shear Force Relationship",
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


def _save_figure(fig, output_stem: Path) -> tuple[Path]:
    """Save one publication-style 600 dpi PNG."""
    style = resolve_plot_style("paper")
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    png_path = output_stem.with_suffix(".png")
    fig.savefig(png_path, dpi=style.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return (png_path,)


def draw_embedded_chart(
    chart: ChartData,
    output_stem: Path,
 ) -> tuple[Path]:
    style = apply_plot_style("paper")
    fig, ax = plt.subplots(figsize=style.figure_size)
    primary_type = chart.chart_types[0]
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    # Excel sometimes stores single-point helper series named "Series 3", etc.
    # When named data series exist, omit those helper series from clean exports.
    named_series = tuple(
        series for series in chart.series
        if not re.fullmatch(r"Series \d+", series.name, flags=re.IGNORECASE)
    )
    plot_series = named_series or chart.series

    if primary_type == "barChart":
        categories = tuple(str(value) for value in plot_series[0].x)
        centers = list(range(len(categories)))
        width = 0.35 / max(len(plot_series), 1)
        for index, series in enumerate(plot_series):
            offset = (index - (len(plot_series) - 1) / 2) * width
            ax.bar(
                [center + offset for center in centers], series.y,
                width=width, label=series.name,
            )
        ax.set_xticks(centers, categories)
    else:
        for index, series in enumerate(plot_series):
            is_story_drift = series.name.strip().lower() == "story drift"
            color = "#D7191C" if is_story_drift else colors[index % len(colors)]
            line_style = "--" if is_story_drift else "-"
            ax.plot(
                series.x,
                series.y,
                label=series.name,
                color=color,
                linestyle=line_style,
            )

    format_axis(
        ax,
        xlabel=chart.xlabel or None,
        ylabel=chart.ylabel or None,
        title=CHART_TITLES.get(chart.index, chart.title),
        legend=len(plot_series) > 1,
    )
    # Keep both axis lines connected while giving all tick numbers more room.
    ax.tick_params(axis="x", pad=10)
    ax.tick_params(axis="y", pad=10)
    if chart.x_limits[0] is not None or chart.x_limits[1] is not None:
        ax.set_xlim(left=chart.x_limits[0], right=chart.x_limits[1])
    if chart.y_limits[0] is not None or chart.y_limits[1] is not None:
        ax.set_ylim(bottom=chart.y_limits[0], top=chart.y_limits[1])

    if chart.index in {1, 2}:
        # Drift time histories: use uncluttered integer ticks every five seconds.
        ax.set_xlim(10, 30)
        ax.set_xticks(range(10, 31, 5))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    if chart.index in {5, 6}:
        # Use identical drift ranges for direct comparison of the two loops.
        ax.set_xlim(-0.04, 0.04)
        ax.set_xticks([-0.04, -0.02, 0.00, 0.02, 0.04])

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
    style = apply_plot_style("paper")
    fig, ax = plt.subplots(figsize=style.figure_size)
    for values, label, _source_column, color in zip(
        series_values, series.labels, series.source_columns, series.colors
    ):
        ax.plot(time_values, values, label=label, color=color)

    format_axis(
        ax,
        xlabel="Time (s)",
        ylabel=r"$\epsilon/\epsilon_y$",
        title=f"{case_name} - {series.member}",
        legend=True,
    )
    # Match the spacing used by the other figures without moving either axis line.
    ax.tick_params(axis="x", pad=10)
    ax.tick_params(axis="y", pad=10)
    ax.legend(loc="upper right", frameon=False, fontsize=style.legend_size)
    ax.set_xlim(10, 30)
    ax.set_xticks(range(10, 31, 5))
    ax.set_ylim(-3, 8)
    ax.set_yticks(range(-3, 9))
    return _save_figure(fig, output_stem)


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

    available_charts = read_excel_charts(workbook)
    available_indices = {chart.index for chart in available_charts}
    missing_indices = sorted(chart_indices - available_indices)
    if missing_indices:
        raise ValueError(f"Requested chart indices do not exist: {missing_indices}")

    for chart in available_charts:
        if chart.index not in chart_indices:
            continue
        if "ε/εy" in chart.ylabel or "strain" in chart.title.lower():
            continue
        title = CHART_TITLES.get(chart.index, chart.title)
        stem = output_dir / f"chart_{chart.index:03d}_{_safe_name(title)}"
        outputs.extend(draw_embedded_chart(chart, stem))

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
    case_name = "20151211-2(JMAKobe100%)"
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
