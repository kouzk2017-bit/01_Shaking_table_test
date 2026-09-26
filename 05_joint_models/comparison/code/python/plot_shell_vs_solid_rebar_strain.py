"""Compare rebar strains of the DIANA layered-shell and solid joint models.

Same loading protocol and step count on both sides (steps 11-850 cyclic), so
strains are overlaid per analysis step. The shell's two element columns are
identical, so it is one curve per point. The solid side reads the along-bar
profiles written by diana_solid/code/python/prepare_rebar_response.py and
plots the columns listed in FIGURES.

Solid point choice (confirmed by the user 2026-09-26): joint stirrup node
10108 corresponds to shell node 2375 (both adjacent bar elements drawn); beam
column faces at nodes 10397 / 10402, column faces at 11296 / 11302. The first
element outside a face carries a compressive spike, so the beam/column curves
use the next node into the member plus one point further in (whose strain
follows the section moment).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from publication_style import apply_style, format_axis, figure_size, save_figure, COLORS  # noqa: E402

YIELD_STRAIN = 0.002
SOLID_COLORS = (COLORS["accent"], COLORS["green"], COLORS["orange"], COLORS["purple"])

# stem, shell csv, shell column, shell label, solid csv, [(solid column, label)], y label
FIGURES = (
    ("02_joint_stirrup_strain_by_step", "joint_stirrup_response.csv", "joint_stirrup_exx", "Shell node 2375",
     "joint_stirrup_profile.csv",
     [("n10108_e2665", "Solid node 10108, elem 2665"), ("n10108_e2666", "Solid node 10108, elem 2666")],
     r"Joint stirrup strain, $\epsilon_{\mathrm{xx}}/\epsilon_{\mathrm{y}}$"),
    ("03_beam_longitudinal_strain_by_step", "beam_rebar_response.csv", "beam_strain", "Shell node 1628 (column face)",
     "beam_bar_profile.csv",
     [("n10403_e2954", "Solid node 10403 (next to right face)"), ("n10406_e2957", "Solid node 10406 (4 elem. into beam)")],
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
    ("04_column_longitudinal_strain_by_step", "column_rebar_response.csv", "column_strain", "Shell node 1985",
     "column_bar_profile.csv",
     [("n11295_e3839", "Solid node 11295 (next to joint)"), ("n11292_e3836", "Solid node 11292 (3 elem. into column)")],
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-dir", type=Path,
                        default=WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed" / "origin")
    parser.add_argument("--solid-dir", type=Path,
                        default=WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed" / "origin_2015")
    parser.add_argument("--output-dir", type=Path,
                        default=WORKSPACE / "06_results" / "comparison" / "joint_shell_vs_solid_origin")
    args = parser.parse_args()

    apply_style("paper")
    for stem, shell_file, shell_column, shell_label, solid_file, solid_columns, y_label in FIGURES:
        shell = pd.read_csv(args.shell_dir / shell_file)
        solid = pd.read_csv(args.solid_dir / solid_file)
        if not shell["case_id"].equals(solid["case_id"]):
            raise ValueError(f"Shell and solid case ids differ for {stem}")

        fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
        ax.plot(shell["case_id"], shell[shell_column] / YIELD_STRAIN,
                color=COLORS["primary"], linewidth=1.25, label=shell_label)
        for (column, label), color in zip(solid_columns, SOLID_COLORS):
            ax.plot(solid["case_id"], solid[column] / YIELD_STRAIN, color=color, linewidth=1.0, label=label)

        values = np.concatenate([shell[shell_column].to_numpy(),
                                 *(solid[c].to_numpy() for c, _ in solid_columns)]) / YIELD_STRAIN
        for ratio in (-1.0, 1.0):
            ax.axhline(ratio, color=COLORS["zero"], linewidth=0.8, linestyle="--", zorder=0)
        ax.axhline(0.0, color=COLORS["zero"], linewidth=0.8, zorder=0)
        ax.set_yticks(integer_strain_ticks(min(values.min(), -1.0), max(values.max(), 1.0)))
        format_axis(ax, xlabel="Analysis step", ylabel=y_label, legend=True, legend_location="best")
        save_figure(fig, args.output_dir / stem, formats=("png",), mode="paper")
        plt.close(fig)

    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
