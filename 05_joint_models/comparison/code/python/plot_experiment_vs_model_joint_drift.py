"""Compare the shaking-table joint response against a DIANA joint model.

``--model shell`` (processed ``diana_shell/data/processed/<condition>``) or
``--model solid`` (``diana_solid/data/processed/<condition>``); output goes to
``06_results/comparison/test_vs_<model>/2015_4F_<protocol>_protocol/<condition>/`` by default
(one subfolder per case, shell and solid alike (``--protocol standard|history``
names the loading protocol the condition was run with).

The experiment records a dynamic time-history; the DIANA model is driven by
a quasi-static, displacement-controlled loading-step sequence. The two are
not comparable point-for-point against time or step number, so both sides
are converted to a response-vs-response curve instead: joint deformation
angle plotted against story drift. Both axes are response quantities, so
the curve exists regardless of whether the underlying process was driven by
time or by loading step, and the two curves can be overlaid directly.

Figure 03 compares story shear vs story drift after dividing each by its own
peak: the test reports the whole 4F story shear, the model one joint, so only
the shape (stiffness change, peak drift, softening) is comparable.

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
PROCESSED = {
    "shell": WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed",
    "solid": WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed",
}
DEFAULT_CONDITION = {"shell": "origin", "solid": "origin_2015"}
SOLID_SHEAR_COLUMN = "column_e1783_shear_kN"  # upper column, same line as the shell's node 524


def read_model(model: str, condition: str) -> dict[str, np.ndarray]:
    """Joint angle, story drift and story shear of one DIANA condition, by load step."""
    folder = PROCESSED[model] / condition
    if model == "shell":
        data = read_condition(PROCESSED[model], condition)
        shear_file, shear_column = "cyclic_response.csv", "story_shear_kN"
    else:
        joint_headers, joint_data = load_csv(folder / "joint_deformation_angle.csv")
        steps = _column(joint_headers, joint_data, "load_step").astype(int)
        angle = _column(joint_headers, joint_data, "deformation_angle_rad")
        data = {"load_step": steps[steps > 10], "deformation_angle_rad": angle[steps > 10]}
        shear_file, shear_column = "story_shear_response.csv", SOLID_SHEAR_COLUMN
    headers, values = load_csv(folder / shear_file)
    by_step = dict(zip(_column(headers, values, "case_id").astype(int),
                       zip(_column(headers, values, "story_drift_rad"), _column(headers, values, shear_column))))
    common = np.isin(data["load_step"], list(by_step))  # exports taken mid-run can end at different steps
    data = {key: values[common] for key, values in data.items()}
    data["story_drift_rad"] = np.asarray([by_step[step][0] for step in data["load_step"]])
    data["story_shear_kN"] = np.asarray([by_step[step][1] for step in data["load_step"]])
    return data


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
        "story_shear_kN": story_shear_floor(csv_dir, floor, drift_time[:length]),
    }


def story_shear_floor(csv_dir: Path, floor: int, time: np.ndarray) -> np.ndarray:
    """Story shear (Y direction) of one floor on the drift time axis."""
    headers, data = load_csv(csv_dir / "story_shear_y.csv")
    shear_time = _column(headers, data, "Time_s")
    return np.interp(time, shear_time, _column(headers, data, f"{floor}F_kN"))


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
    parser.add_argument("--model", choices=("shell", "solid"), default="shell")
    parser.add_argument("--diana-condition", help="processed folder name (default: origin / origin_2015)")
    parser.add_argument("--diana-label", help="legend label for the model")
    parser.add_argument("--protocol", choices=("standard", "history"), default="standard",
                        help="loading protocol of the DIANA run (only names the output folder)")
    parser.add_argument("--output-dir", type=Path,
                        help="default: 06_results/comparison/test_vs_<model>/2015_4F_<protocol>_protocol/<condition>")
    args = parser.parse_args()
    condition = args.diana_condition or DEFAULT_CONDITION[args.model]
    args.diana_label = args.diana_label or f"DIANA {args.model}, {condition} (quasi-static)"
    if args.output_dir is None:
        args.output_dir = WORKSPACE / "06_results" / "comparison" / f"test_vs_{args.model}" / f"2015_4F_{args.protocol}_protocol"
        args.output_dir /= condition

    apply_style("paper")
    experiment = load_experiment_floor(args.experiment_csv_dir, args.experiment_floor)
    model = read_model(args.model, condition)

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

    # Figure 3: story shear normalised by its own peak (test = whole story, model = one joint).
    fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
    ax.plot(experiment["story_drift_rad"], experiment["story_shear_kN"] / np.max(np.abs(experiment["story_shear_kN"])),
            color=COLORS["primary"], linewidth=line_width(0.5), label=args.experiment_label)
    ax.plot(model["story_drift_rad"], model["story_shear_kN"] / np.max(np.abs(model["story_shear_kN"])),
            color=COLORS["accent"], label=args.diana_label)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(-AXIS_LIMIT_RAD, AXIS_LIMIT_RAD)
    format_axis(ax, xlabel="Story drift (rad)", ylabel=r"Story shear / peak $V/V_{max}$", legend=True)
    save_figure(fig, args.output_dir / "03_normalized_shear_vs_story_drift", formats=("png",), mode="paper")
    print(f"Peak story shear: test {np.max(np.abs(experiment['story_shear_kN'])):.0f} kN, "
          f"model {np.max(np.abs(model['story_shear_kN'])):.0f} kN")

    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
