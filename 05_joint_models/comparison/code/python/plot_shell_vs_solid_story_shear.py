"""Compare story shear of the DIANA layered-shell and solid joint models.

Shell: composed-line NX at node 524 (processed story_shear_response.csv).
Solid: composed-line NX of the two column lines next to the plates (elements
1764 and 1783). Both beam ends are also restrained in X, so part of the
horizontal force goes into the beams axially and the two column shears are
not identical; both are drawn.

Figure 07: story shear by analysis step. Figure 08: story shear vs story
drift (load factor x 0.005 rad).
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

SOLID_COLUMNS = (("column_e1764_shear_kN", "Solid column line 1764", COLORS["accent"]),
                 ("column_e1783_shear_kN", "Solid column line 1783", COLORS["green"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-csv", type=Path,
                        default=WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed" / "origin" / "story_shear_response.csv")
    parser.add_argument("--solid-csv", type=Path,
                        default=WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed" / "origin_2015" / "story_shear_response.csv")
    parser.add_argument("--output-dir", type=Path,
                        default=WORKSPACE / "06_results" / "comparison" / "joint_shell_vs_solid_origin")
    args = parser.parse_args()

    apply_style("paper")
    shell = pd.read_csv(args.shell_csv)
    solid = pd.read_csv(args.solid_csv)
    if not shell["case_id"].equals(solid["case_id"]):
        raise ValueError("Shell and solid case ids differ")

    for stem, x_column, x_label in (("07_story_shear_by_step", "case_id", "Analysis step"),
                                    ("08_story_shear_vs_story_drift", "story_drift_rad", "Story drift (rad)")):
        fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
        ax.plot(shell[x_column], shell["story_shear_kN"], color=COLORS["primary"], label="Shell")
        for column, label, color in SOLID_COLUMNS:
            ax.plot(solid[x_column], solid[column], color=color, label=label)
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        if x_column == "story_drift_rad":
            ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
        format_axis(ax, xlabel=x_label, ylabel="Story shear (kN)", legend=True, legend_location="best")
        save_figure(fig, args.output_dir / stem, formats=("png",), mode="paper")
        plt.close(fig)
    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
