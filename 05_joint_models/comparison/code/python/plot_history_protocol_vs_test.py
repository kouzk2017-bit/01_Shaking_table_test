"""Compare the test-history DIANA run with the 2015 shaking-table test in time.

The test-history protocol replays the measured 4F drift reversals, so every
analysis step can be placed on the test time axis: within each leg (between
two reversal times) a step is assigned the first time the measured drift
reaches that step's drift.  Steps whose rounded target lies just beyond the
measured reversal get the reversal time.  The mapping is written to
``processed/origin_history/step_time_map.csv``.

Figures (``06_results/comparison/test_vs_shell/2015_4F_history_protocol/``):
  07  joint deformation angle, test vs model, against time
  08  beam bar strain against time
  09  column bar strain against time (upper column, test-figure position)
  10  story shear normalised by its own peak, against story drift
  11  normalised story shear against time
  12  column bar strain against time (lower column, reference)

The test reports the whole 4F story shear, the model one joint, so shear is
compared only after dividing each by its own peak (shape, not magnitude).
Bar strains (DIANA right = test WEST; gauge mapping in
02_10-story_2015/REBAR_GAUGES.md).  The DIANA mesh is 100 mm, so each test
gauge is compared with the node at the member face and the node 100 mm
away; the gauge distance is unknown (about 50 mm for beams and 80 mm for
columns in the 2018 drawing):
  08  5G21-STR-E01 (G2 east-end bottom bar)  vs right-beam bottom bar,
      nodes 1628 (column face) and 1629 (100 mm into the beam)
  09  5F2AC-STR-02 (5th-story column foot, east)  vs upper-column left bar,
      nodes 1839 (beam face) and 1838 (100 mm above)
  12  4F2AC-STR-18 (4th-story column head, west) vs lower-column right bar,
      node 1985
Since 2026-10-06 the gauges are those of joint 4 (top of story 4, 5F floor), the joint of JNT4;
before, the 4F-floor joint's gauges were used by mistake (one floor too low).
Test strains are read from the raw records with the same baseline and
averaging as the 4F gauge survey; the model starts at 0.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(WORKSPACE / "02_10-story_2015" / "code" / "python"))

from ten_story_pipeline import load_csv  # noqa: E402
from publication_style import COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure  # noqa: E402
from plot_history_vs_standard_protocol import read_response  # noqa: E402
from survey_4f_joint_rebar_gauges import read_group  # noqa: E402

sys.path.insert(0, str(WORKSPACE / "05_joint_models" / "diana_shell" / "code" / "python"))
from prepare_cyclic_comparison_data import case_id, first_response_column, as_float, load_diana_rows  # noqa: E402

CASE = "20151211-2(JMAKobe100%)"
FLOOR = 4
CONDITION = "origin_history"
TEST_CSV = WORKSPACE / "06_results" / "archive" / "2026-07-30_before_cleanup" / "2015" / "python" / CASE / "csv"
PROTOCOL = WORKSPACE / "05_joint_models" / "loading_protocols" / f"2015_{CASE}_{FLOOR}F"
PROCESSED = WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed" / CONDITION
RAW = WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "raw" / "origin_2015_history"
OUTPUT = WORKSPACE / "06_results" / "comparison" / "test_vs_shell" / "2015_4F_history_protocol"
PLOT_CONFIG = WORKSPACE / "08_common" / "config" / "plot_config.json"
TIME_WINDOW = (10.0, 30.0)
YIELD_STRAIN = 0.002

TEST_LABEL = "Test 2015 4F"
MODEL_LABEL = "DIANA (test-history protocol)"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_series(filename: str, column: str) -> tuple[np.ndarray, np.ndarray]:
    headers, data = load_csv(TEST_CSV / filename)
    return data[:, headers.index("Time_s")], data[:, headers.index(column)]


def map_steps_to_time(time: np.ndarray, drift: np.ndarray) -> dict[int, float]:
    """Test time of every protocol step, leg by leg."""
    reversals = read_rows(PROTOCOL / "reversal_points.csv")
    steps = read_rows(PROTOCOL / "load_steps.csv")
    mapping: dict[int, float] = {}
    for leg in range(1, len(reversals)):
        start, end = reversals[leg - 1], reversals[leg]
        direction = np.sign(float(end["target_drift_rad"]) - float(start["target_drift_rad"]))
        window = np.flatnonzero((time >= float(start["time_s"])) & (time <= float(end["time_s"])))
        reach = np.maximum.accumulate(direction * drift[window])
        for row in (r for r in steps if int(r["leg"]) == leg):
            hits = np.flatnonzero(reach >= direction * float(row["story_drift_rad"]) - 1e-12)
            mapping[int(row["step"])] = float(time[window[hits[0]]]) if hits.size else float(end["time_s"])
    return mapping


def diana_node(filename: str, node: int, steps: np.ndarray) -> np.ndarray:
    """One node's response from a raw DIANA export, ordered like ``steps``."""
    headers, rows = load_diana_rows(RAW / filename)
    node_headers = [h for h in headers if f"node {node} " in h]
    column = first_response_column(node_headers, rows)
    by_step = {case_id(row): as_float(row[column]) for row in rows}
    return np.asarray([by_step[int(step)] for step in steps])


def time_overlay(test_t, test_y, model_t, model_y, ylabel: str, name: str, mode: str,
                 test_label: str = TEST_LABEL, model_curves=None) -> None:
    """Test against one model curve, or several given as (values, label) pairs."""
    fig, ax = plt.subplots(figsize=figure_size(mode))
    mask = (test_t >= TIME_WINDOW[0]) & (test_t <= TIME_WINDOW[1])
    ax.plot(test_t[mask], test_y[mask], color="0.6", label=test_label)
    mask = (model_t >= TIME_WINDOW[0]) & (model_t <= TIME_WINDOW[1])
    for (values, label), color, style in zip(model_curves or [(model_y, MODEL_LABEL)], ("C0", "C1", "C2"), ("-", "--", ":")):
        ax.plot(model_t[mask], values[mask], color=color, linestyle=style, label=label)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel=ylabel, legend=True)
    save_figure(fig, OUTPUT / name, formats=("png",), mode=mode)


def main() -> None:
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]
    apply_style(mode)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    drift_t, drift = test_series("story_drift_y.csv", f"{FLOOR}F_rad")
    mapping = map_steps_to_time(drift_t, drift)
    with (PROCESSED / "step_time_map.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["step", "test_time_s"])
        writer.writerows((step, f"{value:.2f}") for step, value in sorted(mapping.items()))

    model = read_response(CONDITION)
    model_t = np.asarray([mapping[int(step)] for step in model["load_step"]])
    angle_t, angle = test_series("joint_rotation.csv", f"{FLOOR}F_rad")
    beam_t, beam = read_group(6, range(20, 21))                  # 5G21-STR-E01
    upper_t, upper = read_group(16, range(2, 3))                 # 5F2AC-STR-02
    lower_t, lower = read_group(6, range(13, 14))                # 4F2AC-STR-18
    steps = model["load_step"]
    shear_t, shear = test_series("story_shear_y.csv", f"{FLOOR}F_kN")

    time_overlay(angle_t, angle, model_t, model["deformation_angle_rad"],
                 "Joint deformation angle (rad)", "07_joint_deformation_time_history", mode)
    strain = r" $\epsilon/\epsilon_y$"
    time_overlay(beam_t, beam["5G21-STR-E01"], model_t, None, "Beam bottom bar strain" + strain,
                 "08_beam_bar_strain_time_history", mode, "Test 5G21-STR-E01", [
                     (diana_node("EXX_node_1628.csv", 1628, steps) / YIELD_STRAIN, "DIANA 1628 (column face)"),
                     (diana_node("EXX_node_1629.csv", 1629, steps) / YIELD_STRAIN, "DIANA 1629 (100 mm from face)"),
                 ])
    time_overlay(upper_t, upper["5F2AC-STR-02"], model_t, None, "Upper column bar strain" + strain,
                 "09_column_bar_strain_time_history", mode, "Test 5F2AC-STR-02", [
                     (diana_node("EZZ_nodes_1838_1839.csv", 1839, steps) / YIELD_STRAIN, "DIANA 1839 (beam face)"),
                     (diana_node("EZZ_nodes_1838_1839.csv", 1838, steps) / YIELD_STRAIN, "DIANA 1838 (100 mm above)"),
                 ])
    time_overlay(lower_t, lower["4F2AC-STR-18"], model_t, None, "Lower column bar strain" + strain,
                 "12_lower_column_bar_strain_time_history", mode, "Test 4F2AC-STR-18", [
                     (diana_node("EZZ_node_1985.csv", 1985, steps) / YIELD_STRAIN, "DIANA 1985"),
                 ])

    test_norm = shear / np.max(np.abs(shear))
    model_norm = model["story_shear_kN"] / np.max(np.abs(model["story_shear_kN"]))
    fig, ax = plt.subplots(figsize=figure_size(mode))
    ax.plot(drift[: shear.size], test_norm[: drift.size], color="0.6", label=TEST_LABEL)
    ax.plot(model["story_drift_rad"], model_norm, color=COLORS["primary"], label=MODEL_LABEL)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel="Story drift (rad)", ylabel=r"Story shear / peak $V/V_{max}$", legend=True)
    save_figure(fig, OUTPUT / "10_normalized_shear_vs_story_drift", formats=("png",), mode=mode)
    time_overlay(shear_t, test_norm, model_t, model_norm,
                 r"Story shear / peak $V/V_{max}$", "11_normalized_shear_time_history", mode)
    plt.close("all")

    print(f"Mapped {len(mapping)} steps to test time; test shear peak {np.max(np.abs(shear)):.0f} kN, "
          f"model {np.max(np.abs(model['story_shear_kN'])):.0f} kN")


if __name__ == "__main__":
    main()
