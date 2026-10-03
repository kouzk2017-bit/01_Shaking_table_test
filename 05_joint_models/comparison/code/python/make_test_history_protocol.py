"""Build DIANA loading protocols that replay a measured story-drift history.

The standard DIANA protocol (one cycle each at +-0.005/0.01/0.02/0.03/0.04 rad)
cannot be compared point-for-point with a shaking-table record: the test jumps
between amplitudes, repeats the largest one and ends with decaying cycles on a
damaged joint.  This script turns the measured 4F story drift of one test case
into a displacement-controlled protocol with the same reversal sequence.

Reversal points are extracted with a range gate: a reversal is kept only when
the drift then moves back by at least ``--gate`` rad, so sub-gate wiggles are
absorbed into the surrounding leg.  Targets are rounded to the protocol step
(0.0005 rad = load factor 0.1), keeping the same constant step size as the
standard protocol.  Steps 1-10 stay reserved for the axial load, so the first
cyclic step is 11, as in the existing models.

Outputs per case (``05_joint_models/loading_protocols/<name>/``):
  reversal_points.csv   measured and rounded reversal points
  load_steps.csv        every analysis step with its load factor and drift
  diana_load_steps.txt  explicit step sizes in DIANA ``size(count)`` form
Figures go to ``06_results/loading_protocols/``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from ten_story_pipeline import load_csv  # noqa: E402
from publication_style import (  # noqa: E402
    COLORS,
    apply_style,
    figure_size,
    format_axis,
    reference_line_kwargs,
    save_figure,
)

ARCHIVE = WORKSPACE / "06_results" / "archive" / "2026-07-30_before_cleanup"
PROTOCOL_ROOT = WORKSPACE / "05_joint_models" / "loading_protocols"
FIGURE_ROOT = WORKSPACE / "06_results" / "loading_protocols"
PLOT_CONFIG = WORKSPACE / "08_common" / "config" / "plot_config.json"
STANDARD_PROTOCOL = (
    WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed" / "origin" / "cyclic_response.csv"
)

DRIFT_PER_LOAD_FACTOR_RAD = 0.005  # same as prepare_cyclic_comparison_data.py
LOAD_FACTOR_STEP = 0.1
DRIFT_STEP_RAD = DRIFT_PER_LOAD_FACTOR_RAD * LOAD_FACTOR_STEP
AXIAL_LOAD_STEPS = 10

CASES = {
    "2015": "20151211-2(JMAKobe100%)",
    "2018": "20190109-2(JMAKobe100%)",
}


def extract_reversals(time: np.ndarray, drift: np.ndarray, gate: float) -> list[tuple[float, float]]:
    """Reversal points of ``drift`` whose following range is at least ``gate``."""
    reversals: list[tuple[float, float]] = [(float(time[0]), 0.0)]
    direction = 0
    extreme = 0
    for index in range(1, drift.size):
        value = drift[index]
        if direction == 0:
            if abs(value) >= gate:
                direction = 1 if value > 0 else -1
                extreme = index
            continue
        if direction * (value - drift[extreme]) > 0:
            extreme = index
        elif direction * (drift[extreme] - value) >= gate:
            reversals.append((float(time[extreme]), float(drift[extreme])))
            direction = -direction
            extreme = index
    # The record ends on the last leg; finish at its final (residual) value.
    reversals.append((float(time[-1]), float(drift[-1])))
    return reversals


def round_reversals(reversals: list[tuple[float, float]]) -> list[dict]:
    """Round targets to the step grid and drop points that stop being reversals."""
    points: list[dict] = []
    for time, measured in reversals:
        target = round(measured / DRIFT_STEP_RAD) * DRIFT_STEP_RAD
        if points and np.isclose(target, points[-1]["target"]):
            continue
        # After rounding, a middle point may continue the previous leg instead
        # of reversing it; merge it into that leg.
        if len(points) >= 2:
            previous_leg = points[-1]["target"] - points[-2]["target"]
            if previous_leg * (target - points[-1]["target"]) > 0:
                points[-1] = {"time": time, "measured": measured, "target": target}
                continue
        points.append({"time": time, "measured": measured, "target": target})
    return points


def build_steps(points: list[dict]) -> tuple[list[dict], list[tuple[float, int]]]:
    """Expand reversal targets into constant-size analysis steps."""
    steps: list[dict] = []
    groups: list[tuple[float, int]] = []
    step_number = AXIAL_LOAD_STEPS
    current = 0.0
    for leg, point in enumerate(points[1:], start=1):
        count = int(round(abs(point["target"] - current) / DRIFT_STEP_RAD))
        if count == 0:
            continue
        sign = 1.0 if point["target"] > current else -1.0
        groups.append((sign * LOAD_FACTOR_STEP, count))
        for _ in range(count):
            step_number += 1
            current += sign * DRIFT_STEP_RAD
            steps.append({
                "step": step_number,
                "leg": leg,
                "load_factor": round(current / DRIFT_PER_LOAD_FACTOR_RAD, 6),
                "story_drift_rad": round(current, 6),
            })
        point["end_step"] = step_number
    return steps, groups


def write_outputs(directory: Path, points: list[dict], steps: list[dict], groups: list[tuple[float, int]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "reversal_points.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["index", "time_s", "measured_drift_rad", "target_drift_rad", "target_load_factor", "end_step"])
        for index, point in enumerate(points):
            writer.writerow([
                index,
                f"{point['time']:.2f}",
                f"{point['measured']:.5f}",
                f"{point['target']:.4f}",
                f"{point['target'] / DRIFT_PER_LOAD_FACTOR_RAD:.1f}",
                point.get("end_step", AXIAL_LOAD_STEPS),
            ])
    with (directory / "load_steps.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["step", "leg", "load_factor", "story_drift_rad"])
        writer.writeheader()
        writer.writerows(steps)
    explicit = " ".join(f"{size:g}({count})" for size, count in groups)
    (directory / "diana_load_steps.txt").write_text(explicit + "\n", encoding="utf-8")


def plot_case(label: str, time: np.ndarray, drift: np.ndarray, points: list[dict], steps: list[dict], mode: str) -> list[Path]:
    apply_style(mode)
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    fig, ax = plt.subplots(figsize=figure_size(mode))
    ax.plot(time, drift, color=COLORS["primary"], label="Measured 4F story drift")
    ax.plot(
        [p["time"] for p in points],
        [p["target"] for p in points],
        "o",
        color=COLORS["accent"],
        label="Protocol reversal points",
    )
    ax.axhline(0.0, **reference_line_kwargs())
    format_axis(ax, xlabel="Time (s)", ylabel="Story drift (rad)", legend=True)
    ax.set_xlim(10.0, 30.0)
    outputs.extend(save_figure(fig, FIGURE_ROOT / f"{label}_measured_drift_and_reversals", formats=("png",), mode=mode))

    headers, standard = load_csv(STANDARD_PROTOCOL)
    fig, ax = plt.subplots(figsize=figure_size(mode))
    ax.plot(
        [s["step"] for s in steps],
        [s["story_drift_rad"] for s in steps],
        color=COLORS["primary"],
        label="Test-history protocol",
    )
    ax.plot(
        standard[:, headers.index("case_id")],
        standard[:, headers.index("story_drift_rad")],
        "--",
        color=COLORS["accent"],
        label="Standard protocol (origin)",
    )
    ax.axhline(0.0, **reference_line_kwargs())
    format_axis(ax, xlabel="Analysis step", ylabel="Story drift (rad)", legend=True)
    outputs.extend(save_figure(fig, FIGURE_ROOT / f"{label}_protocol_vs_standard", formats=("png",), mode=mode))
    plt.close("all")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--floor", type=int, default=4)
    # 0.005 rad drops sub-0.5 % wiggles but keeps every cycle that matters for
    # joint damage, including the decaying cycles after the largest excursion.
    parser.add_argument("--gate", type=float, default=0.005, help="minimum reversal range (rad)")
    args = parser.parse_args()
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]

    for year, case in CASES.items():
        headers, data = load_csv(ARCHIVE / year / "python" / case / "csv" / "story_drift_y.csv")
        time = data[:, headers.index("Time_s")]
        drift = data[:, headers.index(f"{args.floor}F_rad")]
        points = round_reversals(extract_reversals(time, drift, args.gate))
        steps, groups = build_steps(points)
        label = f"{year}_{case}_{args.floor}F"
        write_outputs(PROTOCOL_ROOT / label, points, steps, groups)
        plot_case(label, time, drift, points, steps, mode)
        print(f"{label}: {len(points) - 1} legs, {len(steps)} cyclic steps (steps {AXIAL_LOAD_STEPS + 1}-{steps[-1]['step']})")


if __name__ == "__main__":
    main()
