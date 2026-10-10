"""Schematic elevation of the member-end displacement transducers at joint 3 (4F floor, column 2-A).

Positions from 設置位置一覧 (documents/specimen_information/計測関係情報/03_【資料2】), p. 2-19/2-20,
including the red hand corrections on p. 2-20:
  beams (Y direction, G1 west end / G2 east end): gauge 1000 mm from the column face; lower wire at the
      beam-bottom centre, upper wire on the beam side 80 mm below the slab soffit (printed 50, corrected 80)
  columns: on the column side faces, 100 mm in from the east and west column edges (65 mm at 1F), so the
      lever arm for frame-direction bending is 500 - 2 x 100 = 300 mm at 3F/4F (user 2026-10-10);
      head (3C2T) from the beam bottom down 600 mm, foot (4C2B) from the floor up 600 mm (printed 250)
Section: column 500 x 500, beam 350 x 550 with slab 120 mm (user-confirmed). Test east = DIANA left.
Output: 06_results/experiment/2015/<case>/joints/overview/sensor_layout_joint3.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "08_common" / "python"))
from publication_style import PROJECT_MODE, COLORS, apply_style, figure_size, save_figure  # noqa: E402

OUTPUT = PROJECT / "06_results" / "experiment" / "2015" / "20151211-2(JMAKobe100%)" / "joints" / "overview"
COL, BEAM_H, SLAB, BEAM_L, COL_L = 500.0, 550.0, 120.0, 1500.0, 1100.0
UPPER_BELOW_SLAB, BEAM_GAUGE, COL_GAUGE, COL_INSET = 80.0, 1000.0, 600.0, 100.0


def main() -> None:
    apply_style(PROJECT_MODE)
    fig, ax = plt.subplots(figsize=(figure_size(PROJECT_MODE)[0], figure_size(PROJECT_MODE)[0] * 0.75))
    grey, edge = "0.88", "0.35"
    x0, x1 = -COL / 2, COL / 2                    # column faces: x < 0 is EAST (DIANA left)
    zb, zt = 0.0, BEAM_H                          # beam bottom / top of slab
    ax.add_patch(Rectangle((x0, -COL_L), COL, COL_L * 2 + BEAM_H, fc=grey, ec=edge))       # column
    ax.add_patch(Rectangle((-COL / 2 - BEAM_L, zb), BEAM_L * 2 + COL, BEAM_H, fc=grey, ec=edge))  # beams + joint
    ax.plot([-COL / 2 - BEAM_L, COL / 2 + BEAM_L], [zt - SLAB] * 2, color=edge, linestyle=":", linewidth=0.8)
    text = dict(fontsize=plt.rcParams["legend.fontsize"] * 0.8)

    def wire(x_a, x_b, z_a, z_b, color, label, ha="center", dz=0.0):
        ax.annotate("", xy=(x_b, z_b), xytext=(x_a, z_a),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))
        ax.plot(x_a, z_a, "o", color=color, markersize=4)
        ax.text((x_a + x_b) / 2, (z_a + z_b) / 2 + dz, label, color=color, ha=ha, va="center", **text)

    z_up = zt - SLAB - UPPER_BELOW_SLAB
    # beams: left = G1 west end (east of the column), right = G2 east end
    wire(x0 - BEAM_GAUGE, x0, z_up, z_up, COLORS["primary"], "G1WU (side, 80 below slab)", dz=55)
    wire(x0 - BEAM_GAUGE, x0, zb, zb, COLORS["primary"], "G1WL (soffit centre)", dz=-60)
    wire(x1 + BEAM_GAUGE, x1, z_up, z_up, COLORS["accent"], "G2EU", dz=55)
    wire(x1 + BEAM_GAUGE, x1, zb, zb, COLORS["accent"], "G2EL", dz=-60)
    # columns: east (left) and west (right) faces, 600 mm from the beam bottom / floor
    for x, side, ha, off in ((x0 + COL_INSET, "E", "right", -25), (x1 - COL_INSET, "W", "left", 25)):
        wire(x, x, zb - COL_GAUGE, zb, COLORS["green"], f"3C2T-{side}", ha=ha, dz=0)
        ax.texts[-1].set_x(x + off)
        wire(x, x, zt + COL_GAUGE, zt, COLORS["purple"], f"4C2B-{side}", ha=ha, dz=0)
        ax.texts[-1].set_x(x + off)

    def dim(xa, xb, z, label):
        ax.annotate("", xy=(xa, z), xytext=(xb, z), arrowprops=dict(arrowstyle="<->", color="0.4", lw=0.8))
        ax.text((xa + xb) / 2, z - 45, label, ha="center", va="top", color="0.3", **text)

    dim(x0 - BEAM_GAUGE, x0, -230, "1000")
    dim(x1, x1 + BEAM_GAUGE, -230, "1000")
    dim(x0, x1, -COL_L + 120, "500")
    dim(x0 + COL_INSET, x1 - COL_INSET, zt + COL_L - 120, "300")
    ax.annotate("", xy=(x1 + BEAM_L * 0.9, zb), xytext=(x1 + BEAM_L * 0.9, z_up),
                arrowprops=dict(arrowstyle="<->", color="0.4", lw=0.8))
    ax.text(x1 + BEAM_L * 0.9 + 30, (zb + z_up) / 2, f"{z_up:.0f}", va="center", color="0.3", **text)
    ax.text(x0 - BEAM_L * 0.55, zt + 40, "Slab 120", ha="center", va="bottom", color="0.3", **text)
    ax.text(x0 - BEAM_L, zt + 230, "EAST (DIANA left)\nG1 west end", ha="left", va="bottom", **text)
    ax.text(x1 + BEAM_L, zt + 230, "WEST (DIANA right)\nG2 east end", ha="right", va="bottom", **text)
    ax.text(x1 + 40, zt + COL_GAUGE / 2 + 160, "600", color="0.3", **text)
    ax.text(x1 + 40, zb - COL_GAUGE / 2 - 160, "600", color="0.3", **text)
    ax.text(0, -COL_L + 170, "column sensors 100 mm\nin from the edges", ha="center", va="bottom", color="0.3", **text)
    ax.set_xlim(-COL / 2 - BEAM_L - 50, COL / 2 + BEAM_L + 50)
    ax.set_ylim(-COL_L - 20, BEAM_H + COL_L + 20)
    ax.set_aspect("equal")
    ax.axis("off")
    save_figure(fig, OUTPUT / "sensor_layout_joint3", formats=("png",), mode=PROJECT_MODE)
    print(f"Wrote {OUTPUT / 'sensor_layout_joint3.png'}")


if __name__ == "__main__":
    main()
