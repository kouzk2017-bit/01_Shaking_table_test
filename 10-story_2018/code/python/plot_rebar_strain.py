"""Plot case-20 4F/6F rebar strain in the 2015 publication style."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import (
    DATA_DIRECTORY,
    FIGURE_DIRECTORY,
    PLOT_END,
    PLOT_START,
    REBAR_CHANNELS,
    REBAR_PLOT_CHANNELS,
)
from plot_results import apply_style, format_axis, save


def _key(group: str) -> str:
    return group.lower().replace(" ", "_")


def _trace(data: np.lib.npyio.NpzFile, group: str) -> np.ndarray:
    jb, selected_channels = REBAR_PLOT_CHANNELS[group]
    configured_jb, channels = REBAR_CHANNELS[group]
    if jb != configured_jb or any(channel not in channels for channel in selected_channels):
        raise ValueError(f"Invalid selected channels for {group}: JB{jb:02d} {selected_channels}")
    indices = [channels.index(channel) for channel in selected_channels]
    return np.mean(data[_key(group)][:, indices], axis=1)


def _plot_floor(time: np.ndarray, beam: np.ndarray, column: np.ndarray, floor: int, stem: Path) -> None:
    mask = (time >= PLOT_START) & (time <= PLOT_END)
    fig, ax = plt.subplots(figsize=(6.0, 4.5))
    ax.plot(time[mask], column[mask], color="#0000FF", label="Column longitudinal rebar")
    ax.plot(time[mask], beam[mask], color="#FF0000", linestyle="--", label="Beam longitudinal rebar")
    format_axis(ax, "Time (s)", r"$\epsilon/\epsilon_y$", legend=True)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_xticks(np.arange(PLOT_START, PLOT_END + 0.1, 5.0))
    ax.set_ylim(-2.0, 8.0)
    ax.set_yticks(np.arange(-2.0, 8.1, 1.0))
    save(fig, stem)


def process() -> list[Path]:
    source = DATA_DIRECTORY / "rebar_strain.npz"
    if not source.is_file():
        raise FileNotFoundError(f"Run process_rebar_strain.py first: {source}")
    data = np.load(source)
    time = data["time"]
    apply_style()
    generated: list[Path] = []
    for offset, floor in enumerate((4, 6), start=7):
        stem = FIGURE_DIRECTORY / f"chart_{offset:03d}_2018 {floor}F Rebar Strain"
        _plot_floor(time, _trace(data, f"{floor}F_beam"), _trace(data, f"{floor}F_column"), floor, stem)
        generated.extend([stem.with_suffix(".png"), stem.with_suffix(".pdf")])
    return generated


if __name__ == "__main__":
    paths = process()
    print("Generated rebar-strain figures:")
    for path in paths:
        print(path)
