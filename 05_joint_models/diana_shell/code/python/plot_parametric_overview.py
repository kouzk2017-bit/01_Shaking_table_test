"""All shell parametric cases in one figure per quantity (standard protocol).

Original + J12-M/H + J16-L/M/H together: colour = number of column bars,
line style / marker = joint hoop level.  Full hysteresis loops of six cases
overlap, so each quantity is drawn at the load reversals (skeleton curves).
Rebar strains are at the common positions (right beam bottom bar at the column
face, upper-column left bar at the beam face; see 06_results/data_sources/).

Output: 06_results/comparison/shell_variants/all_variants/
  01 story shear, 02 joint deformation angle, 03 beam bar strain,
  04 column bar strain (all at the reversals vs story drift),
  05 story drift at first yield of the beam and column bars.
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
OUTPUT = WORKSPACE / "06_results" / "comparison" / "shell_variants" / "all_variants"
PLOT_CONFIG = WORKSPACE / "08_common" / "config" / "plot_config.json"
YIELD_RATIO = 1.0

HOOP_STYLE = {"": ("-", "o"), "L": (":", "^"), "M": ("--", "s"), "H": ("-", "D")}
BAR_COLOR = {"": COLORS["black"], "12": COLORS["primary"], "16": COLORS["accent"]}
# (condition, label, column bars, hoop level)
CASES = (
    ("origin", "Original", "", ""),
    ("j12_m", "J12-M", "12", "M"),
    ("j12_h", "J12-H", "12", "H"),
    ("j16_l", "J16-L", "16", "L"),
    ("j16_m", "J16-M", "16", "M"),
    ("j16_h", "J16-H", "16", "H"),
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


def plot_skeleton(cases: dict, column: str, ylabel: str, name: str, mode: str, yield_lines: bool = False) -> None:
    fig, ax = plt.subplots(figsize=figure_size(mode))
    for condition, label, bars, hoop in CASES:
        peaks = cases[condition]
        style, marker = HOOP_STYLE[hoop]
        ax.plot(peaks["story_drift_rad"], peaks[column], linestyle=style, marker=marker,
                color=BAR_COLOR[bars], label=label)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    if yield_lines:
        for level in (YIELD_RATIO, -YIELD_RATIO):
            ax.axhline(level, **reference_line_kwargs(linestyle="--"), zorder=0)
    format_axis(ax, xlabel="Story drift (rad)", ylabel=ylabel, legend=True)
    save_figure(fig, OUTPUT / name, formats=("png",), mode=mode)
    plt.close(fig)


def first_yield_drift(data: pd.DataFrame, column: str) -> float:
    hit = data[column].abs() >= YIELD_RATIO
    return float(abs(data.loc[hit.idxmax(), "story_drift_rad"])) if hit.any() else np.nan


def plot_first_yield(full: dict, mode: str) -> pd.DataFrame:
    rows = [{"case": label,
             "beam_first_yield_drift_rad": first_yield_drift(full[c], "beam_strain_over_0p002"),
             "column_first_yield_drift_rad": first_yield_drift(full[c], "column_strain_over_0p002")}
            for c, label, *_ in CASES]
    table = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=figure_size(mode))
    y = np.arange(len(table))
    ax.plot(table["beam_first_yield_drift_rad"], y, linestyle="none", marker="o", color=COLORS["primary"],
            label="Beam bar (right, bottom)")
    ax.plot(table["column_first_yield_drift_rad"], y, linestyle="none", marker="s", color=COLORS["accent"],
            label="Column bar (upper, left)")
    ax.set_yticks(y, table["case"])
    ax.invert_yaxis()
    format_axis(ax, xlabel="|Story drift| at first yield (rad)", ylabel="", legend=True)
    save_figure(fig, OUTPUT / "05_first_yield_drift", formats=("png",), mode=mode)
    plt.close(fig)
    return table


def main() -> None:
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]
    apply_style(mode)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    full = {c: read_case(c) for c, *_ in CASES}
    peaks = {c: reversals(d) for c, d in full.items()}
    plot_skeleton(peaks, "story_shear_kN", "Story shear (kN)", "01_story_shear_skeleton", mode)
    plot_skeleton(peaks, "deformation_angle_rad", "Joint deformation angle (rad)", "02_joint_deformation_skeleton", mode)
    plot_skeleton(peaks, "beam_strain_over_0p002", r"Beam bottom bar strain $\epsilon/\epsilon_y$",
                  "03_beam_bar_strain_at_reversals", mode, yield_lines=True)
    plot_skeleton(peaks, "column_strain_over_0p002", r"Upper column bar strain $\epsilon/\epsilon_y$",
                  "04_column_bar_strain_at_reversals", mode, yield_lines=True)
    table = plot_first_yield(full, mode)
    table.round(4).to_csv(OUTPUT / "first_yield_drift.csv", index=False)
    pd.concat({label: peaks[c] for c, label, *_ in CASES}, names=["case"]).round(5).to_csv(
        OUTPUT / "reversal_values.csv")
    print(table.to_string(index=False))
    print(f"Wrote figures to {OUTPUT}")


if __name__ == "__main__":
    main()
