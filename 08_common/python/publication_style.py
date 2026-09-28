"""Figure style entry point for the shaking-table project.

All appearance comes from the user-wide ``~/.matplotlib/phd_style.py`` and its
rc files, shared with every other PhD project; this module only re-exports it
under the names this project already uses.  Modes: ``paper`` (default) and
``presentation`` (= ``ppt``, larger text only).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

_STYLE_DIR = Path.home() / ".matplotlib"
if str(_STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(_STYLE_DIR))

import phd_style  # noqa: E402
from phd_style import (  # noqa: E402,F401
    COLORS,
    add_panel_label,
    apply_style,
    format_axis,
    line_width,
    reference_line_kwargs,
    resolve_style,
    save_figure,
    standard_size,
)

PublicationStyle = phd_style.Style
STYLE_MODE_ENVIRONMENT_VARIABLE = "SHAKING_TABLE_PLOT_MODE"
DEFAULT_STYLE_MODE = "paper"
STYLES = ("paper", "presentation")


def figure_size(mode: str | None = None, *, portrait: bool = False) -> tuple[float, float]:
    """Return the standard landscape or portrait dimensions."""
    style = resolve_style(mode) if mode else phd_style.active_style()
    return style.portrait_size if portrait else style.figure_size


apply_style()
