"""Test data of the interior joints (column 2-A), 2015 JMA-Kobe 100 % (base fixed): one folder per joint.

Reads the processed CSVs only, through test_data.py (switches in
02_10-story_2015/config/test_data_options.json); no raw records are read here.

Joint n = the joint at the TOP of story n (Kang et al. EESD Fig. 13, Tsuji paper, joint_rotation.csv):

  joint 1  2F floor  JNT1   no rebar gauges
  joint 2  3F floor  JNT2   upper column foot 3F2AC-STR-01..10 only
  joint 3  4F floor  JNT3   beams 4G1A-W / 4G2A-E, upper column foot 4F2AC-01..10, lower column head 3F2AC-11..20
  joint 4  5F floor  JNT4   beams 5G11-W / 5G21-E, upper column foot 5F2AC-01/02/08/09, lower column head 4F2AC-11/12/18/19
  joint 5  6F floor  no JNT beams 6G11-W / 6G21-E, upper column foot 6F2AC, lower column head 5F2AC-11/12/18/19
  joint 6  7F floor  JNT6   no rebar gauges

Gauge positions (REBAR_GAUGES.md; DIANA left = test east): beam 01/02 bottom bar, 04/05 top bar (03 web);
G1 west end = left beam, G2 east end = right beam; column 01/02 east (left), 08/09 west (right) at the
foot, 11/12 east, 18/19 west at the head. Distance from the faces unknown. 6G11-STR-W05 is broken
(constant 52.66 eps_y) and excluded.

The joint angle and the diagonal strains use the gauge frame set in test_data_options.json (Kang
270 x 270 mm since 2026-10-08); the diagonal strains are unfiltered (the joint expansion is kept).
The story drift of joint n is that of story n; for the upper column the strain belongs to story n+1.

Outputs, 06_results/experiment/2015/<case>/joints/:
  joint_<n>_JNT<n>/ (joint_5_noJNT/)
    01_joint_angle_time_history.png
    02_joint_angle_and_story_drift_time_history.png
    03_joint_angle_vs_story_drift.png
    04_joint_diagonal_strain_time_history.png
    05_rebar_<nn>_<position>.png              one figure per position, both gauges
    07_drift_and_joint_angle_peaks_a-i.png    joints 3, 4: the first nine half-cycle peaks from 13 s as a-i
    08a/08b_rebar_<negative|positive>_drift_pair_peaks_a-i.png   joints 3, 4: beam + column stretched by the
                                              negative / positive drift (the model-comparison gauges), a-i lines
    10_story_shear_time_history_peaks_a-i.png joints 3, 4: story shear (whole story) with a-i
    11_story_shear_vs_drift_peaks_a-i.png     joints 3, 4: story shear vs story drift, a-i marked
    12_beam_end_elongation_peaks_a-i.png      joint 3: beam soffit elongation 0-1000 mm, left (G1WL) vs right (G2EL)
    13_column_end_opening_peaks_a-i.png       joint 3: column-end opening, upper foot (4C2B) / lower head (3C2T), E vs W
    14_beam_end_rotation_peaks_a-i.png        joint 3: beam-end rotation over 1000 mm, (L - U) / 350 mm, left vs right
    15_column_end_rotation_peaks_a-i.png      joint 3: column-end rotation over 600 mm, (E - W) / 300 mm
    09_joint_ratio_at_peaks_a-i.png           joints 3, 4: joint angle / story drift at the half-cycle peaks, a-i labelled
    peaks_a-i.csv                             time, drift and state at a-i (used for the video frames)
    timeseries.csv, peaks.csv                 100 Hz series; every half-cycle peak (|drift| >= 0.005)
  overview/
    01_max_rebar_strain.png, 02_joint_ratio_at_peaks.png, rebar_overview.csv
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "08_common" / "python"))
sys.path.insert(0, str(HERE))

import test_data  # noqa: E402
from publication_style import (  # noqa: E402
    PROJECT_MODE, REBAR_STRAIN_YLIM, ANGLE_YLIM, COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure,
)

CASE = test_data.DEFAULT_CASE
OUTPUT = PROJECT / "06_results" / "experiment" / "2015" / CASE / "joints"
TIME_WINDOW = (10.0, 30.0)
BROKEN = {"6G11-STR-W05"}
STRAIN_LABEL = r"Strain $\epsilon/\epsilon_y$"
# joint-3 member-end transducers (設置位置一覧 p.2-19/2-20, plot_joint3_sensor_layout.py; confirmed 2026-10-10):
# beam U wire 80 mm below the slab soffit, L wire at the soffit -> 550 - 120 - 80 = 350 mm apart, gauge 1000 mm;
# column wires 100 mm in from the E/W edges -> 500 - 2 x 100 = 300 mm apart, gauge 600 mm.
BEAM_SENSOR_SPACING_MM = 350.0
COLUMN_SENSOR_SPACING_MM = 300.0

# joint -> floor, JNT label in joint_rotation.csv (None = no JNT), gauge prefixes per member
JOINTS = {
    1: dict(floor="2F", jnt="1F"),
    2: dict(floor="3F", jnt="2F", upper="3F2AC-STR-"),
    3: dict(floor="4F", jnt="3F", left="4G1A-STR-W", right="4G2A-STR-E", upper="4F2AC-STR-", lower="3F2AC-STR-"),
    4: dict(floor="5F", jnt="4F", left="5G11-STR-W", right="5G21-STR-E", upper="5F2AC-STR-", lower="4F2AC-STR-"),
    5: dict(floor="6F", jnt=None, left="6G11-STR-W", right="6G21-STR-E", upper="6F2AC-STR-", lower="5F2AC-STR-"),
    6: dict(floor="7F", jnt="6F"),
}
# (file stem, title, member key, gauge numbers, story offset of the member: 0 = story n, 1 = story n+1)
POSITIONS = (
    ("left_beam_bottom", "Left beam (G1 west end) bottom bar", "left", ("01", "02"), 0),
    ("left_beam_top", "Left beam (G1 west end) top bar", "left", ("04", "05"), 0),
    ("right_beam_bottom", "Right beam (G2 east end) bottom bar", "right", ("01", "02"), 0),
    ("right_beam_top", "Right beam (G2 east end) top bar", "right", ("04", "05"), 0),
    ("upper_column_left", "Upper column foot, left (east) bar", "upper", ("01", "02"), 1),
    ("upper_column_right", "Upper column foot, right (west) bar", "upper", ("08", "09"), 1),
    ("lower_column_left", "Lower column head, left (east) bar", "lower", ("11", "12"), 0),
    ("lower_column_right", "Lower column head, right (west) bar", "lower", ("18", "19"), 0),
)
SHORT = {"left_beam_bottom": "Beam L\nbottom", "left_beam_top": "Beam L\ntop", "right_beam_bottom": "Beam R\nbottom",
         "right_beam_top": "Beam R\ntop", "upper_column_left": "Col. up\nleft", "upper_column_right": "Col. up\nright",
         "lower_column_left": "Col. low\nleft", "lower_column_right": "Col. low\nright"}
# Presentation set (joints 3, 4): the first nine half-cycle peaks from 13 s labelled a-i, and the
# gauges shown with them (left beam bottom, right beam bottom, upper column left [, right beam top]).
PEAK_LETTERS = "abcdefghi"
PEAK_START_S = 12.9
# The gauges compared with the DIANA joint models, as one beam + one column per loading direction
# (2026-10-09): negative drift stretches the left beam bottom and the upper-column right bar,
# positive drift the right beam bottom and the upper-column left bar.
PEAK_GAUGES = {
    4: {"negative": (("left_beam_bottom", "5G11-STR-W01"), ("upper_column_right", "5F2AC-STR-09")),
        "positive": (("right_beam_bottom", "5G21-STR-E01"), ("upper_column_left", "5F2AC-STR-02"))},
    3: {"negative": (("left_beam_bottom", "4G1A-STR-W02"), ("upper_column_right", "4F2AC-STR-09")),
        "positive": (("right_beam_bottom", "4G2A-STR-E01"), ("upper_column_left", "4F2AC-STR-02"))},
}
JOINT_COLORS = {1: COLORS["sky"], 2: COLORS["orange"], 3: COLORS["primary"], 4: COLORS["accent"],
                5: COLORS["green"], 6: COLORS["purple"]}


def folder(joint: int) -> Path:
    jnt = f"JNT{joint}" if JOINTS[joint]["jnt"] else "noJNT"
    return OUTPUT / f"joint_{joint}_{jnt}"


def gauges(joint: int, key: str, numbers) -> list[str]:
    prefix = JOINTS[joint].get(key)
    return [] if prefix is None else [prefix + n for n in numbers if prefix + n not in BROKEN]


def half_cycle_peaks(time: np.ndarray, drift: np.ndarray, threshold: float = 0.005) -> list[int]:
    """Index of the extreme drift in every half cycle (between zero crossings) that exceeds the threshold."""
    window = np.flatnonzero((time >= TIME_WINDOW[0]) & (time <= TIME_WINDOW[1]))
    cuts = np.flatnonzero(np.diff(np.sign(drift[window])) != 0) + 1
    peaks = [seg[np.argmax(np.abs(drift[seg]))] for seg in np.split(window, cuts) if seg.size]
    return [int(k) for k in peaks if abs(drift[k]) >= threshold]


def time_figure():
    return plt.subplots(figsize=figure_size(PROJECT_MODE))


def finish_time(fig, ax, path: Path, ylabel: str, below_letters: bool = False) -> None:
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel=ylabel, legend=not below_letters)
    if below_letters:  # keep the legend clear of the a-i letters along the top
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.9))
    save_figure(fig, path, formats=("png",), mode=PROJECT_MODE)


def joint_frame(joint: int) -> pd.DataFrame:
    spec = JOINTS[joint]
    time, drift = test_data.story("story_drift_y", joint, CASE)
    _, shear = test_data.story("story_shear_y", joint, CASE)
    frame = pd.DataFrame({"Time_s": time, "story_drift_rad": drift, "story_shear_kN": shear})
    if spec["jnt"]:
        t_angle, angle = test_data.joint_angle(spec["jnt"], CASE)
        t_diag, d1, d2 = test_data.joint_diagonal_strain(spec["jnt"], CASE)
        frame["joint_angle_rad"] = np.interp(time, t_angle, angle)
        frame["diag1_strain"] = np.interp(time, t_diag, d1)
        frame["diag2_strain"] = np.interp(time, t_diag, d2)
    for _, _, key, numbers, _ in POSITIONS:
        tags = gauges(joint, key, numbers)
        if tags:
            t_bar, series = test_data.rebar_gauges(tags, CASE)
            for tag, values in series.items():
                frame[tag] = np.interp(time, t_bar, values, left=np.nan, right=np.nan)  # CSV covers 10-30 s
    if joint == 2:  # the other upper-column-foot gauges (positions not confirmed)
        t_bar, series = test_data.rebar_gauges([f"3F2AC-STR-{n:02d}" for n in (3, 4, 5, 6, 7, 10)], CASE)
        for tag, values in series.items():
            frame[tag] = np.interp(time, t_bar, values, left=np.nan, right=np.nan)
    return frame


def plot_joint(joint: int, frame: pd.DataFrame) -> None:
    out = folder(joint)
    window = (frame["Time_s"] >= TIME_WINDOW[0]) & (frame["Time_s"] <= TIME_WINDOW[1])
    f = frame[window]
    story = f"Story {joint} drift"
    if "joint_angle_rad" in f:
        fig, ax = time_figure()
        ax.plot(f["Time_s"], f["joint_angle_rad"], color=COLORS["accent"], label=f"Joint deformation angle (JNT{joint})")
        finish_time(fig, ax, out / "01_joint_angle_time_history", "Joint deformation angle (rad)")

        fig, ax = time_figure()
        ax.plot(f["Time_s"], f["story_drift_rad"], color=COLORS["primary"], label=story)
        ax.plot(f["Time_s"], f["joint_angle_rad"], color=COLORS["accent"], label="Joint deformation angle")
        finish_time(fig, ax, out / "02_joint_angle_and_story_drift_time_history", "Angle (rad)")

        fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
        ax.plot(f["story_drift_rad"], f["joint_angle_rad"], color=COLORS["accent"])
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
        format_axis(ax, xlabel=f"{story} (rad)", ylabel="Joint deformation angle (rad)")
        save_figure(fig, out / "03_joint_angle_vs_story_drift", formats=("png",), mode=PROJECT_MODE)

        fig, ax = time_figure()
        ax.plot(f["Time_s"], f["diag1_strain"], color=COLORS["primary"], label="Diagonal DY-1")
        ax.plot(f["Time_s"], f["diag2_strain"], color=COLORS["accent"], label="Diagonal DY-2")
        finish_time(fig, ax, out / "04_joint_diagonal_strain_time_history", r"Diagonal strain $\Delta L/L$")

    for index, (stem, title, key, numbers, _) in enumerate(POSITIONS, start=1):
        tags = [t for t in gauges(joint, key, numbers) if t in f]
        if not tags:
            continue
        fig, ax = time_figure()
        for i, tag in enumerate(tags):
            ax.plot(f["Time_s"], f[tag], color=f"C{i}", label=tag)
        ax.axhline(1.0, **reference_line_kwargs(linestyle="--"), zorder=0)
        finish_time(fig, ax, out / f"05_rebar_{index:02d}_{stem}",
                    SHORT[stem].replace("\n", " ") + r" bar $\epsilon/\epsilon_y$")



def lettered_peaks(joint: int, frame: pd.DataFrame) -> pd.DataFrame:
    peaks = peaks_table(joint, frame)
    peaks = peaks[peaks["time_s"] >= PEAK_START_S].head(len(PEAK_LETTERS)).copy()
    peaks.insert(0, "peak", list(PEAK_LETTERS[: len(peaks)]))
    return peaks


def mark_peaks(ax, peaks: pd.DataFrame, values=None) -> None:
    """Letters a-i at the peaks: on the curve if values are given, else as vertical lines labelled at the top."""
    for _, row in peaks.iterrows():
        if values is not None:
            y = values(row["time_s"])
            ax.plot(row["time_s"], y, "o", color=COLORS["black"], markersize=plt.rcParams["lines.markersize"] * 0.8)
            ax.annotate(row["peak"], (row["time_s"], y), textcoords="offset points",
                        xytext=(0, 7 if y >= 0 else -7), ha="center", va="bottom" if y >= 0 else "top",
                        fontsize=plt.rcParams["legend.fontsize"])
        else:
            ax.axvline(row["time_s"], **reference_line_kwargs(linestyle=":"), zorder=0)
            ax.text(row["time_s"], 0.98, row["peak"], transform=ax.get_xaxis_transform(), ha="center", va="top",
                    fontsize=plt.rcParams["legend.fontsize"])


def plot_lettered(joint: int, frame: pd.DataFrame) -> None:
    """07: story drift + joint angle with peaks a-i; 08: the selected gauges with the same peak lines."""
    out = folder(joint)
    peaks = lettered_peaks(joint, frame)
    peaks.round(4).to_csv(out / "peaks_a-i.csv", index=False)
    window = (frame["Time_s"] >= TIME_WINDOW[0]) & (frame["Time_s"] <= TIME_WINDOW[1])
    f = frame[window]
    fig, ax = time_figure()
    ax.plot(f["Time_s"], f["story_drift_rad"], color=COLORS["primary"], label=f"Story {joint} drift")
    ax.plot(f["Time_s"], f["joint_angle_rad"], color=COLORS["accent"], label="Joint deformation angle")
    low, high = ax.get_ylim()
    ax.set_ylim(low - 0.1 * (high - low), high + 0.1 * (high - low))  # room for the letters
    mark_peaks(ax, peaks, lambda t: np.interp(t, frame["Time_s"], frame["story_drift_rad"]))
    finish_time(fig, ax, out / "07_drift_and_joint_angle_peaks_a-i", "Angle (rad)")
    # 09: joint angle / story drift at every half-cycle peak, a-i labelled
    every = peaks_table(joint, frame)
    every = every[every["time_s"] >= PEAK_START_S]
    fig, ax = time_figure()
    ax.plot(every["time_s"], every["joint_ratio"], marker="o", color=COLORS["accent"],
            label=f"Joint {joint}: joint angle / story {joint} drift")
    low, high = ax.get_ylim()
    ax.set_ylim(0.0, high + 0.12 * (high - low))
    for _, row in peaks.iterrows():
        ax.annotate(row["peak"], (row["time_s"], row["joint_ratio"]), textcoords="offset points",
                    xytext=(0, 7), ha="center", va="bottom", fontsize=plt.rcParams["legend.fontsize"])
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel="Joint angle / story drift", legend=True)
    save_figure(fig, out / "09_joint_ratio_at_peaks_a-i", formats=("png",), mode=PROJECT_MODE)
    # 10/11: story shear (whole story n, inertia forces from the floor accelerations) with a-i
    fig, ax = time_figure()
    ax.plot(f["Time_s"], f["story_shear_kN"], color=COLORS["primary"], label=f"Story {joint} shear (whole story)")
    low, high = ax.get_ylim()
    ax.set_ylim(low - 0.1 * (high - low), high + 0.1 * (high - low))
    mark_peaks(ax, peaks, lambda t: np.interp(t, frame["Time_s"], frame["story_shear_kN"]))
    finish_time(fig, ax, out / "10_story_shear_time_history_peaks_a-i", "Story shear (kN)")
    fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
    ax.plot(f["story_drift_rad"], f["story_shear_kN"], color=COLORS["primary"], linewidth=plt.rcParams["lines.linewidth"] * 0.7)
    for _, row in peaks.iterrows():
        x = row["story_drift_rad"]
        y = float(np.interp(row["time_s"], frame["Time_s"], frame["story_shear_kN"]))
        ax.plot(x, y, "o", color=COLORS["black"], markersize=plt.rcParams["lines.markersize"] * 0.8)
        ax.annotate(row["peak"], (x, y), textcoords="offset points", xytext=(6 if x >= 0 else -6, 0),
                    ha="left" if x >= 0 else "right", va="center", fontsize=plt.rcParams["legend.fontsize"])
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel=f"Story {joint} drift (rad)", ylabel=f"Story {joint} shear (kN)")
    save_figure(fig, out / "11_story_shear_vs_drift_peaks_a-i", formats=("png",), mode=PROJECT_MODE)
    # 12/13 (joint 3 only, the joint with member-end displacement transducers, JB12): beam-end
    # elongation over 1000 mm from the column face at the soffit, column-end opening (mean of the two
    # transducers on one face), and the beam-end / column-end rotations from the sensor spacings above.
    if joint == 3:
        names = ["G1WL-DY-1", "G2EL-DY-1", "3C2T-DZ-SW", "3C2T-DZ-NW", "3C2T-DZ-NE", "3C2T-DZ-SE",
                 "4C2B-DZ-SW", "4C2B-DZ-NW", "4C2B-DZ-NE", "4C2B-DZ-SE"]
        t_m, mem = test_data.member_end_displacement(names, CASE)
        keep = (t_m >= TIME_WINDOW[0]) & (t_m <= TIME_WINDOW[1])
        fig, ax = time_figure()
        ax.plot(t_m[keep], mem["G1WL-DY-1"][keep], color=COLORS["primary"], label="Left beam bottom (G1 west end)")
        ax.plot(t_m[keep], mem["G2EL-DY-1"][keep], color=COLORS["accent"], label="Right beam bottom (G2 east end)")
        low, high = ax.get_ylim(); ax.set_ylim(low, high + 0.15 * (high - low))
        mark_peaks(ax, peaks)
        finish_time(fig, ax, out / "12_beam_end_elongation_peaks_a-i", "Beam-end elongation (mm)", below_letters=True)
        fig, ax = time_figure()
        for label, (a1, a2), color, style in (
                ("Upper column foot, east (left)", ("4C2B-DZ-NE", "4C2B-DZ-SE"), COLORS["primary"], "-"),
                ("Upper column foot, west (right)", ("4C2B-DZ-NW", "4C2B-DZ-SW"), COLORS["accent"], "-"),
                ("Lower column head, east (left)", ("3C2T-DZ-NE", "3C2T-DZ-SE"), COLORS["primary"], "--"),
                ("Lower column head, west (right)", ("3C2T-DZ-NW", "3C2T-DZ-SW"), COLORS["accent"], "--")):
            ax.plot(t_m[keep], ((mem[a1] + mem[a2]) / 2)[keep], color=color, linestyle=style, label=label)
        low, high = ax.get_ylim(); ax.set_ylim(low, high + 0.15 * (high - low))
        mark_peaks(ax, peaks)
        finish_time(fig, ax, out / "13_column_end_opening_peaks_a-i", "Column-end opening (mm)", below_letters=True)
        # 14/15: rotations; beam positive = soffit opens, column positive = east (DIANA left) face opens.
        upper_names = ["G1WU-DY-1", "G2EU-DY-1"]
        mem.update(test_data.member_end_displacement(upper_names, CASE)[1])
        fig, ax = time_figure()
        for label, (low_name, up_name), color in (
                ("Left beam (G1 west end)", ("G1WL-DY-1", "G1WU-DY-1"), COLORS["primary"]),
                ("Right beam (G2 east end)", ("G2EL-DY-1", "G2EU-DY-1"), COLORS["accent"])):
            ax.plot(t_m[keep], ((mem[low_name] - mem[up_name]) / BEAM_SENSOR_SPACING_MM)[keep], color=color, label=label)
        ax.set_ylim(ANGLE_YLIM)
        mark_peaks(ax, peaks)
        finish_time(fig, ax, out / "14_beam_end_rotation_peaks_a-i", "Beam-end rotation (rad)", below_letters=True)
        fig, ax = time_figure()
        for label, prefix, color in (("Upper column foot (4C2B)", "4C2B", COLORS["primary"]),
                                     ("Lower column head (3C2T)", "3C2T", COLORS["accent"])):
            east = (mem[f"{prefix}-DZ-NE"] + mem[f"{prefix}-DZ-SE"]) / 2
            west = (mem[f"{prefix}-DZ-NW"] + mem[f"{prefix}-DZ-SW"]) / 2
            ax.plot(t_m[keep], ((east - west) / COLUMN_SENSOR_SPACING_MM)[keep], color=color, label=label)
        ax.set_ylim(-0.05, 0.05)  # exceeds ANGLE_YLIM (peak 0.047 at b)
        mark_peaks(ax, peaks)
        finish_time(fig, ax, out / "15_column_end_rotation_peaks_a-i", "Column-end rotation (rad)", below_letters=True)
    # 08: the gauges compared with the models, one figure per loading direction (beam + column)
    for suffix, (direction, pair) in zip("ab", PEAK_GAUGES[joint].items()):
        fig, ax = time_figure()
        for color, (stem, tag) in zip((COLORS["primary"], COLORS["accent"]), pair):
            ax.plot(f["Time_s"], f[tag], color=color, label=SHORT[stem].replace(chr(10), " "))  # gauge: PEAK_GAUGES
        ax.axhline(1.0, **reference_line_kwargs(linestyle="--"), zorder=0)
        ax.set_ylim(REBAR_STRAIN_YLIM)
        mark_peaks(ax, peaks)
        finish_time(fig, ax, out / f"08{suffix}_rebar_{direction}_drift_pair_peaks_a-i", STRAIN_LABEL,
                    below_letters=True)

def peaks_table(joint: int, frame: pd.DataFrame) -> pd.DataFrame:
    time, drift = frame["Time_s"].to_numpy(), frame["story_drift_rad"].to_numpy()
    vmax = frame.loc[(time >= TIME_WINDOW[0]) & (time <= TIME_WINDOW[1]), "story_shear_kN"].abs().max()
    rows = []
    for k in half_cycle_peaks(time, drift):
        row = {"time_s": time[k], "story_drift_rad": drift[k], "V_over_Vmax": frame.at[k, "story_shear_kN"] / vmax}
        if "joint_angle_rad" in frame:
            row.update(joint_angle_rad=frame.at[k, "joint_angle_rad"],
                       joint_ratio=frame.at[k, "joint_angle_rad"] / drift[k],
                       diag1_strain=frame.at[k, "diag1_strain"], diag2_strain=frame.at[k, "diag2_strain"])
        for stem, _, key, numbers, _ in POSITIONS:
            tags = [t for t in gauges(joint, key, numbers) if t in frame]
            if tags:
                row[f"{stem}_max_so_far"] = frame.loc[:k, tags].max().max()
        rows.append(row)
    return pd.DataFrame(rows)


def rebar_rows(joint: int, frame: pd.DataFrame) -> list[dict]:
    rows = []
    for stem, _, key, numbers, offset in POSITIONS:
        t_drift, drift = test_data.story("story_drift_y", joint + offset, CASE)
        for tag in [t for t in gauges(joint, key, numbers) if t in frame]:
            valid = frame[["Time_s", tag]].dropna()
            hit = valid[tag].to_numpy() >= 1.0
            first = float(valid["Time_s"].to_numpy()[np.argmax(hit)]) if hit.any() else np.nan
            rows.append(dict(joint=joint, position=stem, gauge=tag, max_eps_over_epsy=valid[tag].max(),
                             end_eps_over_epsy=valid[tag].iloc[-1], first_tension_yield_s=first,
                             drift_story=joint + offset,
                             drift_at_first_yield_rad=np.interp(first, t_drift, drift) if hit.any() else np.nan))
    return rows


def plot_overview(table: pd.DataFrame, frames: dict[int, pd.DataFrame]) -> None:
    out = OUTPUT / "overview"
    stems = [p[0] for p in POSITIONS]
    joints = sorted(table["joint"].unique())
    fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
    width = 0.8 / len(joints)
    for k, joint in enumerate(joints):
        per = table[table.joint == joint].groupby("position")["max_eps_over_epsy"].max().reindex(stems)
        ax.bar(np.arange(len(stems)) + (k - (len(joints) - 1) / 2) * width, per.to_numpy(), width,
               color=JOINT_COLORS[joint], label=f"Joint {joint} ({JOINTS[joint]['floor']} floor)")
    ax.axhline(1.0, **reference_line_kwargs(linestyle="--"))
    ax.set_xticks(np.arange(len(stems)), [SHORT[s] for s in stems])
    ax.tick_params(axis="x", labelsize=plt.rcParams["legend.fontsize"])
    format_axis(ax, ylabel=r"Max strain $\epsilon/\epsilon_y$", legend=True, grid_axis="y")
    save_figure(fig, out / "01_max_rebar_strain", formats=("png",), mode=PROJECT_MODE)

    fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
    for joint, frame in frames.items():
        if "joint_angle_rad" not in frame:
            continue
        peaks = peaks_table(joint, frame)
        ax.plot(peaks["time_s"], peaks["joint_ratio"], marker="o", color=JOINT_COLORS[joint],
                label=f"Joint {joint} (JNT{joint})")
    ax.set_xlim(TIME_WINDOW)
    format_axis(ax, xlabel="Time (s)", ylabel="Joint angle / story drift at peaks", legend=True)
    save_figure(fig, out / "02_joint_ratio_at_peaks", formats=("png",), mode=PROJECT_MODE)


def main() -> None:
    apply_style(PROJECT_MODE)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # Generated content: clear the old flat files and per-joint folders (README.md is kept).
    for child in OUTPUT.iterdir():
        if child.name != "README.md":
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    frames, rows = {}, []
    for joint in JOINTS:
        frame = joint_frame(joint)
        frames[joint] = frame
        out = folder(joint)
        out.mkdir(parents=True, exist_ok=True)
        frame.to_csv(out / "timeseries.csv", index=False, float_format="%.6g")
        peaks_table(joint, frame).round(4).to_csv(out / "peaks.csv", index=False)
        plot_joint(joint, frame)
        if joint in PEAK_GAUGES:
            plot_lettered(joint, frame)
        rows.extend(rebar_rows(joint, frame))
        print(f"joint {joint}: {len(list(out.glob('*.png')))} figures -> {out.name}")
    table = pd.DataFrame(rows)
    (OUTPUT / "overview").mkdir(exist_ok=True)
    table.round(4).to_csv(OUTPUT / "overview" / "rebar_overview.csv", index=False)
    plot_overview(table, frames)


if __name__ == "__main__":
    main()
