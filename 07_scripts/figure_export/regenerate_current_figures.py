"""Regenerate the current 2015/2018 preview figures with the shared style."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_DIRECTORY = SCRIPT_DIRECTORY.parents[1]
COMMON_PYTHON = WORKSPACE_DIRECTORY / "08_common" / "python"
CODE_2018 = WORKSPACE_DIRECTORY / "03_10-story_2018" / "code" / "python"
ARCHIVE_ROOT = (
    WORKSPACE_DIRECTORY
    / "06_results"
    / "archive"
    / "2026-07-30_before_cleanup"
)
SHARED_PLOT_CONFIG = WORKSPACE_DIRECTORY / "08_common" / "config" / "plot_config.json"
sys.path.insert(0, str(COMMON_PYTHON))
sys.path.insert(0, str(CODE_2018))

from plot_csv_results import plot_case, plot_rebar_strain_figure  # noqa: E402
from plot_rebar_strain import _trace  # noqa: E402
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


def _style_mode() -> str:
    """Figure style from the shared plot config (paper or presentation)."""
    config = json.loads(SHARED_PLOT_CONFIG.read_text(encoding="utf-8"))
    return config["figure"]["style_mode"]


def regenerate_standard_figures() -> list[Path]:
    outputs: list[Path] = []
    for case in CASES:
        source = ARCHIVE_ROOT / case["year"] / "python" / case["name"]
        target = WORKSPACE_DIRECTORY / "06_results" / "experiment" / case["year"] / case["name"]
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
    target = WORKSPACE_DIRECTORY / "06_results" / "experiment" / "2015" / case_name
    # Current pipeline output (02_10-story_2015/code/python/run_pipeline.py),
    # not the 2026-07-30 archive: the 4F beam channel changed on 2026-10-01.
    source = target / "csv" / "rebar_strain_selected.csv"
    if not source.is_file():
        raise FileNotFoundError(f"2015 rebar data not found (run run_pipeline.py --analyses rebar): {source}")
    # Read through test_data so the residual switch (02_10-story_2015/config/test_data_options.json)
    # applies here too; the selected CSV itself always carries the residual of the earlier runs.
    sys.path.insert(0, str(WORKSPACE_DIRECTORY / "02_10-story_2015" / "code" / "python"))
    import test_data
    tags = {"Joint4_RightBeamBottom_5G21-STR-E01": "5G21-STR-E01", "Joint4_UpperColumnLeft_5F2AC-STR-02": "5F2AC-STR-02",
            "Joint4_LeftBeamBottom_5G11-STR-W01": "5G11-STR-W01", "Joint4_LowerColumnRight_4F2AC-STR-18": "4F2AC-STR-18"}
    time, series = test_data.rebar_gauges(list(tags.values()), case_name)
    headers = list(tags)
    data = np.column_stack([series[tags[h]] for h in headers])
    outputs: list[Path] = []
    # Joint 4 (5F floor, JNT4) gauges since 2026-10-08: 007 = the two positions compared with
    # the DIANA models, 008 = the other beam end and column end.
    pairs = ((7, "right beam + upper column", "Joint4_RightBeamBottom_5G21-STR-E01", "Joint4_UpperColumnLeft_5F2AC-STR-02"),
             (8, "left beam + lower column", "Joint4_LeftBeamBottom_5G11-STR-W01", "Joint4_LowerColumnRight_4F2AC-STR-18"))
    for chart_index, title, beam_header, column_header in pairs:
        beam = data[:, headers.index(beam_header)]
        column = data[:, headers.index(column_header)]
        stem = target / f"chart_{chart_index:03d}_{case_name} Joint 4 Rebar Strain ({title})"
        outputs.extend(plot_rebar_strain_figure(time, beam, column, stem, mode=_style_mode()))
    return outputs


def regenerate_2018_rebar_figures() -> list[Path]:
    case_name = "20190109-2(JMAKobe100%)"
    source = ARCHIVE_ROOT / "2018" / "python" / case_name / "data" / "rebar_strain.npz"
    target = WORKSPACE_DIRECTORY / "06_results" / "experiment" / "2018" / case_name
    if not source.is_file():
        raise FileNotFoundError(f"Archived rebar data not found: {source}")
    outputs: list[Path] = []
    with np.load(source) as data:
        time = data["time"]
        for chart_index, floor in enumerate((4, 6), start=7):
            stem = target / f"chart_{chart_index:03d}_{case_name} {floor}F Rebar Strain"
            outputs.extend(
                plot_rebar_strain_figure(
                    time,
                    _trace(data, f"{floor}F_beam"),
                    _trace(data, f"{floor}F_column"),
                    stem,
                    mode=_style_mode(),
                )
            )
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
