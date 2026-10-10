"""Render the data-source tables (which node / gauge / position each curve comes from) as figures.

Input and output: ``06_results/data_sources/NN_*.csv`` -> ``NN_*.png`` next to it.
Edit the CSV when a node or gauge changes, then re-run this script.
'?' marks a position not yet confirmed; '*' marks the solid node used against the test.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
from publication_style import PROJECT_MODE, COLORS, apply_style, save_figure  # noqa: E402

FOLDER = WORKSPACE / "06_results" / "data_sources"
WRAP = 28              # characters per line in a cell
CHAR_WIDTH_EM = 0.5    # average character width / font size (Times)
LINE_HEIGHT_EM = 1.3   # line pitch / font size
CELL_PAD_LINES = 0.8   # vertical padding per row, in lines

NOTES = {
    "01_rebar_strain": "Joint 4 = top of story 4 (5F floor, JNT4). DIANA right = test west. "
                       "* = node used against the test (about 100 mm from the face). ? = position not confirmed.",
    "03_shell_variants": "One beam + one column per loading direction (2026-10-09). Model vs model: face node; "
                         "model vs test: the 100 mm node. Joint hoop nodes are not yet at one common position.",
}


def render(csv_path: Path) -> None:
    table = pd.read_csv(csv_path, dtype=str).fillna("")
    cells = [[textwrap.fill(value, WRAP) for value in row] for row in table.to_numpy()]
    header = [textwrap.fill(name, WRAP) for name in table.columns]
    lines = [max(c.count("\n") + 1 for c in row) for row in [header, *cells]]
    # Size the figure from the style's font size so the text prints at that size.
    font_in = plt.rcParams["font.size"] / 72
    width = len(header) * (WRAP + 3) * CHAR_WIDTH_EM * font_in
    rows_in = [(n + CELL_PAD_LINES) * LINE_HEIGHT_EM * font_in for n in lines]
    table_in = sum(rows_in)
    note = NOTES.get(csv_path.stem)
    note_lines = textwrap.fill(note, int(width / (CHAR_WIDTH_EM * font_in))) if note else ""
    note_in = (note_lines.count("\n") + 2) * LINE_HEIGHT_EM * font_in if note else 0.0
    fig = plt.figure(figsize=(width, table_in + note_in))
    ax = fig.add_axes((0, note_in / (table_in + note_in), 1, table_in / (table_in + note_in)))
    ax.axis("off")
    grid = ax.table(cellText=cells, colLabels=header, bbox=(0, 0, 1, 1), cellLoc="left", colLoc="left")
    grid.auto_set_font_size(False)
    grid.set_fontsize(plt.rcParams["font.size"])
    for (row, _), cell in grid.get_celld().items():
        cell.set_height(rows_in[row] / table_in)
        cell.PAD = 0.03
        cell.set_edgecolor("0.7")
        if row == 0:
            cell.set_text_props(fontweight="bold")
            cell.set_facecolor("0.92")
        if "?" in cell.get_text().get_text():
            cell.get_text().set_color(COLORS["accent"])
    if note:
        fig.text(0.005, 0.5 * LINE_HEIGHT_EM * font_in / fig.get_figheight(), note_lines,
                 ha="left", va="bottom", style="italic")
    save_figure(fig, csv_path.with_suffix(""), formats=("png",), mode=PROJECT_MODE)
    plt.close(fig)
    print(f"Wrote {csv_path.with_suffix('.png')}")


def main() -> None:
    apply_style(PROJECT_MODE)
    for csv_path in sorted(FOLDER.glob("[0-9][0-9]_*.csv")):
        render(csv_path)


if __name__ == "__main__":
    main()
