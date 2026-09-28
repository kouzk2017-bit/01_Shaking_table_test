"""Compare the shaking-table joint response against a DIANA joint model.

The experiment records a dynamic time-history; the DIANA model is driven by
a quasi-static, displacement-controlled loading-step sequence. The two are
not comparable point-for-point against time or step number, so both sides
are converted to a response-vs-response curve instead: joint deformation
angle plotted against story drift. Both axes are response quantities, so
the curve exists regardless of whether the underlying process was driven by
time or by loading step, and the two curves can be overlaid directly.

Figure 1 overlays the full trajectories. Figure 2 overlays only the cycle
reversal points (every local max/min of story drift) as a simplified
envelope/backbone comparison, since the full experimental trajectory is
noisy and a raw earthquake record does not reduce to a clean hysteresis
loop the way the controlled DIANA protocol does.

Known physical differences to read the comparison against (not corrected
for here): strain-rate effects (dynamic loading is faster, typically
stiffer/stronger than quasi-static), inertial and damping forces present
in the experiment but absent from the static model, and different cycle
counts/amplitude sequences (irregular earthquake motion vs a programmed
cyclic protocol).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
sys.path.insert(0, str(WORKSPACE / "05_joint_models" / "diana_shell" / "code" / "python"))

from ten_story_pipeline import load_csv  # noqa: E402
from publication_style import apply_style, format_axis, figure_size, save_figure, COLORS, reference_line_kwargs, line_width  # noqa: E402
from plot_csv_results import _column, select_peaks  # noqa: E402
from plot_joint_deformation_angle import read_condition  # noqa: E402

AXIS_LIMIT_RAD = 0.045


def load_experiment_floor(csv_dir: Path, floor: int) -> dict[str, np.ndarray]:
    """Join joint rotation and story drift (Y direction) for one floor by time."""
    drift_headers, drift_data = load_csv(csv_dir / "story_drift_y.csv")
    joint_headers, joint_data = load_csv(csv_dir / "joint_rotation.csv")
    drift_time = _column(drift_headers, drift_data, "Time_s")
    joint_time = _column(joint_headers, joint_data, "Time_s")
    length = min(drift_time.size, joint_time.size)
    if not np.allclose(drift_time[:length], joint_time[:length], rtol=0.0, atol=1e-9):
        raise ValueError("story_drift_y.csv and joint_rotation.csv time columns do not align")
    return {
        "time_s": drift_time[:length],
        "story_drift_rad": _column(drift_headers, drift_data, f"{floor}F_rad")[:length],
        "deformation_angle_rad": _column(joint_headers, joint_data, f"{floor}F_rad")[:length],
    }


def cycle_reversal_indices(x: np.ndarray) -> np.ndarray:
    """Every local max/min of x -- the natural backbone vertices of a cyclic signal."""
    is_max = (x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:])
    is_min = (x[1:-1] < x[:-2]) & (x[1:-1] <= x[2:])
    indices = np.flatnonzero(is_max | is_min) + 1
    return np.concatenate(([0], indices, [x.size - 1]))


def style_hysteresis_axis(ax) -> None:
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(-AXIS_LIMIT_RAD, AXIS_LIMIT_RAD)
    ax.set_ylim(-AXIS_LIMIT_RAD, AXIS_LIMIT_RAD)
    format_axis(ax, xlabel="Story drift (rad)", ylabel="Joint deformation angle (rad)", legend=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment-csv-dir", type=Path,
        default=WORKSPACE / "06_results" / "experiment" / "2015" / "20151211-2(JMAKobe100%)" / "csv",
    )
    parser.add_argument("--experiment-floor", type=int, default=4)
    parser.add_argument("--experiment-label", default="2015 shaking table -- 4F (dynamic)")
    parser.add_argument(
        "--diana-processed-dir", type=Path,
        default=WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed",
    )
    parser.add_argument("--diana-condition", default="origin")
    parser.add_argument("--diana-label", default="DIANA origin (quasi-static)")
    parser.add_argument(
        "--output-dir", type=Path,
        default=WORKSPACE / "06_results" / "comparison" / "joint_4F_2015_vs_diana_origin",
    )
    args = parser.parse_args()

    apply_style("paper")
    experiment = load_experiment_floor(args.experiment_csv_dir, args.experiment_floor)
    model = read_condition(args.diana_processed_dir, args.diana_condition)

    selected, _selection = select_peaks(
        experiment["time_s"], experiment["story_drift_rad"],
        mode="min", count=4, time_window=(10.0, 30.0),
        significance_fraction=0.30, minimum_separation_s=0.50,
    )

    # Figure 1: full response-vs-response trajectories overlaid.
    fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
    ax.plot(experiment["story_drift_rad"], experiment["deformation_angle_rad"],
            color=COLORS["primary"], linewidth=line_width(0.5), label=args.experiment_label)
    ax.plot(model["story_drift_rad"], model["deformation_angle_rad"],
            color=COLORS["accent"], label=args.diana_label)
    ax.scatter(experiment["story_drift_rad"][selected], experiment["deformation_angle_rad"][selected],
               color=COLORS["primary"], zorder=5)
    for label, index in zip("ABCD", selected):
        ax.annotate(
            label,
            (experiment["story_drift_rad"][index], experiment["deformation_angle_rad"][index]),
            textcoords="offset points", xytext=(4, 4), color=COLORS["primary"],
        )
    style_hysteresis_axis(ax)
    save_figure(fig, args.output_dir / "01_joint_deformation_vs_story_drift", formats=("png",), mode="paper")

    # Figure 2: cycle-reversal envelope only, for a cleaner backbone comparison.
    experiment_envelope = cycle_reversal_indices(experiment["story_drift_rad"])
    model_envelope = cycle_reversal_indices(model["story_drift_rad"])
    fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
    ax.plot(experiment["story_drift_rad"][experiment_envelope], experiment["deformation_angle_rad"][experiment_envelope],
            color=COLORS["primary"], marker="o", label=f"{args.experiment_label} envelope")
    ax.plot(model["story_drift_rad"][model_envelope], model["deformation_angle_rad"][model_envelope],
            color=COLORS["accent"], marker="o", label=f"{args.diana_label} envelope")
    style_hysteresis_axis(ax)
    save_figure(fig, args.output_dir / "02_joint_deformation_vs_story_drift_envelope", formats=("png",), mode="paper")

    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
