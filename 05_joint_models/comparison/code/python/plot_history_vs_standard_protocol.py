"""Compare the shell joint model under the standard and the test-history protocol.

Same model (``origin``), two loading protocols:
  * standard:  one cycle each at +-0.005/0.01/0.02/0.03/0.04 rad
  * history:   the 2015 Kobe 100% 4F measured drift reversals
               (``05_joint_models/loading_protocols/``)

The protocols differ in step count, so everything is compared response vs
response (story drift on the x axis), never step vs step.  The history run is
additionally compared with the test at the A-D peaks: its reversal points are
matched to the test peaks by time, so the model is read at the same loading
point the test is.
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
sys.path.insert(0, str(WORKSPACE / "05_joint_models" / "diana_shell" / "code" / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from publication_style import COLORS, apply_style, figure_size, format_axis, line_width, reference_line_kwargs, save_figure  # noqa: E402
from plot_csv_results import select_peaks  # noqa: E402
from plot_joint_deformation_angle import read_condition  # noqa: E402
from plot_experiment_vs_model_joint_drift import load_experiment_floor  # noqa: E402

CASE = "20151211-2(JMAKobe100%)"
FLOOR = 4
PROCESSED = WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed"
EXPERIMENT_CSV = WORKSPACE / "06_results" / "experiment" / "2015" / CASE / "csv"
REVERSALS = WORKSPACE / "05_joint_models" / "loading_protocols" / f"2015_{CASE}_{FLOOR}F" / "reversal_points.csv"
OUTPUT = WORKSPACE / "06_results" / "comparison" / "test_vs_shell" / "2015_4F_history_protocol" / "origin_history"
PLOT_CONFIG = WORKSPACE / "08_common" / "config" / "plot_config.json"
YIELD_STRAIN = 0.002

STANDARD = ("origin", "Standard protocol")
HISTORY = ("origin_history", "Test-history protocol")


def read_response(condition: str) -> dict[str, np.ndarray]:
    """Joint angle, drift, shear and bar strains of one condition, by load step."""
    data = read_condition(PROCESSED, condition)
    columns: dict[int, dict[str, float]] = {}
    for filename in ("cyclic_response.csv", "joint_stirrup_response.csv"):
        with (PROCESSED / condition / filename).open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                columns.setdefault(int(row["case_id"]), {}).update(
                    {key: float(value) for key, value in row.items() if key != "case_id"}
                )
    for key in ("story_shear_kN", "beam_strain", "column_strain", "joint_stirrup_exx"):
        data[key] = np.asarray([columns[step][key] for step in data["load_step"]])
    return data


def peak_steps_for_test_peaks(test_times: np.ndarray) -> list[int]:
    """History-protocol step at the reversal matching each test peak time."""
    with REVERSALS.open(newline="", encoding="utf-8") as stream:
        reversals = list(csv.DictReader(stream))
    times = np.asarray([float(row["time_s"]) for row in reversals])
    steps = []
    for time in test_times:
        nearest = int(np.argmin(np.abs(times - time)))
        if abs(times[nearest] - time) > 0.05:
            raise ValueError(f"No protocol reversal at test peak t={time:.2f} s")
        steps.append(int(reversals[nearest]["end_step"]))
    return steps


def first_reach_step(data: dict[str, np.ndarray], drift: float) -> int:
    """First standard-protocol step that reaches ``drift`` in the same direction."""
    reached = np.flatnonzero(np.sign(drift) * data["story_drift_rad"] >= abs(drift) - 1e-9)
    if not reached.size:
        raise ValueError(f"Standard protocol never reaches {drift:+.4f} rad")
    return int(data["load_step"][reached[0]])


def at_step(data: dict[str, np.ndarray], step: int, key: str) -> float:
    return float(data[key][np.flatnonzero(data["load_step"] == step)[0]])


def overlay(standard, history, key: str, ylabel: str, name: str, mode: str, scale: float = 1.0) -> None:
    fig, ax = plt.subplots(figsize=figure_size(mode))
    ax.plot(standard["story_drift_rad"], standard[key] * scale, "--", color=COLORS["accent"], label=STANDARD[1])
    ax.plot(history["story_drift_rad"], history[key] * scale, color=COLORS["primary"], label=HISTORY[1])
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel="Story drift (rad)", ylabel=ylabel, legend=True)
    save_figure(fig, OUTPUT / name, formats=("png",), mode=mode)


def main() -> None:
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]
    apply_style(mode)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    standard = read_response(STANDARD[0])
    history = read_response(HISTORY[0])
    test = load_experiment_floor(EXPERIMENT_CSV, FLOOR)
    test_peaks, _ = select_peaks(test["time_s"], test["story_drift_rad"], mode="min", count=4, time_window=(10.0, 30.0))

    # 1. Story shear vs story drift.
    overlay(standard, history, "story_shear_kN", "Story shear (kN)", "01_story_shear_vs_story_drift", mode)

    # 2. Joint deformation angle vs story drift, with the test.
    fig, ax = plt.subplots(figsize=figure_size(mode))
    ax.plot(test["story_drift_rad"], test["deformation_angle_rad"], color="0.6",
            linewidth=line_width(0.5), label="Test 2015 4F")
    ax.plot(standard["story_drift_rad"], standard["deformation_angle_rad"], "--", color=COLORS["accent"], label=STANDARD[1])
    ax.plot(history["story_drift_rad"], history["deformation_angle_rad"], color=COLORS["primary"], label=HISTORY[1])
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel="Story drift (rad)", ylabel="Joint deformation angle (rad)", legend=True)
    save_figure(fig, OUTPUT / "02_joint_deformation_vs_story_drift", formats=("png",), mode=mode)

    # 3-5. Reinforcement strains vs story drift.
    overlay(standard, history, "joint_stirrup_exx", r"Joint stirrup strain $\epsilon/\epsilon_y$", "03_joint_stirrup_strain_vs_story_drift", mode, 1 / YIELD_STRAIN)
    overlay(standard, history, "beam_strain", r"Beam bar strain $\epsilon/\epsilon_y$", "04_beam_bar_strain_vs_story_drift", mode, 1 / YIELD_STRAIN)
    overlay(standard, history, "column_strain", r"Column bar strain $\epsilon/\epsilon_y$", "05_column_bar_strain_vs_story_drift", mode, 1 / YIELD_STRAIN)

    # 6. Joint-deformation contribution at the test A-D peaks.
    history_steps = peak_steps_for_test_peaks(test["time_s"][test_peaks])
    rows = []
    for label, index, step in zip("ABCD", test_peaks, history_steps):
        drift = float(test["story_drift_rad"][index])
        standard_step = first_reach_step(standard, drift)
        row = {
            "peak": label,
            "test_time_s": float(test["time_s"][index]),
            "test_drift_rad": drift,
            "test_ratio": abs(float(test["deformation_angle_rad"][index]) / drift),
            "history_step": step,
            "history_drift_rad": at_step(history, step, "story_drift_rad"),
            "history_ratio": abs(at_step(history, step, "deformation_angle_rad") / at_step(history, step, "story_drift_rad")),
            "history_shear_kN": at_step(history, step, "story_shear_kN"),
            "standard_step": standard_step,
            "standard_drift_rad": at_step(standard, standard_step, "story_drift_rad"),
            "standard_ratio": abs(at_step(standard, standard_step, "deformation_angle_rad") / at_step(standard, standard_step, "story_drift_rad")),
            "standard_shear_kN": at_step(standard, standard_step, "story_shear_kN"),
        }
        rows.append(row)
    with (OUTPUT / "peak_contribution.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, ax = plt.subplots(figsize=figure_size(mode))
    positions = np.arange(len(rows))
    width = 0.27
    for offset, key, color, label in (
        (-width, "test_ratio", "0.6", "Test 2015 4F"),
        (0.0, "standard_ratio", COLORS["accent"], STANDARD[1]),
        (width, "history_ratio", COLORS["primary"], HISTORY[1]),
    ):
        ax.bar(positions + offset, [row[key] for row in rows], width, color=color, label=label)
    ax.set_xticks(positions, [row["peak"] for row in rows])
    ax.set_ylim(0.0, 1.0)
    format_axis(ax, xlabel="Peak", ylabel="Joint rotation / story drift ratio", legend=True)
    save_figure(fig, OUTPUT / "06_peak_contribution", formats=("png",), mode=mode)
    plt.close("all")

    for row in rows:
        print(
            f"{row['peak']}: test {row['test_drift_rad']:+.4f} ratio {row['test_ratio']:.3f} | "
            f"history step {row['history_step']} {row['history_drift_rad']:+.4f} ratio {row['history_ratio']:.3f} V {row['history_shear_kN']:.0f} | "
            f"standard step {row['standard_step']} {row['standard_drift_rad']:+.4f} ratio {row['standard_ratio']:.3f} V {row['standard_shear_kN']:.0f}"
        )


if __name__ == "__main__":
    main()
