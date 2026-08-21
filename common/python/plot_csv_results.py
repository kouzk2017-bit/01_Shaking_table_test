"""Plot ten-story results using generated CSV files as the only data source."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ten_story_pipeline import load_csv
from publication_style import (
    COLORS,
    apply_style,
    figure_size,
    format_axis,
    save_figure,
)

CONTRIBUTION_BAR_WIDTH = 0.35
CONTRIBUTION_YLABEL = "Joint rotation / story drift ratio"


def _column(headers: list[str], data: np.ndarray, name: str) -> np.ndarray:
    try:
        return data[:, headers.index(name)]
    except ValueError as exc:
        raise KeyError(f"CSV column not found: {name}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_plot_config(path: Path, year: int) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        shared = json.load(stream)
    required_shared = {"defaults", "years", "figure"}
    missing_shared = required_shared - set(shared)
    if missing_shared:
        raise ValueError(f"Shared plot config is missing fields: {sorted(missing_shared)}")
    year_key = str(year)
    if year_key not in shared["years"]:
        raise ValueError(f"Shared plot config has no rules for year {year}")
    config = {
        "year": year,
        **shared["defaults"],
        **shared["years"][year_key],
        "figure": shared["figure"],
        "figure_overrides": shared.get("figure_overrides", {}),
    }
    required = {
        "year",
        "time_window_s",
        "peak_count",
        "peak_mode",
        "peak_significance_fraction",
        "peak_minimum_separation_s",
        "floors",
        "figure",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"Plot config is missing fields: {sorted(missing)}")
    if config["peak_mode"] not in {"min", "max"}:
        raise ValueError("peak_mode must be 'min' or 'max'")
    if not 0.0 < float(config["peak_significance_fraction"]) <= 1.0:
        raise ValueError("peak_significance_fraction must be in (0, 1]")
    if float(config["peak_minimum_separation_s"]) < 0.0:
        raise ValueError("peak_minimum_separation_s must be nonnegative")
    return config


def _local_extrema(values: np.ndarray, candidate_mask: np.ndarray, mode: str) -> np.ndarray:
    """Return all local extrema; deliberately applies no time-separation rule."""
    previous = values[:-2]
    current = values[1:-1]
    following = values[2:]
    finite = np.isfinite(previous) & np.isfinite(current) & np.isfinite(following)
    if mode == "min":
        extrema = ((current < previous) & (current <= following)) | (
            (current <= previous) & (current < following)
        )
    else:
        extrema = ((current > previous) & (current >= following)) | (
            (current >= previous) & (current > following)
        )
    indices = np.flatnonzero(extrema & finite) + 1
    return indices[candidate_mask[indices]]


def select_peaks(
    time: np.ndarray,
    drift: np.ndarray,
    *,
    mode: str,
    count: int,
    time_window: tuple[float, float],
    manual_times: list[float] | None = None,
    significance_fraction: float = 0.30,
    minimum_separation_s: float = 0.50,
) -> tuple[np.ndarray, str]:
    """Select the first consecutive significant, separated extrema."""
    window_mask = (time >= time_window[0]) & (time <= time_window[1])
    if manual_times is not None:
        if len(manual_times) != count:
            raise ValueError(f"Manual peak list must contain exactly {count} times")
        window_indices = np.flatnonzero(window_mask)
        if not window_indices.size:
            raise ValueError("No samples fall inside the configured plot time window")
        selected = np.array(
            [window_indices[np.argmin(np.abs(time[window_indices] - value))] for value in manual_times],
            dtype=int,
        )
        if np.unique(selected).size != selected.size:
            raise ValueError("Manual peak times resolve to duplicate CSV samples")
        return np.sort(selected), "manual"

    candidates = _local_extrema(drift, window_mask, mode)
    candidates = (
        candidates[drift[candidates] < 0.0]
        if mode == "min"
        else candidates[drift[candidates] > 0.0]
    )
    oriented = -drift if mode == "min" else drift
    threshold = significance_fraction * float(np.max(oriented[window_mask]))
    candidates = candidates[oriented[candidates] >= threshold]
    selected: list[int] = []
    for index in candidates:
        if (
            not selected
            or float(time[index] - time[selected[-1]]) >= minimum_separation_s
        ):
            selected.append(int(index))
        if len(selected) == count:
            break
    if len(selected) < count:
        raise ValueError(
            f"Only {len(selected)} significant, separated local {mode} extrema "
            f"found in {time_window[0]}-{time_window[1]} s; need {count}"
        )
    return np.asarray(selected, dtype=int), "automatic_consecutive_significant"


def _save(fig, path: Path, figure_config: dict) -> tuple[Path, ...]:
    extension = path.suffix.lower().lstrip(".") or "png"
    return save_figure(
        fig,
        path.with_suffix(""),
        formats=(extension, "pdf"),
        mode=figure_config.get("style_mode", "paper"),
    )


def _manual_times(config: dict, case_name: str, floor: int) -> list[float] | None:
    overrides = config.get("manual_peak_times_s", {})
    case_overrides = overrides.get(case_name, {})
    values = case_overrides.get(f"{floor}F")
    return [float(value) for value in values] if values is not None else None


def draw_contribution_bars(
    ax,
    contribution: np.ndarray,
    *,
    labels: str | list[str] | tuple[str, ...] | None = None,
    title: str | None = None,
):
    """Apply the one shared contribution-bar format used by both test years."""
    if labels is None:
        labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:contribution.size])
    bars = ax.bar(
        list(labels),
        contribution,
        width=CONTRIBUTION_BAR_WIDTH,
        color=COLORS["primary"],
    )
    format_axis(
        ax,
        xlabel="Peak",
        ylabel=CONTRIBUTION_YLABEL,
        title=title,
        legend=False,
        grid=False,
    )
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks(np.arange(0.0, 1.01, 0.1))
    ax.grid(True, axis="y")
    return bars


def format_time_history_limits(
    ax,
    *,
    time_window: tuple[float, float] = (10.0, 30.0),
) -> None:
    """Use the shared exact limits and ticks for drift time histories."""
    ax.set_xlim(time_window)
    ax.set_xticks(np.arange(time_window[0], time_window[1] + 0.1, 5.0))
    ax.set_ylim(-0.04, 0.04)
    ax.set_yticks(np.linspace(-0.04, 0.04, 9))
    ax.margins(x=0.0, y=0.0)


def format_hysteresis_limits(ax) -> None:
    """Use the shared exact limits and ticks for drift-shear hysteresis."""
    ax.set_xlim(-0.04, 0.04)
    ax.set_xticks(np.linspace(-0.04, 0.04, 9))
    ax.set_ylim(-4000.0, 4000.0)
    ax.set_yticks(np.arange(-4000.0, 4000.1, 1000.0))
    ax.margins(x=0.0, y=0.0)


def draw_selected_peak_markers(
    ax,
    time: np.ndarray,
    story_drift: np.ndarray,
    selected: np.ndarray,
    *,
    mode: str,
) -> None:
    """Mark the four selected story-drift peaks with filled triangles and letters."""
    if mode not in {"min", "max"}:
        raise ValueError("Peak marker mode must be 'min' or 'max'")
    marker = "v" if mode == "min" else "^"
    vertical_offset = -10 if mode == "min" else 10
    vertical_alignment = "top" if mode == "min" else "bottom"
    ax.scatter(
        time[selected],
        story_drift[selected],
        marker=marker,
        s=28,
        facecolor="black",
        edgecolor="black",
        linewidth=0.6,
        zorder=5,
    )
    selected_times = np.sort(time[selected])
    clustered = (
        selected_times.size > 1
        and float(np.min(np.diff(selected_times))) < 0.30
    )
    cluster_offsets = ((-10, 18), (10, 30), (-10, -18), (10, -30))
    for position, (label, index) in enumerate(
        zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", selected)
    ):
        if clustered:
            horizontal_offset, label_vertical_offset = cluster_offsets[
                position % len(cluster_offsets)
            ]
            label_vertical_alignment = (
                "bottom" if label_vertical_offset > 0 else "top"
            )
        else:
            horizontal_offset = 0
            label_vertical_offset = vertical_offset
            label_vertical_alignment = vertical_alignment
        ax.annotate(
            label,
            (time[index], story_drift[index]),
            xytext=(horizontal_offset, label_vertical_offset),
            textcoords="offset points",
            ha="center",
            va=label_vertical_alignment,
            color="black",
            fontweight="bold",
            annotation_clip=True,
        )


def plot_rebar_strain_figure(
    time: np.ndarray,
    beam: np.ndarray,
    column: np.ndarray,
    output_stem: Path,
    *,
    title: str | None = None,
    time_window: tuple[float, float] = (10.0, 30.0),
) -> tuple[Path, ...]:
    """Draw one shared 4F/6F rebar-strain figure for either test year."""
    style = apply_style("paper")
    mask = (time >= time_window[0]) & (time <= time_window[1])
    fig, ax = plt.subplots(figsize=style.figure_size)
    ax.plot(
        time[mask],
        column[mask],
        color=COLORS["primary"],
        label="Column longitudinal rebar",
    )
    ax.plot(
        time[mask],
        beam[mask],
        color=COLORS["accent"],
        linestyle="--",
        label="Beam longitudinal rebar",
    )
    format_axis(
        ax,
        xlabel="Time (s)",
        ylabel=r"$\epsilon/\epsilon_y$",
        title=title,
        legend=True,
        legend_location="upper right",
    )
    ax.set_xlim(time_window)
    ax.set_xticks(np.arange(time_window[0], time_window[1] + 0.1, 5.0))
    ax.set_ylim(-3.0, 8.0)
    ax.set_yticks(np.arange(-3.0, 8.1, 1.0))
    ax.margins(x=0.0, y=0.0)
    return save_figure(fig, output_stem, formats=("png", "pdf"), mode="paper")


def _write_selected_peaks(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = (
        "Case", "Floor", "Peak", "Selection", "SampleIndex", "Time_s",
        "StoryDrift_rad", "JointRotation_rad", "Contribution_ratio",
    )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    return path


def plot_case(
    result_directory: Path,
    case_name: str,
    config_path: Path,
    *,
    year: int,
    output_directory: Path | None = None,
    write_sidecars: bool = True,
) -> list[Path]:
    """Generate standard figures without reading raw data, Excel or NPZ files."""
    config = load_plot_config(config_path, year)
    csv_directory = result_directory / "csv"
    source_paths = {
        "story_drift_y": csv_directory / "story_drift_y.csv",
        "joint_rotation": csv_directory / "joint_rotation.csv",
        "story_shear_y": csv_directory / "story_shear_y.csv",
    }
    drift_h, drift = load_csv(source_paths["story_drift_y"])
    joint_h, joint = load_csv(source_paths["joint_rotation"])
    shear_h, shear = load_csv(source_paths["story_shear_y"])
    figures = output_directory or result_directory
    outputs: list[Path] = []
    peak_rows: list[dict] = []
    time = _column(drift_h, drift, "Time_s")
    joint_time = _column(joint_h, joint, "Time_s")
    shear_time = _column(shear_h, shear, "Time_s")
    common_length = min(time.size, joint_time.size, shear_time.size)
    t = time[:common_length]
    if not (
        np.allclose(t, joint_time[:common_length], rtol=0.0, atol=1e-9)
        and np.allclose(t, shear_time[:common_length], rtol=0.0, atol=1e-9)
    ):
        raise ValueError("Time columns in the three source CSV files do not align")

    window = tuple(float(value) for value in config["time_window_s"])
    figure_config = config["figure"]
    style_mode = figure_config.get("style_mode", "paper")
    apply_style(style_mode)
    figsize = figure_size(mode=style_mode)
    extension = figure_config.get("format", "png")
    with plt.rc_context():
        for offset, floor in enumerate(int(value) for value in config["floors"]):
            d = _column(drift_h, drift, f"{floor}F_rad")[:common_length]
            j = _column(joint_h, joint, f"{floor}F_rad")[:common_length]
            s = _column(shear_h, shear, f"{floor}F_kN")[:common_length]
            mask = (t >= window[0]) & (t <= window[1])
            selected, selection = select_peaks(
                t,
                d,
                mode=config["peak_mode"],
                count=int(config["peak_count"]),
                time_window=window,
                manual_times=_manual_times(config, case_name, floor),
                significance_fraction=float(config["peak_significance_fraction"]),
                minimum_separation_s=float(config["peak_minimum_separation_s"]),
            )

            for label, index in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", selected):
                peak_rows.append({
                    "Case": case_name,
                    "Floor": f"{floor}F",
                    "Peak": label,
                    "Selection": selection,
                    "SampleIndex": int(index),
                    "Time_s": f"{t[index]:.10g}",
                    "StoryDrift_rad": f"{d[index]:.15g}",
                    "JointRotation_rad": f"{j[index]:.15g}",
                    "Contribution_ratio": f"{abs(j[index] / d[index]):.15g}",
                })

            fig, ax = plt.subplots(figsize=figsize)
            ax.plot(t[mask], j[mask], label="Joint deformation")
            ax.plot(t[mask], d[mask], "--", color=COLORS["accent"], label="Story drift")
            format_axis(
                ax,
                xlabel="Time (s)",
                ylabel="Drift (rad)",
                legend=True,
                legend_location="upper right",
            )
            format_time_history_limits(ax, time_window=window)
            draw_selected_peak_markers(
                ax,
                t,
                d,
                selected,
                mode=config["peak_mode"],
            )
            outputs.extend(_save(
                fig,
                figures / f"chart_{1 + offset:03d}_{case_name} {floor}F Joint Deformation and Story Drift.{extension}",
                figure_config,
            ))

            contribution = np.abs(j[selected] / d[selected])
            fig, ax = plt.subplots(figsize=figsize)
            draw_contribution_bars(ax, contribution)
            outputs.extend(_save(
                fig,
                figures / f"chart_{3 + offset:03d}_{case_name} {floor}F Joint-Deformation Contribution.{extension}",
                figure_config,
            ))

            fig, ax = plt.subplots(figsize=figsize)
            ax.plot(d[mask], s[mask], color=COLORS["primary"])
            format_axis(
                ax,
                xlabel="Story drift (rad)",
                ylabel="Shear force (kN)",
                legend=False,
            )
            format_hysteresis_limits(ax)
            outputs.extend(_save(
                fig,
                figures / f"chart_{5 + offset:03d}_{case_name} {floor}F Story Drift-Shear Force Relationship.{extension}",
                figure_config,
            ))

    if write_sidecars:
        selected_path = _write_selected_peaks(csv_directory / "selected_peaks.csv", peak_rows)
        metadata = {
            "case": case_name,
            "data_source": "generated CSV only",
            "raw_data_recomputed": False,
            "peak_rule": {
                "mode": config["peak_mode"],
                "count": config["peak_count"],
                "significance_fraction": config["peak_significance_fraction"],
                "minimum_time_separation_s": config["peak_minimum_separation_s"],
                "selection_order": "first consecutive significant peaks",
                "label_order": "chronological",
                "contribution_formula": "abs(joint_rotation / story_drift)",
            },
            "plot_config": str(config_path.resolve()),
            "plot_config_sha256": _sha256(config_path),
            "source_csv_sha256": {name: _sha256(path) for name, path in source_paths.items()},
            "selected_peaks_csv": str(selected_path),
            "figure_files": [str(path) for path in outputs],
        }
        metadata_path = result_directory / "plot_metadata.json"
        with metadata_path.open("w", encoding="utf-8") as stream:
            json.dump(metadata, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    return outputs
