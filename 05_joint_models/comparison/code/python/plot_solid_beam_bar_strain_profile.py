"""Strain distribution along the solid model's full beam and column bars.

Reads the along-bar profiles written by
diana_solid/code/python/prepare_rebar_response.py (origin_2015, hinged beam
ends). Each bar element reports a value at both of its end nodes, so each
element is drawn as its own segment: a jump at a shared node is the
inter-element strain discontinuity, not noise.

Node coordinates are not in the export, so the x-axis is node sequence, not
physical distance. Dotted lines mark the column/beam faces (confirmed by the
user 2026-09-26).

Figure 05: beam bar (nodes 10380-10419). Figure 06: column bar (11285-11312).
Both at the first peak of each drift amplitude.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from publication_style import apply_style, format_axis, figure_size, save_figure, COLORS, reference_line_kwargs  # noqa: E402

YIELD_STRAIN = 0.002
COLUMN_PATTERN = re.compile(r"^n(\d+)_e(\d+)$")
PALETTE = [COLORS["sky"], COLORS["primary"], COLORS["orange"], COLORS["accent"],
           COLORS["green"], COLORS["sky"], COLORS["purple"], COLORS["black"]]

# stem, processed csv, face nodes, y label
FIGURES = (
    ("05_solid_beam_bar_strain_profile", "beam_bar_profile.csv", (10397, 10402),
     r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
    ("06_solid_column_bar_strain_profile", "column_bar_profile.csv", (11296, 11302),
     r"Column longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$"),
)


def first_peak_steps(frame: pd.DataFrame) -> list[tuple[str, int]]:
    steps = []
    for amplitude in (2, 4, 6, 8):
        for sign in (1, -1):
            reached = frame.loc[sign * frame["load_factor"] >= amplitude - 1e-6, "case_id"]
            if len(reached):
                steps.append((f"{sign * amplitude * 0.005:+.3f} rad", int(reached.iloc[0])))
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solid-dir", type=Path,
                        default=WORKSPACE / "05_joint_models" / "diana_solid" / "data" / "processed" / "origin_2015")
    parser.add_argument("--output-dir", type=Path,
                        default=WORKSPACE / "06_results" / "comparison" / "joint_shell_vs_solid_origin")
    args = parser.parse_args()

    apply_style("paper")
    for stem, filename, faces, y_label in FIGURES:
        frame = pd.read_csv(args.solid_dir / filename).set_index("case_id", drop=False)
        elements: dict[int, list[tuple[int, str]]] = {}
        for column in frame.columns:
            match = COLUMN_PATTERN.match(column)
            if match:
                elements.setdefault(int(match.group(2)), []).append((int(match.group(1)), column))
        first_node = min(node for ends in elements.values() for node, _ in ends)
        last_node = max(node for ends in elements.values() for node, _ in ends)

        fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
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
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        ticks = range(0, last_node - first_node + 1, 3)
        ax.set_xticks(ticks, [str(first_node + i) for i in ticks], rotation=45)
        format_axis(ax, xlabel=f"Node along bar (sequence, not distance; dotted = faces {faces[0]} / {faces[1]})",
                    ylabel=y_label, legend=True, legend_location="best")
        save_figure(fig, args.output_dir / stem, formats=("png",), mode="paper")
        plt.close(fig)
    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
