"""Draw original-versus-changed-column-rebar DIANA cyclic comparison figures."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / "common" / "python"))

from publication_style import (  # noqa: E402
    COLORS,
    add_panel_label,
    apply_style,
    figure_size,
    format_axis,
    save_figure,
)


CONDITIONS = ()
OUTPUTS = (
    ("01_story_shear_vs_story_drift", "story_drift_rad", "story_shear_kN", "Story drift (rad)", "Story shear (kN)", "(a)"),
    ("02_beam_longitudinal_strain_vs_case_id", "case_id", "beam_strain_over_0p002", "Analysis step", r"Beam longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$", "(b)"),
    ("03_column_longitudinal_strain_vs_case_id", "case_id", "column_strain_over_0p002", "Analysis step", r"Column longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$", "(c)"),
)


def read_table(path: Path) -> dict[str, np.ndarray]:
    """Load one standardized response table as numeric arrays."""
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return {
        header: np.asarray([float(row[header]) for row in rows])
        for header in rows[0]
    }


def draw_comparison(
    output_directory: Path,
    stem: str,
    x_column: str,
    y_column: str,
    x_label: str,
    y_label: str,
    panel_label: str,
) -> tuple[Path, ...]:
    """Draw one consistently formatted two-condition comparison figure."""
    style = apply_style("paper")
    fig, ax = plt.subplots(figsize=figure_size("paper"))
    for condition, label, color, line_style in CONDITIONS:
        source = WORKSPACE / "diana" / "data" / "processed" / condition / "cyclic_response.csv"
        table = read_table(source)
        ax.plot(
            table[x_column],
            table[y_column],
            color=color,
            linestyle=line_style,
            label=label,
        )
    if x_column == "story_drift_rad":
        ax.axhline(0.0, color=COLORS["zero"], linewidth=style.reference_line_width, zorder=0)
        ax.axvline(0.0, color=COLORS["zero"], linewidth=style.reference_line_width, zorder=0)
    else:
        ax.axhline(1.0, color=COLORS["zero"], linestyle="--", linewidth=style.reference_line_width, zorder=0)
        ax.axhline(-1.0, color=COLORS["zero"], linestyle="--", linewidth=style.reference_line_width, zorder=0)
        ax.set_xlim(11, 850)
        lower, upper = ax.get_ylim()
        ax.set_yticks(np.arange(np.floor(lower), np.ceil(upper) + 1.0, 1.0))
    format_axis(ax, xlabel=x_label, ylabel=y_label, legend=True, legend_location="best")
    add_panel_label(ax, panel_label)
    return save_figure(
        fig,
        output_directory / stem,
        formats=("svg", "png"),
        mode="paper",
    )


def draw_beam_column_comparison(
    output_directory: Path,
    condition: str,
    panel_label: str,
    output_stem: str,
) -> tuple[Path, ...]:
    """Compare beam and column strain ratios within one axial-force condition."""
    style = apply_style("paper")
    fig, ax = plt.subplots(figsize=figure_size("paper"))
    source = WORKSPACE / "diana" / "data" / "processed" / condition / "cyclic_response.csv"
    table = read_table(source)
    ax.plot(
        table["case_id"],
        table["beam_strain_over_0p002"],
        color=COLORS["primary"],
        linestyle="-",
        label="Beam",
    )
    ax.plot(
        table["case_id"],
        table["column_strain_over_0p002"],
        color=COLORS["accent"],
        linestyle="--",
        label="Column",
    )
    ax.axhline(1.0, color=COLORS["zero"], linestyle="--", linewidth=style.reference_line_width, zorder=0)
    ax.axhline(-1.0, color=COLORS["zero"], linestyle="--", linewidth=style.reference_line_width, zorder=0)
    ax.set_xlim(11, 850)
    lower, upper = ax.get_ylim()
    ax.set_yticks(np.arange(np.floor(lower), np.ceil(upper) + 1.0, 1.0))
    format_axis(
        ax,
        xlabel="Analysis step",
        ylabel=r"Longitudinal strain, $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$",
        legend=True,
        legend_location="best",
    )
    add_panel_label(ax, panel_label)
    return save_figure(
        fig,
        output_directory / output_stem,
        formats=("svg", "png"),
        mode="paper",
    )




def draw_joint_stirrup_comparison(output_directory: Path) -> tuple[Path, ...]:
    """Overlay the canonical joint-stirrup response for the configured conditions."""
    style = apply_style("paper")
    fig, ax = plt.subplots(figsize=figure_size("paper"))
    for condition, label, color, line_style in CONDITIONS:
        source = WORKSPACE / "diana" / "data" / "processed" / condition / "joint_stirrup_response.csv"
        table = read_table(source)
        ax.plot(
            table["case_id"],
            table["joint_stirrup_exx"] / 0.002,
            color=color,
            linestyle=line_style,
            label=label,
        )
    ax.axhline(1.0, color=COLORS["zero"], linestyle=":", linewidth=style.reference_line_width, zorder=0)
    ax.axhline(-1.0, color=COLORS["zero"], linestyle=":", linewidth=style.reference_line_width, zorder=0)
    lower, upper = ax.get_ylim()
    ax.set_yticks(np.arange(np.floor(lower), np.ceil(upper) + 1.0, 1.0))
    format_axis(
        ax,
        xlabel="Analysis step",
        ylabel=r"Joint stirrup strain, $\epsilon_{\mathrm{xx}}/\epsilon_{\mathrm{y}}$",
        legend=True,
        legend_location="best",
    )
    add_panel_label(ax, "(f)")
    return save_figure(
        fig,
        output_directory / "06_joint_stirrup_strain_vs_case_id",
        formats=("svg", "png"),
        mode="paper",
    )

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        required=True,
    )
    parser.add_argument("--variant", default="changed_column_longitudinal_rebar")
    parser.add_argument("--variant-label", default="Changed Column Longitudinal Rebar")
    args = parser.parse_args()
    global CONDITIONS
    CONDITIONS = (
        ("origin", "Original", COLORS["primary"], "-"),
        (args.variant, args.variant_label, COLORS["accent"], "--"),
    )
    missing = [
        condition
        for condition, *_ in CONDITIONS
        if not (WORKSPACE / "diana" / "data" / "processed" / condition / "cyclic_response.csv").is_file()
    ]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing processed data for: {joined}. Run prepare_cyclic_comparison_data.py first."
        )
    created: list[Path] = []
    for specification in OUTPUTS:
        created.extend(draw_comparison(args.output_directory, *specification))
    created.extend(
        draw_beam_column_comparison(
            args.output_directory,
            "origin",
            "(d)",
            "04_beam_column_strain_origin",
        )
    )
    created.extend(
        draw_beam_column_comparison(
            args.output_directory,
            args.variant,
            "(e)",
            "05_beam_column_strain_variant",
        )
    )
    created.extend(draw_joint_stirrup_comparison(args.output_directory))
    print(f"Created {len(created)} files in {args.output_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
