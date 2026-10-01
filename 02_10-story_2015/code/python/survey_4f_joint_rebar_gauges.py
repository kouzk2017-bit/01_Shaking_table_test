"""Survey every rebar strain gauge around the 4F interior joint (column 2-A).

The 2015 gauge layout drawing is missing, so each gauge's position is inferred
from its tag and its response.  Plan orientation (設置位置一覧 p.19): G1 lies
EAST of the interior column C2, so the interior joint 2-A is framed by the
G1 *west* end and the G2 *east* end; the G1 east end is at the corner column.

By analogy with the 2018 layout drawing (same plan; 別資料1-2), a beam-end
group has 5 gauges (2 top bars, 2 bottom bars, 1 side/web bar) about 50 mm
from the column face, and a column-end group 10 gauges (4 corner bars, 4
intermediate bars, 2 ties) about 80 mm from the beam face.  Whether 2015 used
the same scheme is an assumption that the responses below are meant to test.

Strain is baseline-corrected on the first 1000 samples of this case only
(earlier-case residuals are not added), averaged to 0.01 s and divided by
2000 με (εy = 0.002, as in the processed test figures).

Outputs: ``06_results/experiment/2015/<case>/rebar_gauges_4F_joint/``
  <group>.png         one panel per gauge, ε/εy against time (10-30 s)
  gauge_summary.csv   value at each large drift peak, extremes, residual,
                      correlation with the 4F story drift
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))

from publication_style import COLORS, apply_style, format_axis, reference_line_kwargs, save_figure, standard_size  # noqa: E402
from ten_story_pipeline import load_csv  # noqa: E402

CASE = "20151211-2(JMAKobe100%)"
RAW = WORKSPACE / "02_10-story_2015" / "data" / "raw" / "2015-1211" / "2015-1211-006-1"
DRIFT_CSV = WORKSPACE / "06_results" / "archive" / "2026-07-30_before_cleanup" / "2015" / "python" / CASE / "csv" / "story_drift_y.csv"
OUTPUT = WORKSPACE / "06_results" / "experiment" / "2015" / CASE / "rebar_gauges_4F_joint"
MODE = "presentation"
YIELD_MICROSTRAIN = 2000.0
TIME_WINDOW = (10.0, 30.0)
# Large 4F drift reversals of this case (loading_protocols reversal_points.csv).
DRIFT_PEAKS_S = (13.57, 14.02, 14.86, 15.68, 16.37, 17.31)

# group key -> (title, JB number, channel numbers)
GROUPS = {
    "G1_west_end_interior": ("4F G1 west end (interior joint 2-A, east side)", 5, range(1, 6)),
    "G2_east_end_interior": ("4F G2 east end (interior joint 2-A, west side)", 5, range(6, 11)),
    "G1_east_end_corner": ("4F G1 east end (corner column, for reference)", 4, range(43, 48)),
    "column_4F_2A": ("4F column 2-A (above the 4F joint)", 6, range(1, 15)),
    "column_3F_2A": ("3F column 2-A (below the 4F joint)", 4, range(11, 31)),
}


def raw_file(jb: int) -> Path:
    return RAW / f"2015-1211-006-1_ENG_001-{jb:02d}.csv"


def channel_names(jb: int) -> list[str]:
    with raw_file(jb).open("rb") as stream:
        stream.readline()
        return stream.readline().decode("shift_jis").strip().split(",")[1:]


def read_group(jb: int, channels: range) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    names = channel_names(jb)
    columns = [0, *channels]
    data = pd.read_csv(
        raw_file(jb), skiprows=3, header=None, usecols=columns, comment="%", encoding="shift_jis",
    ).apply(pd.to_numeric, errors="coerce").to_numpy(float)
    data = data[np.all(np.isfinite(data), axis=1)]
    usable = data.shape[0] // 10 * 10
    averaged = data[:usable].reshape(-1, 10, data.shape[1]).mean(axis=1)
    time = averaged[:, 0]
    series = {}
    for position, channel in enumerate(channels, start=1):
        values = averaged[:, position] - data[:1000, position].mean()
        tag = names[channel - 1].split("-", 1)[1]
        series[tag] = values / YIELD_MICROSTRAIN
    return time, series


def main() -> None:
    apply_style(MODE)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    headers, drift_data = load_csv(DRIFT_CSV)
    drift_time = drift_data[:, headers.index("Time_s")]
    drift = drift_data[:, headers.index("4F_rad")]

    rows = []
    for key, (title, jb, channels) in GROUPS.items():
        time, series = read_group(jb, channels)
        drift_on_time = np.interp(time, drift_time, drift)
        window = (time >= TIME_WINDOW[0]) & (time <= TIME_WINDOW[1])
        count = len(series)
        columns = 2 if count <= 6 else 4
        panel_rows = int(np.ceil(count / columns))
        fig, axes = plt.subplots(panel_rows, columns, sharex=True, figsize=standard_size(6.5 * columns / 2, 1.9 * panel_rows), squeeze=False)
        for ax, (tag, values) in zip(axes.flat, series.items()):
            ax.plot(time[window], values[window], color=COLORS["primary"])
            ax.axhline(0.0, **reference_line_kwargs())
            ax.set_title(tag)
            ax.set_xlim(TIME_WINDOW)
            rows.append({
                "group": key,
                "tag": tag,
                **{f"at_{t:.2f}s_drift_{np.interp(t, drift_time, drift):+.3f}": round(float(np.interp(t, time, values)), 2) for t in DRIFT_PEAKS_S},
                "max": round(float(values[window].max()), 2),
                "min": round(float(values[window].min()), 2),
                "residual_end": round(float(values[-100:].mean()), 2),
                "corr_with_drift_12_18s": round(float(np.corrcoef(values[(time >= 12) & (time <= 18)], drift_on_time[(time >= 12) & (time <= 18)])[0, 1]), 2),
            })
        for ax in list(axes.flat)[count:]:
            ax.set_visible(False)
        for ax in axes[-1]:
            format_axis(ax, xlabel="Time (s)", legend=False)
        for ax in axes[:, 0]:
            ax.set_ylabel(r"$\epsilon/\epsilon_y$")
        fig.suptitle(title)
        save_figure(fig, OUTPUT / key, formats=("png",), mode=MODE)
        plt.close(fig)

    with (OUTPUT / "gauge_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} gauges to {OUTPUT}")


if __name__ == "__main__":
    main()
