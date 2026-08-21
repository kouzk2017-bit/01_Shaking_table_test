"""Create the six 2018 figures using the existing 2015 publication style."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import CASE_NAME, DATA_DIRECTORY, FIGURE_DIRECTORY, PLOT_END, PLOT_START


COMMON_PYTHON = Path(__file__).resolve().parents[3] / "common" / "python"
sys.path.insert(0, str(COMMON_PYTHON))

from publication_style import (  # noqa: E402
    COLORS,
    apply_style,
    figure_size,
    format_axis,
    save_figure,
)
from plot_csv_results import (  # noqa: E402
    draw_contribution_bars,
    draw_selected_peak_markers,
    format_hysteresis_limits,
    format_time_history_limits,
    select_peaks,
)


FIGURE_SIZE = figure_size("paper")


def save(fig, stem: Path) -> None:
    save_figure(fig, stem, formats=("png", "pdf"), mode="paper")


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
        time_window=(PLOT_START, PLOT_END),
        significance_fraction=0.30,
        minimum_separation_s=0.50,
    )
    return selected


def plot_time_history(time, joint, drift, peaks: np.ndarray, stem: Path) -> None:
    mask = (time >= PLOT_START) & (time <= PLOT_END)
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.plot(time[mask], joint[mask], color=COLORS["primary"], label="Joint deformation")
    ax.plot(time[mask], drift[mask], color=COLORS["accent"], linestyle="--", label="Story drift")
    format_axis(ax, "Time (s)", "Drift (rad)", legend=True)
    format_time_history_limits(ax, time_window=(PLOT_START, PLOT_END))
    draw_selected_peak_markers(ax, time, drift, peaks, mode="max")
    save(fig, stem)


def plot_contribution(joint, drift, peaks: np.ndarray, stem: Path) -> np.ndarray:
    contribution = np.abs(joint[peaks] / drift[peaks])
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    draw_contribution_bars(ax, contribution, labels="ABCD")
    save(fig, stem)
    return contribution


def plot_hysteresis(time, drift, shear, stem: Path) -> None:
    mask = (time >= PLOT_START) & (time <= PLOT_END)
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.plot(drift[mask], shear[mask], color=COLORS["primary"])
    format_axis(ax, "Story drift (rad)", "Shear force (kN)")
    format_hysteresis_limits(ax)
    save(fig, stem)


def process() -> dict[str, np.ndarray]:
    drift_data = np.load(DATA_DIRECTORY / "story_drift.npz")
    shear_data = np.load(DATA_DIRECTORY / "story_shear.npz")
    joint_data = np.load(DATA_DIRECTORY / "joint_rotation.npz")
    time = drift_data["time"]
    if not (np.array_equal(time, shear_data["time"]) and np.array_equal(time, joint_data["time"])):
        raise ValueError("Drift, shear, and joint-rotation time axes do not match")

    apply_style()
    summary: dict[str, np.ndarray] = {}
    for chart_offset, floor in enumerate((4, 6)):
        column = floor - 1
        joint = joint_data["joint_rotation"][:, column]
        drift = drift_data["story_drift_y"][:, column]
        shear = shear_data["shear_y"][:, column]
        peaks = four_consecutive_peaks(time, drift, direction=1)
        plot_time_history(
            time, joint, drift, peaks,
            FIGURE_DIRECTORY / f"chart_{1 + chart_offset:03d}_{CASE_NAME} {floor}F Joint Deformation and Story Drift",
        )
        contribution = plot_contribution(
            joint, drift, peaks,
            FIGURE_DIRECTORY / f"chart_{3 + chart_offset:03d}_{CASE_NAME} {floor}F Joint-Deformation Contribution",
        )
        plot_hysteresis(
            time, drift, shear,
            FIGURE_DIRECTORY / f"chart_{5 + chart_offset:03d}_{CASE_NAME} {floor}F Story Drift-Shear Force Relationship",
        )
        summary[f"{floor}F_peak_indices"] = peaks
        summary[f"{floor}F_peak_times"] = time[peaks]
        summary[f"{floor}F_contribution"] = contribution
    np.savez_compressed(DATA_DIRECTORY / "figure_metrics.npz", **summary)
    return summary


if __name__ == "__main__":
    metrics = process()
    print(f"Generated six figures in {FIGURE_DIRECTORY}")
    for key, value in metrics.items():
        if key.endswith("contribution"):
            print(key, np.array2string(value, precision=4))
