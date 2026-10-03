"""Right-beam bottom bar of the test-history DIANA run against the beam-end sensor.

DIANA nodes 1628-1646 run along the right-beam bottom bar from the column
face at 100 mm spacing (1628 at the face).  DIANA right = test WEST, so the
bar corresponds to the G2 east-end bottom bar of the 4F interior joint.

  13  bar strain against distance from the column face at the six large
      test peaks and at the end of the run; the strain gauge
      4G2A-STR-E01 (distance unknown, about 50 mm in the 2018 analogue)
      is marked at 50 mm.
  14  elongation over 0-1000 mm from the column face against time: the
      DIANA bar strain integrated over nodes 1628-1638 vs the wire sensor
      G2EL-DY-1, which measures the length change between the column
      face and a point on the beam soffit 1000 mm away (設置位置一覧
      p.19-20, Y-direction beams).  The bar sits about the cover above
      the soffit, so the soffit elongation is slightly larger than the
      bar elongation; the comparison is of order, not exact.

  15  beam-end rotation over 0-1000 mm against time.  Test: (G2EL - G2EU)
      / 370 mm, with G2EU on the beam side 50 mm below the slab soffit
      (180 mm below the top of the 550 mm beam) and G2EL at the soffit.
      DIANA: (bottom-bar - top-bar elongation) / bar spacing, with the top
      bar from nodes 1418-1436 (1418 at the column face, 100 mm spacing)
      and the spacing taken as BAR_SPACING_MM (assumed, to be confirmed).

Outputs go to ``06_results/comparison/test_vs_shell/2015_4F_history_protocol/``.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(HERE))

from plot_history_protocol_vs_test import (  # noqa: E402
    OUTPUT, PLOT_CONFIG, PROTOCOL, RAW, TIME_WINDOW, YIELD_STRAIN,
    diana_node, map_steps_to_time, read_rows, test_series,
)
from publication_style import COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure  # noqa: E402
from survey_4f_joint_rebar_gauges import read_group  # noqa: E402
import pandas as pd  # noqa: E402

FLOOR = 4
NODES = list(range(1628, 1647))
SPACING_MM = 100.0
GAUGE_LENGTH_MM = 1000.0
PROFILE_FILE = "EXX_nodes_" + "_".join(str(n) for n in NODES) + ".csv"
TOP_NODES = list(range(1418, 1437))
TOP_PROFILE_FILE = "EXX_nodes_" + "_".join(str(n) for n in TOP_NODES) + ".csv"
BAR_SPACING_MM = 450.0     # top-to-bottom bar centres in DIANA (assumed: 550 beam, ~50 mm to each face)
SENSOR_SPACING_MM = 370.0  # G2EU (550 - 130 slab - 50) above G2EL (soffit)
TEST_RAW = WORKSPACE / "02_10-story_2015" / "data" / "raw" / "2015-1211" / "2015-1211-006-1"
PEAK_TIMES_S = (13.57, 14.02, 14.86, 15.68, 16.37, 17.31)


def wire_sensor(jb: int, channel: int) -> tuple[np.ndarray, np.ndarray]:
    """Baseline-corrected sensor record (mm), averaged to 0.01 s."""
    data = pd.read_csv(
        TEST_RAW / f"2015-1211-006-1_ENG_001-{jb:02d}.csv", skiprows=3, header=None,
        usecols=[0, channel], comment="%", encoding="shift_jis",
    ).apply(pd.to_numeric, errors="coerce").dropna().to_numpy()
    usable = data.shape[0] // 10 * 10
    averaged = data[:usable].reshape(-1, 10, 2).mean(axis=1)
    return averaged[:, 0], averaged[:, 1] - data[:1000, 1].mean()


def main() -> None:
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]
    apply_style(mode)

    drift_t, drift = test_series("story_drift_y.csv", f"{FLOOR}F_rad")
    mapping = map_steps_to_time(drift_t, drift)
    steps = np.asarray(sorted(mapping))
    model_t = np.asarray([mapping[s] for s in steps])
    strain = np.column_stack([diana_node(PROFILE_FILE, node, steps) for node in NODES])
    distance = np.arange(len(NODES)) * SPACING_MM

    # 13: strain profile at the test peaks (reversal steps) and at the end.
    reversals = read_rows(PROTOCOL / "reversal_points.csv")
    reversal_times = np.asarray([float(r["time_s"]) for r in reversals])
    gauge_t, gauge = read_group(5, range(6, 7))
    gauge = gauge["4G2A-STR-E01"]
    fig, ax = plt.subplots(figsize=figure_size(mode))
    for k, time in enumerate(PEAK_TIMES_S):
        row = reversals[int(np.argmin(np.abs(reversal_times - time)))]
        step = int(row["end_step"])
        color = f"C{k % 6}"
        style = "-" if float(row["target_drift_rad"]) > 0 else "--"
        ax.plot(distance, strain[np.searchsorted(steps, step)] / YIELD_STRAIN, style, color=color,
                marker="o", label=f"{time:.2f} s, {float(row['target_drift_rad']):+.4f} rad")
        ax.plot(50.0, np.interp(time, gauge_t, gauge), "*", color=color, markersize=12)
    ax.plot(distance, strain[-1] / YIELD_STRAIN, color="0.4", linestyle=":", marker="o", label="End of run")
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel="Distance from column face (mm)", ylabel=r"Bottom bar strain $\epsilon/\epsilon_y$", legend=True)
    ax.set_title("Lines: DIANA nodes 1628-1646; stars: test 4G2A-STR-E01 at assumed 50 mm")
    save_figure(fig, OUTPUT / "13_beam_bottom_bar_strain_profile", formats=("png",), mode=mode)

    # 14: elongation over 0-1000 mm vs the wire sensor G2EL-DY-1.
    within = distance <= GAUGE_LENGTH_MM
    elongation = np.trapezoid(strain[:, within], distance[within], axis=1)
    sensor_t, sensor = wire_sensor(12, 6)  # 710-G2EL-DY-1
    fig, ax = plt.subplots(figsize=figure_size(mode))
    mask = (sensor_t >= TIME_WINDOW[0]) & (sensor_t <= TIME_WINDOW[1])
    ax.plot(sensor_t[mask], sensor[mask], color="0.6", label="Test G2EL-DY-1 (soffit, 0-1000 mm)")
    mask = (model_t >= TIME_WINDOW[0]) & (model_t <= TIME_WINDOW[1])
    ax.plot(model_t[mask], elongation[mask], color=COLORS["primary"], label="DIANA bottom bar, 0-1000 mm")
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel="Elongation (mm)", legend=True)
    save_figure(fig, OUTPUT / "14_beam_bottom_elongation_time_history", formats=("png",), mode=mode)
    # 15: beam-end rotation over 0-1000 mm.
    top = np.column_stack([diana_node(TOP_PROFILE_FILE, node, steps) for node in TOP_NODES])
    top_elongation = np.trapezoid(top[:, within], distance[within], axis=1)
    model_rotation = (elongation - top_elongation) / BAR_SPACING_MM
    upper_t, upper = wire_sensor(12, 5)  # 709-G2EU-DY-1
    test_rotation = (sensor - np.interp(sensor_t, upper_t, upper)) / SENSOR_SPACING_MM
    fig, ax = plt.subplots(figsize=figure_size(mode))
    mask = (sensor_t >= TIME_WINDOW[0]) & (sensor_t <= TIME_WINDOW[1])
    ax.plot(sensor_t[mask], test_rotation[mask], color="0.6", label="Test (G2EL - G2EU) / 370 mm")
    mask = (model_t >= TIME_WINDOW[0]) & (model_t <= TIME_WINDOW[1])
    ax.plot(model_t[mask], model_rotation[mask], color=COLORS["primary"], label=f"DIANA (bottom - top bar) / {BAR_SPACING_MM:.0f} mm")
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel="Beam-end rotation, 0-1000 mm (rad)", legend=True)
    save_figure(fig, OUTPUT / "15_beam_end_rotation_time_history", formats=("png",), mode=mode)
    plt.close("all")

    with (OUTPUT / "beam_bottom_bar_peaks.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "step", "drift_rad", "test_G2EL_mm", "diana_elongation_0_1000_mm",
                         "test_G2EU_mm", "diana_top_elongation_0_1000_mm", "test_rotation_rad", "diana_rotation_rad",
                         "test_4G2A_E01_eps_over_epsy", *[f"diana_{int(d)}mm" for d in distance]])
        for time in PEAK_TIMES_S:
            row = reversals[int(np.argmin(np.abs(reversal_times - time)))]
            index = np.searchsorted(steps, int(row["end_step"]))
            writer.writerow([time, row["end_step"], row["target_drift_rad"],
                             round(float(np.interp(time, sensor_t, sensor)), 2), round(float(elongation[index]), 2),
                             round(float(np.interp(time, upper_t, upper)), 2), round(float(top_elongation[index]), 2),
                             round(float(np.interp(time, sensor_t, test_rotation)), 4), round(float(model_rotation[index]), 4),
                             round(float(np.interp(time, gauge_t, gauge)), 2),
                             *[round(float(v), 2) for v in strain[index] / YIELD_STRAIN]])
    print(f"Peak elongation: test {sensor[(sensor_t > 10) & (sensor_t < 30)].max():.2f} mm, "
          f"DIANA {elongation.max():.2f} mm")


if __name__ == "__main__":
    main()
