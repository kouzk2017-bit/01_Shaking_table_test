"""Compare the DIANA layered-shell and solid joint models' deformation angle.

Both models run the same displacement-controlled loading protocol (steps
1-10 axial force, 11-850 cyclic displacement control) on the same physical
joint panel (a=300 mm, b=366.67 mm), just with different meshes and node
numbering -- shell uses nodes 623/620/639/636, solid uses 3149/3152/3165/3168
(see 05_joint_models/diana_solid/data/raw/README.md). Same load-step count on
both sides makes a direct step-for-step comparison meaningful; steps 1-10
(axial-only) are excluded, matching plot_joint_deformation_angle.py.
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


def load_deformation_angle(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame["load_step"] > 10]
    return frame[["load_step", "deformation_angle_rad"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shell-csv", type=Path,
        default=WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed" / "origin" / "joint_deformation_angle.csv",
    )
    parser.add_argument(
        "--solid-csv", type=Path,
        default=WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed" / "origin_2015" / "joint_deformation_angle.csv",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=WORKSPACE / "06_results" / "comparison" / "joint_shell_vs_solid_origin",
    )
    args = parser.parse_args()

    apply_style("paper")
    shell = load_deformation_angle(args.shell_csv)
    solid = load_deformation_angle(args.solid_csv)
    if not shell["load_step"].equals(solid["load_step"]):
        raise ValueError("Shell and solid load-step sequences do not match; check both raw exports.")

    fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
    ax.plot(shell["load_step"], shell["deformation_angle_rad"],
            color=COLORS["primary"], label="Shell (origin)")
    ax.plot(solid["load_step"], solid["deformation_angle_rad"],
            color=COLORS["accent"], label="Solid (origin_2015, hinged beam ends)")
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel="Analysis step", ylabel="Deformation angle (rad)", legend=True)
    save_figure(fig, args.output_dir / "01_joint_deformation_angle_by_step", formats=("png",), mode="paper")

    print(f"Wrote figure to {args.output_dir}")


if __name__ == "__main__":
    main()
