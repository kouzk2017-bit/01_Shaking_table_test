"""Joint 3 (4F floor) member-end rotations: shell model joint3 (standard protocol) vs the test sensors.

Test (JB12, test_data.member_end_displacement, story 3 drift, 10-30 s):
  beam   (L - U) / 350 mm over 1000 mm from the column face, + = soffit opens; left = G1W, right = G2E
  column (E - W) / 300 mm over 600 mm, + = east (DIANA left) face opens; upper foot 4C2B, lower head 3C2T
Model: total displacements of the nodes at the sensor ends (user 2026-10-10, 8-node mesh), same formulas
with the mesh spacings:
  right beam  near 2 (L) / 616 (U), far 1072 (L) / 1106 (U); U-L 366.66 mm, gauge 1000 mm
  left beam   near 3 (L) / 613 (U), far 727 (L) / 761 (U)
  upper column  244 / 206 left (E), 241 / 203 right (W); gauge 614.98, lever arm 300 mm
  lower column  19 / 166 left (E), 22 / 160 right (W); gauge 620.43, lever arm 300 mm
Output: 06_results/comparison/test_vs_shell/2015_3F_standard_protocol/joint3/04-07_*.png
The test column readings exceed the story drift (see joints/README.md), so 06/07 are qualitative.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
sys.path.insert(0, str(WORKSPACE / "02_10-story_2015" / "code" / "python"))

import test_data  # noqa: E402
from publication_style import (  # noqa: E402
    COLORS, PROJECT_MODE, TEST_COLOR, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure,
)

SHELL = WORKSPACE / "05_joint_models" / "diana_shell" / "data"
RAW, PROCESSED = SHELL / "raw" / "joint3_2015", SHELL / "processed" / "joint3"
OUTPUT = WORKSPACE / "06_results" / "comparison" / "test_vs_shell" / "2015_3F_standard_protocol" / "joint3"
TIME_WINDOW = (10.0, 30.0)
TEST_BEAM_SPACING, MODEL_BEAM_SPACING, COLUMN_SPACING = 350.0, 366.66, 300.0
X_LIMIT = 0.045


def model_displacements() -> pd.DataFrame:
    """TDtX / TDtZ of every exported node by load step, columns 'X<node>' / 'Z<node>'."""
    frames = []
    for path in sorted(RAW.glob("TDt[XZ]_nodes_*.csv")):
        raw = pd.read_csv(path, skiprows=[1])
        axis = path.name[3]
        raw.index = raw["case label"].str.extract(r"Load-step (\d+)", expand=False).astype(int)
        raw = raw.filter(like="node")
        raw.columns = [f"{axis}{c.split()[-1]}" for c in raw.columns]
        frames.append(raw)
    data = pd.concat(frames, axis=1)
    drift = pd.read_csv(PROCESSED / "cyclic_response.csv").set_index("case_id")["story_drift_rad"]
    return data.join(drift, how="inner")


def model_rotations(d: pd.DataFrame) -> dict[str, np.ndarray]:
    right_l, right_u = d["X1072"] - d["X2"], d["X1106"] - d["X616"]
    left_l, left_u = d["X3"] - d["X727"], d["X613"] - d["X761"]
    upper = ((d["Z244"] - d["Z206"]) - (d["Z241"] - d["Z203"])) / COLUMN_SPACING
    lower = ((d["Z19"] - d["Z166"]) - (d["Z22"] - d["Z160"])) / COLUMN_SPACING
    return {"left_beam": ((left_l - left_u) / MODEL_BEAM_SPACING).to_numpy(),
            "right_beam": ((right_l - right_u) / MODEL_BEAM_SPACING).to_numpy(),
            "upper_column": upper.to_numpy(), "lower_column": lower.to_numpy()}


def test_rotations() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    names = ["G1WL-DY-1", "G1WU-DY-1", "G2EL-DY-1", "G2EU-DY-1"] + [
        f"{p}-DZ-{s}" for p in ("4C2B", "3C2T") for s in ("NE", "SE", "NW", "SW")]
    t, m = test_data.member_end_displacement(names)
    t_d, drift = test_data.story("story_drift_y", 3)
    keep = (t >= TIME_WINDOW[0]) & (t <= TIME_WINDOW[1])

    def column(p):
        east = (m[f"{p}-DZ-NE"] + m[f"{p}-DZ-SE"]) / 2
        west = (m[f"{p}-DZ-NW"] + m[f"{p}-DZ-SW"]) / 2
        return (east - west) / COLUMN_SPACING

    rot = {"left_beam": (m["G1WL-DY-1"] - m["G1WU-DY-1"]) / TEST_BEAM_SPACING,
           "right_beam": (m["G2EL-DY-1"] - m["G2EU-DY-1"]) / TEST_BEAM_SPACING,
           "upper_column": column("4C2B"), "lower_column": column("3C2T")}
    return np.interp(t, t_d, drift)[keep], {k: v[keep] for k, v in rot.items()}


FIGURES = (
    ("04_left_beam_end_rotation_vs_story_drift", "left_beam", "Left beam-end rotation (rad)"),
    ("05_right_beam_end_rotation_vs_story_drift", "right_beam", "Right beam-end rotation (rad)"),
    ("06_upper_column_foot_rotation_vs_story_drift", "upper_column", "Upper column-foot rotation (rad)"),
    ("07_lower_column_head_rotation_vs_story_drift", "lower_column", "Lower column-head rotation (rad)"),
)


def main() -> None:
    apply_style(PROJECT_MODE)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    d = model_displacements()
    model = model_rotations(d)
    test_drift, test = test_rotations()
    for name, key, ylabel in FIGURES:
        fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
        ax.plot(test_drift, test[key], color=TEST_COLOR, linewidth=plt.rcParams["lines.linewidth"] * 0.6, label="Test")
        ax.plot(d["story_drift_rad"], model[key], color=COLORS["primary"], label="DIANA shell")
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
        ax.set_xlim(-X_LIMIT, X_LIMIT)
        ax.set_ylim((-0.05, 0.05) if "column" in key else (-0.04, 0.04))
        format_axis(ax, xlabel="Story 3 drift (rad)", ylabel=ylabel, legend=True)
        save_figure(fig, OUTPUT / name, formats=("png",), mode=PROJECT_MODE)
        plt.close(fig)
    # values at the largest test-like drifts for the README
    drift = d["story_drift_rad"].to_numpy()
    for target in (0.01, -0.01, 0.02, -0.02, 0.03, -0.03):
        k = np.flatnonzero(np.isclose(drift, target, atol=2e-4))
        if len(k):
            k = k[0]
            print(f"model drift {target:+.2f}: " + ", ".join(f"{key} {model[key][k]:+.4f}" for key in model))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
