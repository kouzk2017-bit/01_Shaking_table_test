"""Rebar-strain trace helpers shared by regenerate_current_figures.py."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from config import (
    PLOT_END,
    PLOT_START,
    REBAR_CHANNELS,
    REBAR_PLOT_CHANNELS,
)

COMMON_PYTHON = Path(__file__).resolve().parents[3] / "common" / "python"
sys.path.insert(0, str(COMMON_PYTHON))

from plot_csv_results import plot_rebar_strain_figure


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
    plot_rebar_strain_figure(
        time,
        beam,
        column,
        stem,
        time_window=(PLOT_START, PLOT_END),
    )
