"""The one way figure / comparison scripts read the 2015 shaking-table test data.

Everything comes from the CSVs written by run_pipeline.py in
06_results/experiment/2015/<case>/csv/ -- no script reads the raw records itself.
Where a processing choice exists it is a switch in ../../config/test_data_options.json:

  rebar_include_previous_runs_residual  rebar strain with / without the residual of earlier runs
  joint_angle_geometry                  gauge frame for the joint deformation angle
  joint_diagonal_geometry               diagonal length for the diagonal strain

Usage:
    import test_data
    t, drift = test_data.story("story_drift_y", 4)          # story 4, rad
    t, angle = test_data.joint_angle("4F")                   # JNT4 (joint 4)
    t, d1, d2 = test_data.joint_diagonal_strain("4F")
    t, gauges = test_data.rebar_gauges(["5G21-STR-E01"])     # strain / eps_y
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[2]            # 02_10-story_2015
WORKSPACE = PROJECT.parent
OPTIONS_FILE = PROJECT / "config" / "test_data_options.json"
DEFAULT_CASE = "20151211-2(JMAKobe100%)"

# Gauge frames of the JNT displacement transducers: (a, b) in mm.
GEOMETRY = {
    "kang_270x270": (270.0, 270.0),                                   # pipeline / Kang Fig.13
    "anchor_286x420": (500.0 - 2 * 107.0, 550.0 - 50.0 - 80.0),       # paper Fig.2 anchors
}
PIPELINE_GEOMETRY = "kang_270x270"   # coefficient used inside joint_rotation.csv


def options() -> dict:
    data = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("//")}


def csv_dir(case: str = DEFAULT_CASE) -> Path:
    return WORKSPACE / "06_results" / "experiment" / "2015" / case / "csv"


def _read(name: str, case: str) -> pd.DataFrame:
    return pd.read_csv(csv_dir(case) / f"{name}.csv")


def _coefficient(geometry: str) -> float:
    a, b = GEOMETRY[geometry]
    return float(np.hypot(a, b) / (2 * a * b))


def story(name: str, story_number: int, case: str = DEFAULT_CASE) -> tuple[np.ndarray, np.ndarray]:
    """A per-story series, e.g. story("story_drift_y", 4) or story("story_shear_y", 4) (column nF = story n)."""
    frame = _read(name, case)
    column = next(c for c in frame.columns if c.startswith(f"{story_number}F_"))
    return frame["Time_s"].to_numpy(), frame[column].to_numpy()


def joint_angle(label: str, case: str = DEFAULT_CASE, geometry: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Joint deformation angle (rad) of the JNT pair labelled ``label`` in joint_rotation.csv ("4F" = JNT4)."""
    geometry = geometry or options()["joint_angle_geometry"]
    frame = _read("joint_rotation", case)
    scale = _coefficient(geometry) / _coefficient(PIPELINE_GEOMETRY)
    return frame["Time_s"].to_numpy(), frame[f"{label}_rad"].to_numpy() * scale


def joint_diagonal_strain(label: str, case: str = DEFAULT_CASE,
                          geometry: str | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unfiltered diagonal strains d/L of the two JNT transducers (joint expansion kept)."""
    geometry = geometry or options()["joint_diagonal_geometry"]
    length = float(np.hypot(*GEOMETRY[geometry]))
    frame = _read("joint_diagonal_displacement", case)
    return (frame["Time_s"].to_numpy(), frame[f"{label}_DY1_mm"].to_numpy() / length,
            frame[f"{label}_DY2_mm"].to_numpy() / length)


def rebar_channel_map(case: str = DEFAULT_CASE) -> pd.DataFrame:
    return _read("rebar_channel_map", case)


def rebar_gauges(tags, case: str = DEFAULT_CASE,
                 include_residual: bool | None = None) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Strain / eps_y of the named gauges (rebar_strain_all.csv covers 10-30 s)."""
    if include_residual is None:
        include_residual = options()["rebar_include_previous_runs_residual"]
    mapping = rebar_channel_map(case).set_index("tag")
    strain = _read("rebar_strain_all", case)
    series = {}
    for tag in tags:
        row = mapping.loc[tag]
        values = strain[f"{row['column']}_eps_over_epsy"].to_numpy()
        series[tag] = values if include_residual else values - row["previous_runs_residual_eps_over_epsy"]
    return strain["Time_s"].to_numpy(), series


def rebar_channels(jb: int, channels, case: str = DEFAULT_CASE,
                   include_residual: bool | None = None) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Same as rebar_gauges, selected by acquisition box and channel numbers."""
    mapping = rebar_channel_map(case)
    tags = [mapping.loc[(mapping["jb"] == jb) & (mapping["channel"] == ch), "tag"].iloc[0] for ch in channels]
    return rebar_gauges(tags, case, include_residual)


def member_end_displacement(names, case: str = DEFAULT_CASE) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Member-end displacement transducers at joint 3 (JB12), mm, unfiltered: e.g. "G1WL-DY-1", "3C2T-DZ-NE"."""
    frame = _read("member_end_displacement", case)
    return frame["Time_s"].to_numpy(), {n: frame[f"{n}_mm"].to_numpy() for n in names}
