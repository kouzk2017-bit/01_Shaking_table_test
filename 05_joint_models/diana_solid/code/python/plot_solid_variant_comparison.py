"""Compare solid-model concrete variants against the layered-shell model.

Solid variants (same mesh, same node numbers, hinged beam ends):
- origin_2015: total strain crack model, multi-linear compression curve,
  Poisson's ratio reduction = damage based (reference)
- origin_2015_nu_no_reduction: same, Poisson's ratio reduction = none
- origin_2015_parabolic: origin_2015 with the multi-linear compression curve
  replaced by DIANA's parabolic curve (fracture-energy regularized)

A variant whose export is missing (e.g. an interim check of a run still in
progress) is drawn only in the figures it has data for.

One standard-size figure each: 01 story shear vs story drift (upper column),
02 joint deformation angle by step, 03 beam bar next to the right column face
(solid node 10403 / element 2954 <-> shell 1628), 04 joint stirrup x-leg
(solid 10108 / 2665 <-> shell 2375), 05 largest joint stirrup y-leg strain
(EYY, nodes 10122-10126; solid only).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from publication_style import apply_style, format_axis, figure_size, save_figure, COLORS, reference_line_kwargs  # noqa: E402

YIELD_STRAIN = 0.002
SOLID = WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed"
VARIANTS = (
    ("origin_2015", "Solid, multi-linear", COLORS["accent"]),
    ("origin_2015_nu_no_reduction", r"Solid, multi-linear, no $\nu$ red.", COLORS["green"]),
    ("origin_2015_parabolic", "Solid, parabolic", COLORS["purple"]),
)


def y_leg_max(frame: pd.DataFrame) -> pd.Series:
    return frame[[c for c in frame.columns if c.startswith("n")]].max(axis=1)


# stem, x label, y label, shell (csv, x column, y column, scale) or None,
# solid (csv, x column, y function)
FIGURES = (
    ("01_story_shear_vs_story_drift", "Story drift (rad)", "Story shear (kN)",
     ("story_shear_response.csv", "story_drift_rad", "story_shear_kN", 1.0),
     ("story_shear_response.csv", "story_drift_rad", lambda f: f["column_e1783_shear_kN"])),
    ("02_joint_deformation_angle_by_step", "Analysis step", "Joint deformation angle (rad)",
     ("joint_deformation_angle.csv", "load_step", "deformation_angle_rad", 1.0),
     ("joint_deformation_angle.csv", "load_step", lambda f: f["deformation_angle_rad"])),
    ("03_beam_bar_at_column_face_by_step", "Analysis step",
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$",
     ("beam_rebar_response.csv", "case_id", "beam_strain", 1 / YIELD_STRAIN),
     ("beam_bar_profile.csv", "case_id", lambda f: f["n10403_e2954"] / YIELD_STRAIN)),
    ("04_joint_stirrup_x_leg_by_step", "Analysis step",
     r"Joint stirrup strain (x-leg), $\epsilon/\epsilon_{\mathrm{y}}$",
     ("joint_stirrup_response.csv", "case_id", "joint_stirrup_exx", 1 / YIELD_STRAIN),
     ("joint_stirrup_profile.csv", "case_id", lambda f: f["n10108_e2665"] / YIELD_STRAIN)),
    ("05_joint_stirrup_y_leg_by_step", "Analysis step",
     r"Joint stirrup strain (y-leg, max), $\epsilon/\epsilon_{\mathrm{y}}$",
     None,
     ("joint_stirrup_y_profile.csv", "case_id", lambda f: y_leg_max(f) / YIELD_STRAIN)),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-dir", type=Path,
                        default=WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed" / "origin")
    parser.add_argument("--output-dir", type=Path,
                        default=WORKSPACE / "06_results" / "comparison" / "joint_shell_vs_solid_origin" / "solid_concrete_variants")
    args = parser.parse_args()

    apply_style("paper")
    for stem, x_label, y_label, shell_spec, solid_spec in FIGURES:
        fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
        if shell_spec is not None:
            filename, x_column, y_column, scale = shell_spec
            shell = pd.read_csv(args.shell_dir / filename)
            shell = shell[shell[x_column] > 10] if x_column == "load_step" else shell
            ax.plot(shell[x_column], shell[y_column] * scale, color=COLORS["primary"], label="Shell")
        filename, x_column, y_function = solid_spec
        for folder, label, color in VARIANTS:
            path = SOLID / folder / filename
            if not path.exists():
                continue
            frame = pd.read_csv(path)
            frame = frame[frame[x_column] > 10] if x_column == "load_step" else frame
            ax.plot(frame[x_column], y_function(frame), color=color, label=label)
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        if x_column == "story_drift_rad":
            ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
        format_axis(ax, xlabel=x_label, ylabel=y_label, legend=True, legend_location="best")
        save_figure(fig, args.output_dir / stem, formats=("png",), mode="paper")
        plt.close(fig)
    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
