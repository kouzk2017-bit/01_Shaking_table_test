"""Compare rebar strains of the DIANA layered-shell and solid joint models.

Same loading protocol and step count on both sides (steps 11-850 cyclic), so
strains are overlaid per analysis step. The shell's two element columns are
identical, so it is one curve per point. The solid side reads the along-bar
profiles written by diana_solid/code/python/prepare_rebar_response.py and
plots the columns listed in FIGURES.

One solid curve per figure, chosen by the user (2026-09-28): stirrup node
10108 / element 2665 (<-> shell 2375), beam bar node 10403 / element 2954
(next to the right column face 10402, <-> shell 1628), column bar node
11295 / element 3839 (next to the upper face 11296, <-> shell 1985). The
element right at a face carries a compressive spike, hence the adjacent node.

On hold (2026-10-01): the shell model is still being tuned, so shell vs solid is
not regenerated until it is final; each model is first checked against the test.
The 2026-09 figures are in 06_results/archive/2026-10-01_shell_vs_solid_preliminary/.
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

from publication_style import PROJECT_MODE, apply_style, format_axis, figure_size, save_figure, COLORS, reference_line_kwargs  # noqa: E402

YIELD_STRAIN = 0.002
SOLID_COLORS = (COLORS["accent"], COLORS["green"], COLORS["orange"], COLORS["purple"])

# stem, shell csv, shell column, shell label, solid csv, [(solid column, label)], y label
FIGURES = (
    ("02_joint_stirrup_strain_by_step", "joint_stirrup_response.csv", "joint_stirrup_exx", "Shell node 2375",
     "joint_stirrup_profile.csv",
     [("n10108_e2665", "Solid node 10108")],
     r"Joint stirrup strain, $\epsilon_{\mathrm{xx}}/\epsilon_{\mathrm{y}}$"),
    ("03_beam_longitudinal_strain_by_step", "beam_rebar_response.csv", "beam_strain", "Shell node 1628 (column face)",
     "beam_bar_profile.csv",
     [("n10403_e2954", "Solid node 10403 (column face)")],
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
    ("04_column_longitudinal_strain_by_step", "column_rebar_response.csv", "column_strain", "Shell node 1985",
     "column_bar_profile.csv",
     [("n11295_e3839", "Solid node 11295")],
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
                        default=WORKSPACE / "06_results" / "comparison" / "shell_vs_solid")
    args = parser.parse_args()

    apply_style(PROJECT_MODE)
    for stem, shell_file, shell_column, shell_label, solid_file, solid_columns, y_label in FIGURES:
        shell = pd.read_csv(args.shell_dir / shell_file)
        solid = pd.read_csv(args.solid_dir / solid_file)
        if not shell["case_id"].equals(solid["case_id"]):
            raise ValueError(f"Shell and solid case ids differ for {stem}")

        fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
        ax.plot(shell["case_id"], shell[shell_column] / YIELD_STRAIN,
                color=COLORS["primary"], label=shell_label)
        for (column, label), color in zip(solid_columns, SOLID_COLORS):
            ax.plot(solid["case_id"], solid[column] / YIELD_STRAIN, color=color, label=label)

        values = np.concatenate([shell[shell_column].to_numpy(),
                                 *(solid[c].to_numpy() for c, _ in solid_columns)]) / YIELD_STRAIN
        for ratio in (-1.0, 1.0):
            ax.axhline(ratio, **reference_line_kwargs(), linestyle="--", zorder=0)
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        ax.set_yticks(integer_strain_ticks(min(values.min(), -1.0), max(values.max(), 1.0)))
        format_axis(ax, xlabel="Analysis step", ylabel=y_label, legend=True, legend_location="best")
        save_figure(fig, args.output_dir / stem, formats=("png",), mode=PROJECT_MODE)
        plt.close(fig)

    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
