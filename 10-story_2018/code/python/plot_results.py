"""Create the six 2018 figures using the existing 2015 publication style."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import DATA_DIRECTORY, FIGURE_DIRECTORY, PLOT_END, PLOT_START


FIGURE_SIZE = (6.0, 4.5)
DPI = 600


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "figure.figsize": FIGURE_SIZE,
        "axes.labelsize": 14,
        "axes.linewidth": 1.0,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "legend.fontsize": 12,
        "legend.frameon": False,
        "lines.linewidth": 1.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def format_axis(ax, xlabel: str, ylabel: str, legend: bool = False) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.tick_params(direction="in", top=True, right=True, width=1.0, pad=8)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
    if legend:
        ax.legend(frameon=False, loc="upper right")


def save(fig, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(stem.with_suffix(".png"), dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def four_negative_peaks(time: np.ndarray, drift: np.ndarray) -> np.ndarray:
    """Return four major, time-separated negative drift peaks A--D."""
    window = (time >= PLOT_START) & (time <= PLOT_END)
    indices = np.flatnonzero(window)
    local = indices[1:-1][
        (drift[indices[1:-1]] <= drift[indices[:-2]]) &
        (drift[indices[1:-1]] < drift[indices[2:]])
    ]
    threshold = -0.30 * np.max(np.abs(drift[window]))
    candidates = local[drift[local] <= threshold]
    ranked = candidates[np.argsort(drift[candidates])]
    selected: list[int] = []
    minimum_separation = int(round(0.50 / (time[1] - time[0])))
    for index in ranked:
        if all(abs(int(index) - previous) >= minimum_separation for previous in selected):
            selected.append(int(index))
        if len(selected) == 4:
            break
    if len(selected) != 4:
        raise ValueError("Could not identify four separated negative drift peaks")
    return np.asarray(sorted(selected), dtype=int)


def plot_time_history(time, joint, drift, floor: int, stem: Path) -> None:
    mask = (time >= PLOT_START) & (time <= PLOT_END)
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.plot(time[mask], joint[mask], color="#1f77b4", label="Joint deformation")
    ax.plot(time[mask], drift[mask], color="#D7191C", linestyle="--", label="Story drift")
    format_axis(ax, "Times (s)", "Drift (rad)", legend=True)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_xticks(np.arange(10, 31, 5))
    ax.set_ylim(-0.04, 0.04)
    ax.set_yticks(np.arange(-0.04, 0.041, 0.01))
    save(fig, stem)


def plot_contribution(time, joint, drift, stem: Path) -> tuple[np.ndarray, np.ndarray]:
    peaks = four_negative_peaks(time, drift)
    contribution = np.abs(joint[peaks] / drift[peaks])
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.bar(list("ABCD"), contribution, width=0.35, color="#1f77b4")
    format_axis(ax, "", r"Contribution of joint deformation $\eta$")
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks(np.arange(0.0, 1.01, 0.2))
    save(fig, stem)
    return peaks, contribution


def plot_hysteresis(time, drift, shear, stem: Path) -> None:
    mask = (time >= PLOT_START) & (time <= PLOT_END)
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.plot(drift[mask], shear[mask], color="#1f77b4")
    format_axis(ax, "Story drift (rad)", "Shear force (kN)")
    ax.set_xlim(-0.04, 0.04)
    ax.set_xticks(np.arange(-0.04, 0.041, 0.02))
    ax.set_ylim(-4000, 4000)
    ax.set_yticks(np.arange(-4000, 4001, 1000))
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
        plot_time_history(
            time, joint, drift, floor,
            FIGURE_DIRECTORY / f"chart_{1 + chart_offset:03d}_2018 {floor}F Joint Deformation and Story Drift",
        )
        peaks, contribution = plot_contribution(
            time, joint, drift,
            FIGURE_DIRECTORY / f"chart_{3 + chart_offset:03d}_2018 {floor}F Joint-Deformation Contribution",
        )
        plot_hysteresis(
            time, drift, shear,
            FIGURE_DIRECTORY / f"chart_{5 + chart_offset:03d}_2018 {floor}F Story Drift-Shear Force Relationship",
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
