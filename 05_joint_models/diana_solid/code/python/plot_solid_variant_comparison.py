"""Compare the solid model's concrete variants with each other (no shell, no test).

Solid variants (same mesh, same node numbers, hinged beam ends):
- origin_2015: total strain crack model, multi-linear compression curve,
  Poisson's ratio reduction = damage based (reference)
- origin_2015_nu_no_reduction: same, Poisson's ratio reduction = none
- origin_2015_parabolic: origin_2015 with the multi-linear compression curve
  replaced by DIANA's parabolic curve (fracture-energy regularized)
- origin_2015_parabolic_fine: parabolic with smaller load steps from about
  +0.0125 rad, so its step numbers differ from the others after that point;
  only shear and joint angle exported, so it appears in 01 and 02 only

A variant whose export is missing is drawn only in the figures it has data for.
Figures 01 and 02 are against story drift, so all variants are comparable even
with different step sizes; 03-05 are by step and exclude the fine-step run.

One standard-size figure each: 01 story shear vs story drift (upper column),
02 joint deformation angle vs story drift, 03 beam bar next to the right column
face (node 10403 / element 2954), 04 joint stirrup x-leg (10108 / 2665),
05 largest joint stirrup y-leg strain (EYY, nodes 10122-10126).
Output: 06_results/diana/solid/concrete_variants/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from publication_style import PROJECT_MODE, apply_style, format_axis, figure_size, save_figure, COLORS, reference_line_kwargs  # noqa: E402

YIELD_STRAIN = 0.002
SOLID = WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed"
VARIANTS = (
    ("origin_2015", "Solid, multi-linear", COLORS["accent"]),
    ("origin_2015_nu_no_reduction", r"Solid, multi-linear, no $\nu$ red.", COLORS["green"]),
    ("origin_2015_parabolic", "Solid, parabolic", COLORS["purple"]),
    ("origin_2015_parabolic_fine", "Solid, parabolic, fine steps", COLORS["orange"]),
)
BY_DRIFT_ONLY = {"origin_2015_parabolic_fine"}


def y_leg_max(frame: pd.DataFrame) -> pd.Series:
    return frame[[c for c in frame.columns if c.startswith("n")]].max(axis=1)


def joint_angle_with_drift(folder: Path) -> pd.DataFrame:
    joint = pd.read_csv(folder / "joint_deformation_angle.csv")
    shear = pd.read_csv(folder / "story_shear_response.csv")
    return joint.merge(shear[["case_id", "story_drift_rad"]], left_on="load_step", right_on="case_id")


# stem, x label, y label, (csv or reader, x column, y function)
FIGURES = (
    ("01_story_shear_vs_story_drift", "Story drift (rad)", "Story shear (kN)",
     ("story_shear_response.csv", "story_drift_rad", lambda f: f["column_e1783_shear_kN"])),
    ("02_joint_deformation_vs_story_drift", "Story drift (rad)", "Joint deformation angle (rad)",
     (joint_angle_with_drift, "story_drift_rad", lambda f: f["deformation_angle_rad"])),
    ("03_beam_bar_at_column_face_by_step", "Analysis step",
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$",
     ("beam_bar_profile.csv", "case_id", lambda f: f["n10403_e2954"] / YIELD_STRAIN)),
    ("04_joint_stirrup_x_leg_by_step", "Analysis step",
     r"Joint stirrup strain (x-leg), $\epsilon/\epsilon_{\mathrm{y}}$",
     ("joint_stirrup_profile.csv", "case_id", lambda f: f["n10108_e2665"] / YIELD_STRAIN)),
    ("05_joint_stirrup_y_leg_by_step", "Analysis step",
     r"Joint stirrup strain (y-leg, max), $\epsilon/\epsilon_{\mathrm{y}}$",
     ("joint_stirrup_y_profile.csv", "case_id", lambda f: y_leg_max(f) / YIELD_STRAIN)),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=WORKSPACE / "06_results" / "diana" / "solid" / "concrete_variants")
    args = parser.parse_args()

    apply_style(PROJECT_MODE)
    for stem, x_label, y_label, (source, x_column, y_function) in FIGURES:
        fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
        for folder, label, color in VARIANTS:
            if x_column != "story_drift_rad" and folder in BY_DRIFT_ONLY:
                continue
            if callable(source):
                if not (SOLID / folder / "joint_deformation_angle.csv").exists():
                    continue
                frame = source(SOLID / folder)
            else:
                if not (SOLID / folder / source).exists():
                    continue
                frame = pd.read_csv(SOLID / folder / source)
            ax.plot(frame[x_column], y_function(frame), color=color, label=label)
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        if x_column == "story_drift_rad":
            ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
        format_axis(ax, xlabel=x_label, ylabel=y_label, legend=True, legend_location="best")
        save_figure(fig, args.output_dir / stem, formats=("png",), mode=PROJECT_MODE)
        plt.close(fig)
    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
