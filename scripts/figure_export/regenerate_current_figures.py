"""Regenerate the current 2015/2018 preview figures with the shared style."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_DIRECTORY = SCRIPT_DIRECTORY.parents[1]
COMMON_PYTHON = WORKSPACE_DIRECTORY / "common" / "python"
CODE_2018 = WORKSPACE_DIRECTORY / "10-story_2018" / "code" / "python"
ARCHIVE_ROOT = (
    WORKSPACE_DIRECTORY
    / "results"
    / "archive"
    / "2026-07-30_before_cleanup"
)
SHARED_PLOT_CONFIG = WORKSPACE_DIRECTORY / "common" / "config" / "plot_config.json"
sys.path.insert(0, str(COMMON_PYTHON))
sys.path.insert(0, str(CODE_2018))

from plot_csv_results import plot_case, plot_rebar_strain_figure  # noqa: E402
from publication_style import apply_style  # noqa: E402
from plot_rebar_strain import _plot_floor, _trace  # noqa: E402
from ten_story_pipeline import load_csv  # noqa: E402


CASES = (
    {
        "year": "2015",
        "name": "20151211-2(JMAKobe100%)",
    },
    {
        "year": "2018",
        "name": "20190109-2(JMAKobe100%)",
    },
)


def regenerate_standard_figures() -> list[Path]:
    outputs: list[Path] = []
    for case in CASES:
        source = ARCHIVE_ROOT / case["year"] / "python" / case["name"]
        target = WORKSPACE_DIRECTORY / "results" / case["year"] / case["name"]
        outputs.extend(
            plot_case(
                source,
                case["name"],
                SHARED_PLOT_CONFIG,
                year=int(case["year"]),
                output_directory=target,
                write_sidecars=False,
            )
        )
    return outputs


def regenerate_2015_rebar_figures() -> list[Path]:
    case_name = "20151211-2(JMAKobe100%)"
    source = (
        ARCHIVE_ROOT
        / "2015"
        / "python"
        / case_name
        / "csv"
        / "rebar_strain_selected.csv"
    )
    target = WORKSPACE_DIRECTORY / "results" / "2015" / case_name
    if not source.is_file():
        raise FileNotFoundError(f"Archived 2015 rebar data not found: {source}")
    headers, data = load_csv(source)
    time = data[:, headers.index("Time_s")]
    outputs: list[Path] = []
    for chart_index, floor in enumerate((4, 6), start=7):
        beam = data[:, headers.index(f"{floor}F_Beam_Longitudinal_Rebar_Col{44 if floor == 4 else 179}")]
        column = data[:, headers.index(f"{floor}F_Column_Longitudinal_Rebar_Col{105 if floor == 4 else 185}")]
        stem = target / f"chart_{chart_index:03d}_{case_name} {floor}F Rebar Strain"
        outputs.extend(plot_rebar_strain_figure(time, beam, column, stem))
    return outputs


def regenerate_2018_rebar_figures() -> list[Path]:
    case_name = "20190109-2(JMAKobe100%)"
    source = ARCHIVE_ROOT / "2018" / "python" / case_name / "data" / "rebar_strain.npz"
    target = WORKSPACE_DIRECTORY / "results" / "2018" / case_name
    if not source.is_file():
        raise FileNotFoundError(f"Archived rebar data not found: {source}")
    apply_style("paper")
    outputs: list[Path] = []
    with np.load(source) as data:
        time = data["time"]
        for chart_index, floor in enumerate((4, 6), start=7):
            stem = target / f"chart_{chart_index:03d}_{case_name} {floor}F Rebar Strain"
            _plot_floor(
                time,
                _trace(data, f"{floor}F_beam"),
                _trace(data, f"{floor}F_column"),
                floor,
                stem,
            )
            outputs.extend((stem.with_suffix(".png"), stem.with_suffix(".pdf")))
    return outputs


def main() -> None:
    outputs = regenerate_standard_figures()
    outputs.extend(regenerate_2015_rebar_figures())
    outputs.extend(regenerate_2018_rebar_figures())
    missing = [path for path in outputs if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Expected figure outputs were not created: {missing}")
    print(f"Generated {len(outputs)} files using the shared publication style.")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
