"""Result package of the DIANA solid joint model, one analysis case at a time.

Reads only the solid model's own processed data
(``diana_solid/data/processed/<case>/``, written by prepare_rebar_response.py
and calculate_joint_deformation_angle.py) and writes one standard-size figure
per response to ``06_results/diana/solid/<case>/``. No shell or test curves:
comparisons live in ``06_results/comparison/``.

Figures (a figure is skipped when its processed file is missing, e.g. an
interim export):
  01  story shear vs story drift        (upper-column composed line, e1783)
  02  story shear by analysis step
  03  joint deformation angle by step   (diagonal length change, as the test)
  04  joint deformation angle vs story drift
  05  joint stirrup x-leg               (node 10108 / element 2665)
  06  joint stirrup y-leg, largest of nodes 10122-10126 (EYY)
  07  beam bar next to the right column face   (node 10403 / element 2954)
  08  column bar next to the upper beam face   (node 11295 / element 3839)
  09  beam bar strain along the bar (nodes 10380-10419), first peak of each amplitude
  10  column bar strain along the bar (nodes 11285-11312), same peaks
The element right at a face carries a compressive spike, hence the adjacent
node in 07/08 (chosen by the user 2026-09-28). In 09/10 each bar element is
drawn as its own segment, so a jump at a shared node is the inter-element
discontinuity, not noise; the x-axis is node sequence, not distance.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from publication_style import apply_style, format_axis, figure_size, save_figure, COLORS, reference_line_kwargs  # noqa: E402

PROCESSED = WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed"
RESULTS = WORKSPACE / "06_results" / "diana" / "solid"
YIELD_STRAIN = 0.002
AXIAL_LOAD_STEPS = 10
SHEAR_COLUMN = "column_e1783_shear_kN"
COLUMN_PATTERN = re.compile(r"^n(\d+)_e(\d+)$")
PALETTE = [COLORS["sky"], COLORS["primary"], COLORS["orange"], COLORS["accent"],
           COLORS["green"], "#006D4F", COLORS["purple"], COLORS["black"]]  # +/- drift pairs: light/dark of one hue

# stem, processed csv, column (or None = max over n* columns), y label
STRAIN_BY_STEP = (
    ("05_joint_stirrup_x_leg_by_step", "joint_stirrup_profile.csv", "n10108_e2665",
     r"Joint stirrup strain (x-leg), $\epsilon/\epsilon_{\mathrm{y}}$"),
    ("06_joint_stirrup_y_leg_by_step", "joint_stirrup_y_profile.csv", None,
     r"Joint stirrup strain (y-leg, max), $\epsilon/\epsilon_{\mathrm{y}}$"),
    ("07_beam_bar_at_column_face_by_step", "beam_bar_profile.csv", "n10403_e2954",
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
    ("08_column_bar_at_beam_face_by_step", "column_bar_profile.csv", "n11295_e3839",
     r"Column longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
)

# stem, processed csv, face nodes, y label
PROFILES = (
    ("09_beam_bar_strain_profile", "beam_bar_profile.csv", (10397, 10402),
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
    ("10_column_bar_strain_profile", "column_bar_profile.csv", (11296, 11302),
     r"Column longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
)


def integer_strain_ticks(lower: float, upper: float, max_ticks: int = 14) -> np.ndarray:
    span = np.ceil(upper) - np.floor(lower)
    step = 1
    for candidate in (1, 2, 5, 10, 20, 25, 50, 100):
        step = candidate
        if span / step <= max_ticks:
            break
    return np.arange(np.floor(lower / step) * step, np.ceil(upper / step) * step + step, step)


def first_peak_steps(frame: pd.DataFrame) -> list[tuple[str, int]]:
    steps = []
    for amplitude in (2, 4, 6, 8):
        for sign in (1, -1):
            reached = frame.loc[sign * frame["load_factor"] >= amplitude - 1e-6, "case_id"]
            if len(reached):
                steps.append((f"{sign * amplitude * 0.005:+.3f} rad", int(reached.iloc[0])))
    return steps


def new_axes():
    return plt.subplots(figsize=figure_size(mode="paper"))


def finish(fig, ax, output: Path, stem: str, x_label: str, y_label: str, legend: bool = False) -> None:
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    if "drift" in x_label.lower():
        ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel=x_label, ylabel=y_label, legend=legend, legend_location="best")
    save_figure(fig, output / stem, formats=("png",), mode="paper")
    plt.close(fig)


def plot_shear_and_joint(folder: Path, output: Path) -> None:
    shear = pd.read_csv(folder / "story_shear_response.csv")
    fig, ax = new_axes()
    ax.plot(shear["story_drift_rad"], shear[SHEAR_COLUMN], color=COLORS["accent"])
    finish(fig, ax, output, "01_story_shear_vs_story_drift", "Story drift (rad)", "Story shear (kN)")
    fig, ax = new_axes()
    ax.plot(shear["case_id"], shear[SHEAR_COLUMN], color=COLORS["accent"])
    finish(fig, ax, output, "02_story_shear_by_step", "Analysis step", "Story shear (kN)")

    joint = pd.read_csv(folder / "joint_deformation_angle.csv")
    joint = joint[joint["load_step"] > AXIAL_LOAD_STEPS]
    fig, ax = new_axes()
    ax.plot(joint["load_step"], joint["deformation_angle_rad"], color=COLORS["accent"])
    finish(fig, ax, output, "03_joint_deformation_angle_by_step", "Analysis step", "Joint deformation angle (rad)")
    merged = joint.merge(shear[["case_id", "story_drift_rad"]], left_on="load_step", right_on="case_id")
    fig, ax = new_axes()
    ax.plot(merged["story_drift_rad"], merged["deformation_angle_rad"], color=COLORS["accent"])
    finish(fig, ax, output, "04_joint_deformation_vs_story_drift", "Story drift (rad)", "Joint deformation angle (rad)")


def plot_strain_by_step(folder: Path, output: Path) -> None:
    for stem, filename, column, y_label in STRAIN_BY_STEP:
        if not (folder / filename).exists():
            continue
        frame = pd.read_csv(folder / filename)
        if column is None:
            values = frame[[c for c in frame.columns if c.startswith("n")]].max(axis=1) / YIELD_STRAIN
        else:
            values = frame[column] / YIELD_STRAIN
        fig, ax = new_axes()
        ax.plot(frame["case_id"], values, color=COLORS["accent"])
        for ratio in (-1.0, 1.0):
            ax.axhline(ratio, **reference_line_kwargs(), linestyle="--", zorder=0)
        ax.set_yticks(integer_strain_ticks(min(values.min(), -1.0), max(values.max(), 1.0)))
        finish(fig, ax, output, stem, "Analysis step", y_label)


def plot_profiles(folder: Path, output: Path) -> None:
    for stem, filename, faces, y_label in PROFILES:
        if not (folder / filename).exists():
            continue
        frame = pd.read_csv(folder / filename).set_index("case_id", drop=False)
        elements: dict[int, list[tuple[int, str]]] = {}
        for column in frame.columns:
            match = COLUMN_PATTERN.match(column)
            if match:
                elements.setdefault(int(match.group(2)), []).append((int(match.group(1)), column))
        first_node = min(node for ends in elements.values() for node, _ in ends)
        last_node = max(node for ends in elements.values() for node, _ in ends)

        fig, ax = new_axes()
        for (label, step), color in zip(first_peak_steps(frame), PALETTE):
            linestyle = "-" if label.startswith("+") else "--"
            for index, (_, ends) in enumerate(sorted(elements.items())):
                ax.plot([node - first_node for node, _ in ends], [frame.loc[step, c] / YIELD_STRAIN for _, c in ends],
                        color=color, linestyle=linestyle, marker="o",
                        label=f"{label} (step {step})" if index == 0 else None)
        for face in faces:
            ax.axvline(face - first_node, **reference_line_kwargs(), linestyle=":")
        for ratio in (-1.0, 1.0):
            ax.axhline(ratio, **reference_line_kwargs(), linestyle="--", zorder=0)
        ticks = range(0, last_node - first_node + 1, 3)
        ax.set_xticks(ticks, [str(first_node + i) for i in ticks], rotation=45)
        finish(fig, ax, output, stem,
               f"Node along bar (sequence, not distance; dotted = faces {faces[0]} / {faces[1]})", y_label, legend=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", default="origin_2015", help="folder name under diana_solid/data/processed/")
    parser.add_argument("--output-dir", type=Path, help="default: 06_results/diana/solid/<case>/")
    args = parser.parse_args()

    folder = PROCESSED / args.case
    output = args.output_dir or RESULTS / args.case
    apply_style("paper")
    plot_shear_and_joint(folder, output)
    plot_strain_by_step(folder, output)
    plot_profiles(folder, output)
    print(f"Wrote figures to {output}")


if __name__ == "__main__":
    main()
