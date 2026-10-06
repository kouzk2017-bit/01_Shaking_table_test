"""Compare solid joint runs under the test-history protocol with the 2015 test in time.

The solid runs use the same 1119-step test-history protocol as the shell run
(``05_joint_models/loading_protocols/``), so every analysis step is placed on
the test time axis with the same leg-by-leg mapping as
plot_history_protocol_vs_test.py (``map_steps_to_time``).

Per case (``06_results/comparison/test_vs_solid/2015_4F_history_protocol/<case>/``,
next to the 01-03 response-vs-drift figures):
  04  story drift: test vs protocol (checks the step-to-time mapping)
  05  joint deformation angle
  06  story shear normalised by its own peak (test = whole 4F story, model = one joint)
  07  beam bottom bar strain: test 5G21-STR-E01 (G2 east-end bottom bar) vs solid
      right-beam bottom bar at the column face (node 10402 / element 2953) and
      100 mm into the beam (10403 / 2954); the solid bar tracks shell node 1628
  10  left-beam bottom bar: test 5G11-STR-W01 (G1 west-end bottom bar, DIANA left beam) vs solid
      node 10396 / element 2947, 100 mm from the left column face
  Test gauges are at joint 4 (top of story 4 = 5F floor, same joint as JNT4; see REBAR_GAUGES.md section 5).
  08  upper-column bar at the beam-top face: test 5F2AC-STR-02 (5th-story column foot,
      east) vs solid LEFT column bar (nodes 11145-11172, exported 2026-10-03) at
      the face, node 11162 / element 3711, and 100 mm above, 11163 / 3712
  09  lower-column bar at the beam-bottom face: test 4F2AC-STR-18 (4th-story column head,
      west) vs solid RIGHT column bar (11285-11312) at the face, 11296 / 3839, and
      100 mm below, 11295 / 3838
      DIANA right = test west. Column bar nodes are numbered upward: faces are
      11156 (bottom) / 11162 (top) on the left bar and 11296 / 11302 on the right
      bar (identified 2026-10-03 from where each bar yields and from correlation
      with shell nodes 1839 upper-left / 1985 lower-right).

07-09 draw one DIANA curve each, the node 100 mm from the member face: the gauge
offset is unknown for 2015 (about 50 mm for beams and 80 mm for columns in the
2018 drawing), and the element right at the face carries a strain spike from
localization. The face-node values stay in the processed profiles.

Summary over all cases (``.../2015_4F_history_protocol/``):
  summary_01_shear_at_reversals, summary_02_joint_ratio_at_reversals and
  summary_reversals.csv: V/Vmax and joint angle / story drift at each protocol
  reversal; the test value is taken where |drift| peaks within +-0.15 s of the
  reversal time.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from publication_style import COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure  # noqa: E402
from plot_history_protocol_vs_test import PROTOCOL, TIME_WINDOW, map_steps_to_time, read_group, test_series  # noqa: E402

FLOOR = 4
YIELD_STRAIN = 0.002
SOLID = WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed"
OUTPUT = WORKSPACE / "06_results" / "comparison" / "test_vs_solid" / "2015_4F_history_protocol"
SHEAR_COLUMN = "column_e1783_shear_kN"
TEST_COLOR, MODEL_COLOR = COLORS["primary"], COLORS["accent"]  # same pairing as the 01-03 figures
# history-protocol cases, in the order they were run: folder, legend label
CASES = (
    ("origin_2015_parabolic_history", "Gc 26.6, residual 0"),
    ("origin_2015_parabolic_residual_history", "Gc 26.6, residual 9.6 MPa"),
    ("origin_2015_parabolic_gc61_residual_history", "Gc 61, residual 9.6 MPa"),
    ("origin_2015_parabolic_gc61_residual20_history", "Gc 61, residual 20 MPa"),
)
CASE_COLORS = (COLORS["sky"], COLORS["green"], COLORS["orange"], COLORS["accent"])


def read_case(case: str) -> pd.DataFrame:
    """Story drift, shear and joint angle of one solid case, by load step."""
    shear = pd.read_csv(SOLID / case / "story_shear_response.csv")
    joint = pd.read_csv(SOLID / case / "joint_deformation_angle.csv")
    frame = shear.merge(joint[["load_step", "deformation_angle_rad"]], left_on="case_id", right_on="load_step")
    return frame.set_index("case_id")


def time_overlay(test_curves, model_t, model_curves, ylabel: str, path: Path) -> None:
    """One test curve (time, values, label) and one model curve on the mapped time axis."""
    fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
    for t, y, label in test_curves:
        mask = (t >= TIME_WINDOW[0]) & (t <= TIME_WINDOW[1])
        ax.plot(t[mask], y[mask], color=TEST_COLOR, label=label)
    mask = (model_t >= TIME_WINDOW[0]) & (model_t <= TIME_WINDOW[1])
    for values, label in model_curves:
        ax.plot(model_t[mask], np.asarray(values)[mask], color=MODEL_COLOR, label=label)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel=ylabel, legend=True, legend_location="best")
    save_figure(fig, path, formats=("png",), mode="paper")
    plt.close(fig)


def plot_case(case: str, mapping: dict[int, float]) -> None:
    out = OUTPUT / case
    model = read_case(case)
    model = model[model.index.isin(list(mapping))]
    model_t = np.asarray([mapping[int(step)] for step in model.index])
    label = "DIANA solid"

    drift_t, drift = test_series("story_drift_y.csv", f"{FLOOR}F_rad")
    time_overlay([(drift_t, drift, "Test 2015 4F")], model_t, [(model["story_drift_rad"], label + " (protocol)")],
                 "Story drift (rad)", out / "04_story_drift_time_history")
    angle_t, angle = test_series("joint_rotation.csv", f"{FLOOR}F_rad")
    time_overlay([(angle_t, angle, "Test 2015 4F")], model_t, [(model["deformation_angle_rad"], label)],
                 "Joint deformation angle (rad)", out / "05_joint_deformation_time_history")
    shear_t, shear = test_series("story_shear_y.csv", f"{FLOOR}F_kN")
    time_overlay([(shear_t, shear / np.max(np.abs(shear)), "Test 2015 4F")], model_t,
                 [(model[SHEAR_COLUMN] / model[SHEAR_COLUMN].abs().max(), label)],
                 r"Story shear / peak $V/V_{max}$", out / "06_normalized_shear_time_history")

    strain = r", $\epsilon/\epsilon_{\mathrm{y}}$"
    beam_file, column_file = SOLID / case / "beam_bar_profile.csv", SOLID / case / "column_bar_profile.csv"
    if beam_file.exists():
        beam = pd.read_csv(beam_file).set_index("case_id").reindex(model.index)
        beam_t, gauges = read_group(6, range(20, 21))
        time_overlay([(beam_t, gauges["5G21-STR-E01"], "Test 5G21-STR-E01")], model_t, [
            (beam["n10403_e2954"] / YIELD_STRAIN, "DIANA solid (10403, 100 mm from face)"),
        ], "Beam bottom bar strain" + strain, out / "07_beam_bar_strain_time_history")
        left_t, left_gauges = read_group(6, range(15, 16))
        time_overlay([(left_t, left_gauges["5G11-STR-W01"], "Test 5G11-STR-W01")], model_t, [
            (beam["n10396_e2947"] / YIELD_STRAIN, "DIANA solid (10396, 100 mm from face)"),
        ], "Left beam bottom bar strain" + strain, out / "10_left_beam_bar_strain_time_history")
    left_file = SOLID / case / "column_bar_left_profile.csv"
    if left_file.exists():
        left = pd.read_csv(left_file).set_index("case_id").reindex(model.index)
        upper_t, upper = read_group(16, range(2, 3))
        time_overlay([(upper_t, upper["5F2AC-STR-02"], "Test 5F2AC-STR-02")], model_t, [
            (left["n11163_e3712"] / YIELD_STRAIN, "DIANA solid (11163, 100 mm above face)"),
        ], "Upper column bar strain" + strain, out / "08_upper_column_bar_strain_time_history")
    if column_file.exists():
        column = pd.read_csv(column_file).set_index("case_id").reindex(model.index)
        lower_t, lower = read_group(6, range(13, 14))
        time_overlay([(lower_t, lower["4F2AC-STR-18"], "Test 4F2AC-STR-18")], model_t, [
            (column["n11295_e3838"] / YIELD_STRAIN, "DIANA solid (11295, 100 mm below face)"),
        ], "Lower column bar strain" + strain, out / "09_lower_column_bar_strain_time_history")
    print(f"{case}: time-history figures in {out}")


def reversal_table() -> pd.DataFrame:
    drift_t, drift = test_series("story_drift_y.csv", f"{FLOOR}F_rad")
    shear_t, shear = test_series("story_shear_y.csv", f"{FLOOR}F_kN")
    angle_t, angle = test_series("joint_rotation.csv", f"{FLOOR}F_rad")
    reversals = pd.read_csv(PROTOCOL / "reversal_points.csv").iloc[1:]
    cases = {case: read_case(case) for case, _ in CASES if (SOLID / case).exists()}
    rows = []
    for _, rev in reversals.iterrows():
        window = np.flatnonzero(np.abs(drift_t - rev["time_s"]) <= 0.15)
        k = window[np.argmax(np.abs(drift[window]))]
        row = {"reversal": int(rev["index"]), "end_step": int(rev["end_step"]), "drift_rad": rev["target_drift_rad"],
               "test_V_over_Vmax": np.interp(drift_t[k], shear_t, shear) / np.max(np.abs(shear)),
               "test_joint_ratio": np.interp(drift_t[k], angle_t, angle) / drift[k]}
        for case, frame in cases.items():
            step = int(rev["end_step"])
            if step in frame.index:
                row[f"{case}_V_over_Vmax"] = frame.loc[step, SHEAR_COLUMN] / frame[SHEAR_COLUMN].abs().max()
                row[f"{case}_joint_ratio"] = frame.loc[step, "deformation_angle_rad"] / frame.loc[step, "story_drift_rad"]
        rows.append(row)
    return pd.DataFrame(rows)


def plot_summary(table: pd.DataFrame) -> None:
    table.round(3).to_csv(OUTPUT / "summary_reversals.csv", index=False)
    large = table[table["drift_rad"].abs() >= 0.0125]  # the small tail cycles say little about the joint
    for stem, key, ylabel in (("summary_01_shear_at_reversals", "V_over_Vmax", r"$|V|/V_{max}$ at reversal"),
                              ("summary_02_joint_ratio_at_reversals", "joint_ratio",
                               "Joint deformation angle / story drift")):
        fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
        x = large["reversal"]
        ax.plot(x, large[f"test_{key}"].abs(), color=COLORS["black"], marker="s", label="Test 2015 4F")
        for (case, label), color in zip(CASES, CASE_COLORS):
            column = f"{case}_{key}"
            if column in large:
                ax.plot(x, large[column].abs(), color=color, marker="o", label=label)
        ax.set_xticks(x, [f"{r}\n{d:+.4f}" for r, d in zip(x, large["drift_rad"])])
        format_axis(ax, xlabel="Reversal (story drift, rad)", ylabel=ylabel, legend=True, legend_location="best")
        save_figure(fig, OUTPUT / stem, formats=("png",), mode="paper")
        plt.close(fig)
    print(f"Summary in {OUTPUT}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", action="append", help="solid case folder(s); default: every case in CASES")
    args = parser.parse_args()

    apply_style("paper")
    drift_t, drift = test_series("story_drift_y.csv", f"{FLOOR}F_rad")
    mapping = map_steps_to_time(drift_t, drift)
    for case in args.case or [case for case, _ in CASES if (SOLID / case).exists()]:
        plot_case(case, mapping)
    plot_summary(reversal_table())


if __name__ == "__main__":
    main()
