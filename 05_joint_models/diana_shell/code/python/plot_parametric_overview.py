"""All shell parametric cases in one figure per quantity (standard protocol).

Original + J12-M/H + J16-L/M/H together: colour = number of column bars,
line style / marker = joint hoop level.  Full hysteresis loops of six cases
overlap, so each quantity is drawn at the load reversals (skeleton curves).
Rebar strains are at the common positions (right beam bottom bar at the column
face, upper-column left bar at the beam face; see 06_results/data_sources/).

Outputs: 06_results/comparison/shell_variants/all_variants/ (Original + J12/J16) and
slab_vs_origin_skeleton/ (without / with slab flange), each:
  01 story shear, 02 joint deformation angle (at the reversals vs story drift),
  03/04 positive-drift pair: right beam bottom, upper column left;
  05/06 negative-drift pair: left beam bottom, upper column right (rebar strain at the reversals),
  07 story drift at first tension yield, beam vs column, per direction.
A case without an exported position is left out of that figure (origin: negative pair pending).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
from publication_style import COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure  # noqa: E402

PROCESSED = WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed"
RESULTS = WORKSPACE / "06_results" / "comparison" / "shell_variants"
PLOT_CONFIG = WORKSPACE / "08_common" / "config" / "plot_config.json"
YIELD_RATIO = 1.0

HOOP_STYLE = {"": ("-", "o"), "L": (":", "^"), "M": ("--", "s"), "H": ("-", "D"), "slab": ("--", "s")}
BAR_COLOR = {"": COLORS["black"], "12": COLORS["primary"], "16": COLORS["accent"], "slab": COLORS["green"]}
# (condition, label, column bars, hoop level)
PARAMETRIC = (
    ("origin", "Original", "", ""),
    ("j12_m", "J12-M", "12", "M"),
    ("j12_h", "J12-H", "12", "H"),
    ("j16_l", "J16-L", "16", "L"),
    ("j16_m", "J16-M", "16", "M"),
    ("j16_h", "J16-H", "16", "H"),
)
SLAB = (("origin", "No slab", "", ""), ("origin_slab", "With slab", "slab", "slab"))
BEAM_REBAR = (("origin", "Original", "", ""), ("beam_rebar", "Modified beam rebar", "12", "M"))
BEAM_AXIAL = (("beam_rebar", "Beam axial restrained", "", ""), ("beam_rebar_free", "Beam axial free", "12", "M"))
CASE_SETS = {"all_variants": PARAMETRIC, "slab_vs_origin_skeleton": SLAB, "beam_rebar_vs_origin_skeleton": BEAM_REBAR,
             "beam_axial_free_vs_restrained_skeleton": BEAM_AXIAL}
# rebar strain at the reversals, one beam + one column per loading direction (2026-10-09)
REBAR = (
    ("03_pos_right_beam_bottom", "beam_strain_over_0p002", r"Right beam bottom bar $\epsilon/\epsilon_y$"),
    ("04_pos_upper_column_left", "column_strain_over_0p002", r"Upper column left bar $\epsilon/\epsilon_y$"),
    ("05_neg_left_beam_bottom", "left_beam_strain_over_0p002", r"Left beam bottom bar $\epsilon/\epsilon_y$"),
    ("06_neg_upper_column_right", "column_right_strain_over_0p002", r"Upper column right bar $\epsilon/\epsilon_y$"),
)


def read_case(condition: str) -> pd.DataFrame:
    cyclic = pd.read_csv(PROCESSED / condition / "cyclic_response.csv")
    joint = pd.read_csv(PROCESSED / condition / "joint_deformation_angle.csv")[["load_step", "deformation_angle_rad"]]
    return cyclic.merge(joint, left_on="case_id", right_on="load_step").sort_values("case_id").reset_index(drop=True)


def reversals(data: pd.DataFrame) -> pd.DataFrame:
    """First reversal at each drift amplitude, plus the origin, ordered by drift."""
    drift = data["story_drift_rad"].to_numpy()
    turn = [i for i in range(1, len(drift) - 1) if (drift[i] - drift[i - 1]) * (drift[i + 1] - drift[i]) < 0]
    peaks = data.iloc[turn].copy()
    peaks["amplitude"] = peaks["story_drift_rad"].round(4)
    peaks = peaks.drop_duplicates("amplitude")
    zero = pd.DataFrame([{c: 0.0 for c in peaks.columns}])
    return pd.concat([peaks, zero]).sort_values("story_drift_rad")


def plot_skeleton(cases: dict, case_list, out: Path, column: str, ylabel: str, name: str, mode: str,
                  yield_lines: bool = False) -> None:
    fig, ax = plt.subplots(figsize=figure_size(mode))
    for condition, label, bars, hoop in case_list:
        peaks = cases[condition]
        if column not in peaks:  # position not exported for this case (yet)
            continue
        style, marker = HOOP_STYLE[hoop]
        ax.plot(peaks["story_drift_rad"], peaks[column], linestyle=style, marker=marker,
                color=BAR_COLOR[bars], label=label)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    if yield_lines:
        for level in (YIELD_RATIO, -YIELD_RATIO):
            ax.axhline(level, **reference_line_kwargs(linestyle="--"), zorder=0)
    format_axis(ax, xlabel="Story drift (rad)", ylabel=ylabel, legend=True)
    save_figure(fig, out / name, formats=("png",), mode=mode)
    plt.close(fig)


def first_yield_drift(data: pd.DataFrame, column: str) -> float:
    """First TENSION yield (strain >= eps_y); compressive yield is not counted (fixed 2026-10-08)."""
    if column not in data:
        return np.nan
    hit = data[column] >= YIELD_RATIO
    return float(abs(data.loc[hit.idxmax(), "story_drift_rad"])) if hit.any() else np.nan


def plot_first_yield(full: dict, case_list, out: Path, mode: str) -> pd.DataFrame:
    """Drift at first tension yield, beam vs column, per loading direction."""
    rows = [{"case": label,
             "neg_left_beam": first_yield_drift(full[c], "left_beam_strain_over_0p002"),
             "neg_upper_column_right": first_yield_drift(full[c], "column_right_strain_over_0p002"),
             "pos_right_beam": first_yield_drift(full[c], "beam_strain_over_0p002"),
             "pos_upper_column_left": first_yield_drift(full[c], "column_strain_over_0p002")}
            for c, label, *_ in case_list]
    table = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=figure_size(mode))
    y = np.arange(len(table))
    for key, label, marker, color, dy in (
            ("neg_left_beam", "Negative: beam (left, bottom)", "o", COLORS["primary"], -0.12),
            ("neg_upper_column_right", "Negative: column (upper, right)", "s", COLORS["primary"], -0.12),
            ("pos_right_beam", "Positive: beam (right, bottom)", "o", COLORS["accent"], 0.12),
            ("pos_upper_column_left", "Positive: column (upper, left)", "s", COLORS["accent"], 0.12)):
        ax.plot(table[key], y + dy, linestyle="none", marker=marker, color=color,
                markerfacecolor=color if marker == "o" else "none", label=label)
    ax.set_yticks(y, table["case"])
    ax.invert_yaxis()
    values = table.drop(columns="case").to_numpy(dtype=float)
    ax.set_xlim(np.nanmin(values) - 0.001, np.nanmax(values) + 0.008)  # room for the legend on the right
    ax.xaxis.set_major_locator(plt.MultipleLocator(0.005))
    format_axis(ax, xlabel="|Story drift| at first tension yield (rad)", ylabel="", legend=True,
                legend_location="lower right")
    save_figure(fig, out / "07_first_yield_by_direction", formats=("png",), mode=mode)
    plt.close(fig)
    return table


def main() -> None:
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]
    apply_style(mode)
    for folder, case_list in CASE_SETS.items():
        out = RESULTS / folder
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.png"):
            old.unlink()
        full = {c: read_case(c) for c, *_ in case_list}
        peaks = {c: reversals(d) for c, d in full.items()}
        plot_skeleton(peaks, case_list, out, "story_shear_kN", "Story shear (kN)", "01_story_shear_skeleton", mode)
        plot_skeleton(peaks, case_list, out, "deformation_angle_rad", "Joint deformation angle (rad)",
                      "02_joint_deformation_skeleton", mode)
        for name, column, ylabel in REBAR:
            plot_skeleton(peaks, case_list, out, column, ylabel, f"{name}_strain_at_reversals", mode, yield_lines=True)
        table = plot_first_yield(full, case_list, out, mode)
        table.round(4).to_csv(out / "first_yield_drift.csv", index=False)
        pd.concat({label: peaks[c] for c, label, *_ in case_list}, names=["case"]).round(5).to_csv(
            out / "reversal_values.csv")
        print(folder); print(table.to_string(index=False))


if __name__ == "__main__":
    main()
