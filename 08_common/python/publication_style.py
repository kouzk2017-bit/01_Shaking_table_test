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

# The project's figure mode, one switch for every script: 08_common/config/plot_config.json
# "figure.style_mode" ("presentation" for slides, "paper" for the thesis/papers).
try:
    import json as _json
    PROJECT_MODE = _json.loads((Path(__file__).resolve().parents[1] / "config" / "plot_config.json")
                               .read_text(encoding="utf-8"))["figure"]["style_mode"]
except (OSError, KeyError, ValueError):
    PROJECT_MODE = DEFAULT_STYLE_MODE

# One y range for every rebar-strain (eps/eps_y) time history shown in presentations, so test and
# model figures can be compared at a glance: plot_config.json "figure.rebar_strain_ylim".
try:
    REBAR_STRAIN_YLIM = tuple(_json.loads((Path(__file__).resolve().parents[1] / "config" / "plot_config.json")
                                          .read_text(encoding="utf-8"))["figure"]["rebar_strain_ylim"])
except (OSError, KeyError, ValueError):
    REBAR_STRAIN_YLIM = (-3.0, 10.0)

# Model-comparison conventions (plot_config.json "figure"): story drift / joint angle time histories
# on one y range; test curve grey, model curve blue (COLORS["primary"]).
try:
    _figure = _json.loads((Path(__file__).resolve().parents[1] / "config" / "plot_config.json")
                          .read_text(encoding="utf-8"))["figure"]
    ANGLE_YLIM = tuple(_figure["angle_ylim"])
    TEST_COLOR = _figure["test_color"]
except (OSError, KeyError, ValueError):
    ANGLE_YLIM, TEST_COLOR = (-0.04, 0.04), "0.6"


def figure_size(mode: str | None = None, *, portrait: bool = False) -> tuple[float, float]:
    """Return the standard landscape or portrait dimensions."""
    style = resolve_style(mode) if mode else phd_style.active_style()
    return style.portrait_size if portrait else style.figure_size


apply_style()
