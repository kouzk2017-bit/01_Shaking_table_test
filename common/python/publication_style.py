"""Shared figure appearance and export rules for the shaking-table project.

All active Python plotting entry points import this module.  Plot-specific
choices such as axis limits, peak annotations, and engineering reference lines
remain in the individual plotting functions.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterator, Sequence
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


STYLE_MODE_ENVIRONMENT_VARIABLE = "SHAKING_TABLE_PLOT_MODE"
DEFAULT_STYLE_MODE = "paper"

# Colour-blind-safe palette based on the Okabe-Ito family.
COLORS = {
    "primary": "#0072B2",
    "accent": "#D55E00",
    "green": "#009E73",
    "orange": "#E69F00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "black": "#222222",
    "grid": "#B8B8B8",
    "zero": "#6E6E6E",
}


@dataclass(frozen=True)
class PublicationStyle:
    """Immutable common settings for one output context."""

    name: str
    font: str
    figure_size: tuple[float, float]
    portrait_size: tuple[float, float]
    label_size: float
    tick_size: float
    legend_size: float
    title_size: float
    panel_label_size: float
    line_width: float
    reference_line_width: float
    marker_size: float
    axis_width: float
    major_tick_length: float
    minor_tick_length: float
    grid_alpha: float
    grid_line_width: float
    output_dpi: int
    pad_inches: float
    show_title: bool


STYLES = {
    "paper": PublicationStyle(
        name="paper",
        font="Times New Roman",
        figure_size=(6.5, 4.5),
        portrait_size=(5.0, 6.5),
        label_size=12,
        tick_size=10,
        legend_size=10,
        title_size=12,
        panel_label_size=11,
        line_width=1.7,
        reference_line_width=0.8,
        marker_size=5.0,
        axis_width=0.9,
        major_tick_length=4.0,
        minor_tick_length=2.5,
        grid_alpha=0.22,
        grid_line_width=0.7,
        output_dpi=600,
        pad_inches=0.05,
        show_title=False,
    ),
    "presentation": PublicationStyle(
        name="presentation",
        font="Arial",
        figure_size=(10.0, 5.625),
        portrait_size=(7.5, 10.0),
        label_size=18,
        tick_size=15,
        legend_size=15,
        title_size=20,
        panel_label_size=17,
        line_width=2.4,
        reference_line_width=1.1,
        marker_size=7.0,
        axis_width=1.2,
        major_tick_length=5.5,
        minor_tick_length=3.0,
        grid_alpha=0.18,
        grid_line_width=0.9,
        output_dpi=300,
        pad_inches=0.06,
        show_title=True,
    ),
}

_ACTIVE_STYLE = STYLES[DEFAULT_STYLE_MODE]


def resolve_style(mode: str | None = None) -> PublicationStyle:
    """Return a validated style, using the project environment override."""
    key = (
        mode
        or os.environ.get(STYLE_MODE_ENVIRONMENT_VARIABLE, DEFAULT_STYLE_MODE)
    ).strip().lower()
    if key not in STYLES:
        choices = ", ".join(sorted(STYLES))
        raise ValueError(f"Unknown figure style {key!r}; expected one of: {choices}")
    return STYLES[key]


def apply_style(mode: str | None = None) -> PublicationStyle:
    """Apply the common Matplotlib style and return its settings."""
    global _ACTIVE_STYLE
    style = resolve_style(mode)
    _ACTIVE_STYLE = style
    serif_fonts = [style.font, "Times New Roman", "DejaVu Serif"]
    sans_fonts = [style.font, "Arial", "DejaVu Sans"]
    plt.rcParams.update({
        "font.family": "sans-serif" if style.name == "presentation" else "serif",
        "font.serif": serif_fonts,
        "font.sans-serif": sans_fonts,
        "mathtext.fontset": "stix",
        "axes.unicode_minus": True,
        "figure.figsize": style.figure_size,
        "figure.dpi": 100,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.labelsize": style.label_size,
        "axes.titlesize": style.title_size,
        "axes.titleweight": "normal",
        "axes.linewidth": style.axis_width,
        "axes.axisbelow": True,
        "axes.prop_cycle": plt.cycler(color=[
            COLORS["primary"], COLORS["accent"], COLORS["green"],
            COLORS["orange"], COLORS["purple"], COLORS["sky"],
        ]),
        "xtick.labelsize": style.tick_size,
        "ytick.labelsize": style.tick_size,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": style.major_tick_length,
        "ytick.major.size": style.major_tick_length,
        "xtick.minor.size": style.minor_tick_length,
        "ytick.minor.size": style.minor_tick_length,
        "xtick.major.width": style.axis_width,
        "ytick.major.width": style.axis_width,
        "xtick.minor.width": style.axis_width,
        "ytick.minor.width": style.axis_width,
        "legend.fontsize": style.legend_size,
        "legend.frameon": False,
        "legend.handlelength": 2.4,
        "legend.handletextpad": 0.7,
        "legend.borderaxespad": 0.5,
        "lines.linewidth": style.line_width,
        "lines.markersize": style.marker_size,
        "grid.color": COLORS["grid"],
        "grid.linestyle": "--",
        "grid.linewidth": style.grid_line_width,
        "grid.alpha": style.grid_alpha,
        "savefig.dpi": style.output_dpi,
        "savefig.format": "png",
        "savefig.facecolor": "white",
        "savefig.edgecolor": "none",
        "savefig.bbox": "tight",
        "savefig.pad_inches": style.pad_inches,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })
    return style


@contextmanager
def style_context(mode: str | None = None) -> Iterator[PublicationStyle]:
    """Temporarily apply a common style without leaking rcParams changes."""
    global _ACTIVE_STYLE
    previous = _ACTIVE_STYLE
    with plt.rc_context():
        style = apply_style(mode)
        try:
            yield style
        finally:
            _ACTIVE_STYLE = previous


def figure_size(
    mode: str | None = None,
    *,
    portrait: bool = False,
) -> tuple[float, float]:
    """Return the standard landscape or portrait dimensions."""
    style = resolve_style(mode) if mode else _ACTIVE_STYLE
    return style.portrait_size if portrait else style.figure_size


def format_axis(
    ax,
    xlabel: str | None = None,
    ylabel: str | None = None,
    title: str | None = None,
    *,
    legend: bool = False,
    legend_location: str = "best",
    grid: bool = True,
    grid_axis: str = "both",
):
    """Apply shared labels, ticks, frame, grid, and legend formatting."""
    style = _ACTIVE_STYLE
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if style.show_title and title:
        ax.set_title(title)
    ax.tick_params(
        which="major",
        direction="in",
        top=True,
        right=True,
        width=style.axis_width,
        length=style.major_tick_length,
        pad=4,
    )
    ax.tick_params(
        which="minor",
        direction="in",
        top=True,
        right=True,
        width=style.axis_width,
        length=style.minor_tick_length,
    )
    for spine in ax.spines.values():
        spine.set_linewidth(style.axis_width)
        spine.set_color(COLORS["black"])
    ax.grid(grid, which="major", axis=grid_axis)
    if legend:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(
                handles,
                labels,
                loc=legend_location,
                frameon=False,
                fontsize=style.legend_size,
            )
    return ax


def add_panel_label(ax, label: str, *, x: float = 0.02, y: float = 0.98):
    """Add a consistent panel label such as ``(a)`` in axes coordinates."""
    return ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=_ACTIVE_STYLE.panel_label_size,
        fontweight="bold",
    )


def save_figure(
    fig,
    output_stem: str | os.PathLike[str],
    *,
    formats: Sequence[str] = ("png", "pdf"),
    mode: str | None = None,
    close: bool = True,
) -> tuple[Path, ...]:
    """Save a figure with identical geometry in raster and vector formats."""
    style = resolve_style(mode) if mode else _ACTIVE_STYLE
    stem = Path(output_stem).with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)
    normalized_formats = tuple(dict.fromkeys(value.lower().lstrip(".") for value in formats))
    unsupported = set(normalized_formats) - {"png", "pdf", "svg", "eps", "tif", "tiff"}
    if unsupported:
        raise ValueError(f"Unsupported figure formats: {sorted(unsupported)}")
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="This figure includes Axes that are not compatible with tight_layout.*",
            category=UserWarning,
        )
        fig.tight_layout(pad=0.5)
    outputs: list[Path] = []
    for extension in normalized_formats:
        path = stem.with_suffix(f".{extension}")
        kwargs = {
            "bbox_inches": "tight",
            "pad_inches": style.pad_inches,
            "facecolor": "white",
            "edgecolor": "none",
        }
        if extension in {"png", "tif", "tiff"}:
            kwargs["dpi"] = style.output_dpi
        fig.savefig(path, **kwargs)
        outputs.append(path)
    if close:
        plt.close(fig)
    return tuple(outputs)


apply_style()
