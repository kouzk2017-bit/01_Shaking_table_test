"""Test data of the interior joints with joint-deformation transducers, 2015 JMA-Kobe 100% (base fixed).

Joints are named by story: joint n is the joint at the TOP of story n (the convention of
Kang et al. EESD Fig. 13, the Tsuji paper and the pipeline's joint_rotation.csv):

  joint 3 = JNT3 (JB11 ch5/6), 4F floor;  joint 4 = JNT4 (ch7/8), 5F floor;  joint 6 = JNT6 (ch9/10), 7F floor.

All on the interior column 2-A of the frame-direction elevation (設置位置一覧 p.16; there is no JNT
at the 6F floor). Rebar gauges exist at joints 3 and 4 only (the gauges labelled "6F" in Kang Fig.16
are at the 6F-floor joint, which has no JNT; joint 6 has none):

  joint 3: lower column head 3F2AC-STR-11..20 (JB04 ch21-30), upper column foot 4F2AC-STR-01..10 (JB06 ch1-10),
           beams 4G1A-STR-W01..05 (JB05 ch1-5) and 4G2A-STR-E01..05 (JB05 ch6-10)
  joint 4: lower column head 4F2AC-STR-11/12/18/19 (JB06 ch11-14), upper column foot 5F2AC-STR-01/02/08/09
           (JB16 ch1-4), beams 5G11-STR-W01..05 (JB06 ch15-19) and 5G21-STR-E01..05 (JB06 ch20-24)

Gauge positions (REBAR_GAUGES.md): beam 01/02 bottom bar, 03 web, 04/05 top bar; G1 west end is at the
column's east face (DIANA left beam), G2 east end at its west face (DIANA right). Column 01/02 east face
(DIANA left), 08/09 west face (DIANA right); head 11/12 east, 18/19 west. Distance from the faces unknown.
Strains are read as in survey_4f_joint_rebar_gauges.read_group (10-sample mean = 100 Hz, offset of the
first 1000 samples removed, divided by 2000 micro) and interpolated onto the drift time axis.

Joint deformation (transducers M-11-40S; anchors 107 mm from the column faces, 50 mm below the floor top,
80 mm above the beam bottom; 500 mm column, 550 mm beam -> a = 286, b = 420 mm, diagonal 508.1 mm):
  joint_angle_kang_rad   = 0.002619 * (d1 - d2), the pipeline / Kang Fig.13 coefficient (270 x 270 square),
                           band-passed 0.05-100 Hz exactly as joint_rotation.csv (checked here)
  joint_angle_anchor_rad = L/(2ab) * (d1 - d2) with the anchor rectangle (0.81 x the above), same filter
  diag1_strain, diag2_strain = d1/L, d2/L WITHOUT the 0.05 Hz high-pass (keeps the slow joint expansion)
Story drift / shear are those of story n (story_drift_y.csv, story_shear_y.csv, frame direction).

Outputs (06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/):
  joint_<n>_timeseries.csv, joint_<n>_peaks.csv (every half-cycle peak of story-n drift with |drift| >= 0.005),
  joint_<n>_01_drift_and_joint_angle.png, _02_diagonal_strain.png, then one figure per beam end / column end
  (03 G1 west end, 04 G2 east end, 05 lower column head, 06 upper column foot) with only the gauges whose
  position is known (beam 01/02 bottom, 04/05 top; column 01/02 & 11/12 east, 08/09 & 18/19 west).
  Every gauge is in the time-series CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "08_common" / "python"))
sys.path.insert(0, str(HERE))

from legacy_signal import fft_filter, resample_decimate  # noqa: E402
from publication_style import COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure  # noqa: E402
from survey_4f_joint_rebar_gauges import read_group  # noqa: E402
from ten_story_pipeline import DT, OUTPUT_DT, _time, read_channels  # noqa: E402
from workflow_config import CASES, SPEC  # noqa: E402

CASE = "20151211-2(JMAKobe100%)"
CSV = PROJECT / "06_results" / "experiment" / "2015" / CASE / "csv"
OUTPUT = PROJECT / "06_results" / "experiment" / "2015" / CASE / "joints"
A_MM, B_MM = 500.0 - 2 * 107.0, 550.0 - 50.0 - 80.0
DIAGONAL_MM = float(np.hypot(A_MM, B_MM))
KANG = np.sqrt(270.0**2 + 270.0**2) / (2 * 270.0 * 270.0)
ANCHOR = DIAGONAL_MM / (2 * A_MM * B_MM)
TIME_WINDOW = (10.0, 30.0)
_BEAM = {"01": "bottom", "02": "bottom", "04": "top", "05": "top"}
POSITION = {"beam_G1_west_end": _BEAM, "beam_G2_east_end": _BEAM,
            "lower_column_head": {"11": "east", "12": "east", "18": "west", "19": "west"},
            "upper_column_foot": {"01": "east", "02": "east", "08": "west", "09": "west"}}

# joint -> JNT channels, pipeline joint_rotation column, gauge groups {label: (JB, channels)}
JOINTS = {
    3: dict(jnt=(5, 6), rotation="3F_rad", gauges={
        "beam_G1_west_end": (5, range(1, 6)), "beam_G2_east_end": (5, range(6, 11)),
        "upper_column_foot": (6, range(1, 11)), "lower_column_head": (4, range(21, 31))}),
    4: dict(jnt=(7, 8), rotation="4F_rad", gauges={
        "beam_G1_west_end": (6, range(15, 20)), "beam_G2_east_end": (6, range(20, 25)),
        "upper_column_foot": (16, range(1, 5)), "lower_column_head": (6, range(11, 15))}),
    6: dict(jnt=(9, 10), rotation="6F_rad", gauges={}),
}


def jnt_signals(channels: tuple[int, int]) -> pd.DataFrame:
    case = next(c for c in CASES if c.name == CASE)
    raw = read_channels(SPEC, case, 11, range(channels[0], channels[1] + 1))
    filtered = resample_decimate(fft_filter(raw, 1 / DT, (0.05, 100.0), "fft_BPF"), DT, OUTPUT_DT)
    unfiltered = resample_decimate(raw - raw[:1000].mean(axis=0), DT, OUTPUT_DT)
    difference = filtered[:, 0] - filtered[:, 1]
    return pd.DataFrame({
        "Time_s": _time(filtered.shape[0]),
        "joint_angle_kang_rad": KANG * difference,
        "joint_angle_anchor_rad": ANCHOR * difference,
        "diag1_strain": unfiltered[:, 0] / DIAGONAL_MM,
        "diag2_strain": unfiltered[:, 1] / DIAGONAL_MM,
    })


def half_cycle_peaks(time: np.ndarray, drift: np.ndarray, threshold: float = 0.005) -> list[int]:
    """Index of the extreme drift in every half cycle (between zero crossings) that exceeds the threshold."""
    window = np.flatnonzero((time >= TIME_WINDOW[0]) & (time <= TIME_WINDOW[1]))
    sign = np.sign(drift[window])
    cuts = np.flatnonzero(np.diff(sign) != 0) + 1
    peaks = []
    for segment in np.split(window, cuts):
        if segment.size:
            k = segment[np.argmax(np.abs(drift[segment]))]
            if abs(drift[k]) >= threshold:
                peaks.append(int(k))
    return peaks


def process_joint(number: int, spec: dict) -> None:
    drift = pd.read_csv(CSV / "story_drift_y.csv")[["Time_s", f"{number}F_rad"]]
    shear = pd.read_csv(CSV / "story_shear_y.csv")
    frame = drift.rename(columns={f"{number}F_rad": "story_drift_rad"})
    frame["story_shear_kN"] = np.interp(frame["Time_s"], shear["Time_s"], shear[f"{number}F_kN"])
    jnt = jnt_signals(spec["jnt"])
    for column in jnt.columns[1:]:
        frame[column] = np.interp(frame["Time_s"], jnt["Time_s"], jnt[column])

    rotation = pd.read_csv(CSV / "joint_rotation.csv")[spec["rotation"]].to_numpy()
    n = min(rotation.size, jnt.shape[0])
    if not np.allclose(jnt["joint_angle_kang_rad"].to_numpy()[:n], rotation[:n], atol=1e-7):
        raise ValueError(f"joint {number}: JNT channels do not reproduce joint_rotation.csv {spec['rotation']}")

    groups = {}
    for label, (jb, channels) in spec["gauges"].items():
        t, gauges = read_group(jb, channels)
        groups[label] = list(gauges)
        for tag, values in gauges.items():
            frame[tag] = np.interp(frame["Time_s"], t, values)
    frame.to_csv(OUTPUT / f"joint_{number}_timeseries.csv", index=False, float_format="%.6g")

    time, story = frame["Time_s"].to_numpy(), frame["story_drift_rad"].to_numpy()
    vmax = frame.loc[(time >= TIME_WINDOW[0]) & (time <= TIME_WINDOW[1]), "story_shear_kN"].abs().max()
    rows = []
    for k in half_cycle_peaks(time, story):
        row = {"time_s": time[k], "story_drift_rad": story[k], "V_over_Vmax": frame.at[k, "story_shear_kN"] / vmax,
               "joint_ratio_kang": frame.at[k, "joint_angle_kang_rad"] / story[k],
               "joint_ratio_anchor": frame.at[k, "joint_angle_anchor_rad"] / story[k],
               "diag1_strain": frame.at[k, "diag1_strain"], "diag2_strain": frame.at[k, "diag2_strain"]}
        for label, tags in groups.items():
            row[f"{label}_max_so_far"] = frame.loc[:k, tags].max().max()
        rows.append(row)
    pd.DataFrame(rows).round(4).to_csv(OUTPUT / f"joint_{number}_peaks.csv", index=False)
    plot_joint(number, frame, groups)
    print(f"joint {number}: {len(rows)} half-cycle peaks, gauges: {sum(len(v) for v in groups.values())}")


def time_axes(frame: pd.DataFrame):
    fig, ax = plt.subplots(figsize=figure_size(mode="paper"))
    mask = (frame["Time_s"] >= TIME_WINDOW[0]) & (frame["Time_s"] <= TIME_WINDOW[1])
    return fig, ax, frame[mask]


def finish(fig, ax, path: Path, ylabel: str) -> None:
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel=ylabel, legend=True, legend_location="best")
    save_figure(fig, path, formats=("png",), mode="paper")
    plt.close(fig)


def plot_joint(number: int, frame: pd.DataFrame, groups: dict[str, list[str]]) -> None:
    stem = OUTPUT / f"joint_{number}"
    fig, ax, f = time_axes(frame)
    ax.plot(f["Time_s"], f["story_drift_rad"], color=COLORS["primary"], label=f"Story {number} drift")
    ax.plot(f["Time_s"], f["joint_angle_kang_rad"], color=COLORS["accent"], label="Joint angle (Kang coefficient)")
    ax.plot(f["Time_s"], f["joint_angle_anchor_rad"], color=COLORS["green"], label="Joint angle (anchor geometry)")
    finish(fig, ax, Path(f"{stem}_01_drift_and_joint_angle"), "Angle (rad)")
    fig, ax, f = time_axes(frame)
    ax.plot(f["Time_s"], f["diag1_strain"], color=COLORS["primary"], label="Diagonal DY-1")
    ax.plot(f["Time_s"], f["diag2_strain"], color=COLORS["accent"], label="Diagonal DY-2")
    finish(fig, ax, Path(f"{stem}_02_diagonal_strain"), "Diagonal strain, $\\Delta L/L$")
    for suffix, key, numbers in (("03_beam_G1_west_end", "beam_G1_west_end", ("01", "02", "04", "05")),
                                 ("04_beam_G2_east_end", "beam_G2_east_end", ("01", "02", "04", "05")),
                                 ("05_lower_column_head", "lower_column_head", ("11", "12", "18", "19")),
                                 ("06_upper_column_foot", "upper_column_foot", ("01", "02", "08", "09"))):
        tags = [t for t in groups.get(key, []) if t[-2:] in numbers]
        if not tags:
            continue
        fig, ax, f = time_axes(frame)
        for i, tag in enumerate(tags):
            ax.plot(f["Time_s"], f[tag], color=f"C{i}", label=f"{tag} ({POSITION[key][tag[-2:]]})")
        finish(fig, ax, Path(f"{stem}_{suffix}"), r"Strain, $\epsilon/\epsilon_{\mathrm{y}}$")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    apply_style("paper")
    for number, spec in JOINTS.items():
        process_joint(number, spec)


if __name__ == "__main__":
    main()
