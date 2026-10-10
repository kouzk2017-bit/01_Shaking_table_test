"""Frames of the joint videos (2015 JMA-Kobe 100 %) at the key moments of the test, synchronised with the data.

Videos (E-Defense, in 06_results/experiment/2015/<case>/): 21_3階 / 22_4階 (timecode burnt in) and
T-09_5階 (no timecode) 柱梁接合部 = joints 3 / 4 / 5 (the joint at the top of story 3 / 4 / 5; the column
below carries the label 3D2C-S / 4D2C-S / 5D2C-S).

Synchronisation: video_time = test_time + lag. The lag is found by cross-correlating the frame-to-frame
image change with |d(story drift)/dt| of the same story (story_drift_y.csv via test_data.py), 0-30 s
lags, 20 fps. Result 2026-10-09: 14.85 s (3階, 4階, r 0.76/0.82; test t = 0 at timecode 14:00:28.8,
the log says 14:00:28) and 14.25 s (5階, r 0.87).

Outputs (06_results/experiment/2015/<case>/joint_videos/):
  sync.csv                               lag and correlation per video
  joint_<n>/frame_<tt.tt>s.jpg           full-resolution frames
  joint_<n>_key_frames.png               3 x 3 sheet with time and story drift
  comparison_joints_3_4_5.png            rows = joints, columns = before / after the big cycles / end
  joint_<n>/peak_<a-i>.png               joints 3, 4: frame at each lettered peak (joints/joint_<n>_JNT<n>/peaks_a-i.csv,
                                         written by process_joint_data.py), captioned with time and story drift
  joint_<n>_peaks_a-i.png                the nine peak frames as a 3 x 3 sheet
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "08_common" / "python"))
sys.path.insert(0, str(HERE))

import test_data  # noqa: E402
from publication_style import PROJECT_MODE, apply_style, figure_size, save_figure  # noqa: E402

CASE = test_data.DEFAULT_CASE
CASE_DIR = PROJECT / "06_results" / "experiment" / "2015" / CASE
OUTPUT = CASE_DIR / "joint_videos"
VIDEOS = {3: "21_3階_柱梁接合部.wmv", 4: "22_4階_柱梁接合部.wmv", 5: "2015-1211-006-1_T-09_5階_柱梁接合部.mp4"}
FPS = 20
# before; the big reversals of the 4F record (A, +0.028, B, +0.030, -0.030, +0.030, D); end of shaking
KEY_TIMES = (10.0, 13.03, 13.57, 14.02, 14.86, 15.68, 16.37, 17.31, 45.0)
COMPARISON_TIMES = (10.0, 13.57, 15.68, 45.0)


def ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def motion(video: Path) -> tuple[np.ndarray, np.ndarray]:
    raw = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(video),
                          "-vf", f"fps={FPS},scale=160:90,format=gray", "-f", "rawvideo", "-"],
                         check=True, capture_output=True).stdout
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 90, 160).astype(float)
    change = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    return np.arange(1, len(frames)) / FPS, change


def find_lag(joint: int, video: Path) -> tuple[float, float]:
    t_video, change = motion(video)
    t, drift = test_data.story("story_drift_y", joint, CASE)
    grid = np.arange(0.0, 60.0, 1 / FPS)
    speed = np.abs(np.gradient(np.interp(grid, t, drift), 1 / FPS))
    best = (0.0, -1.0)
    for lag in np.arange(0.0, 30.0, 1 / FPS):
        shifted = np.interp(grid + lag, t_video, change, left=np.nan, right=np.nan)
        ok = ~np.isnan(shifted) & (grid > 5) & (grid < 40)
        r = float(np.corrcoef(shifted[ok], speed[ok])[0, 1])
        if r > best[1]:
            best = (float(lag), r)
    return best


def grab(video: Path, video_time: float, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-ss", f"{video_time:.3f}", "-i", str(video),
                    "-frames:v", "1", "-q:v", "2", "-y", str(path)], check=True)


def caption(joint: int, time: float) -> str:
    t, drift = test_data.story("story_drift_y", joint, CASE)
    return f"t = {time:.2f} s, story {joint} drift {np.interp(time, t, drift):+.4f}"


def sheet(paths_captions: list[tuple[Path, str]], rows: int, cols: int, out: Path, row_labels=None) -> None:
    width = figure_size(PROJECT_MODE)[0] * cols / 2.2
    fig, axes = plt.subplots(rows, cols, figsize=(width, width / cols * rows * 0.62), squeeze=False)
    for ax, (path, text) in zip(axes.flat, paths_captions):
        ax.imshow(mpimg.imread(path))
        ax.set_title(text, fontsize=plt.rcParams["legend.fontsize"] * 0.8)
        ax.axis("off")
    if row_labels:
        for ax, label in zip(axes[:, 0], row_labels):
            ax.text(-0.02, 0.5, label, transform=ax.transAxes, ha="right", va="center",
                    rotation=90, fontsize=plt.rcParams["axes.labelsize"])
    fig.tight_layout()
    save_figure(fig, out, formats=("png",), mode=PROJECT_MODE)


def peak_frames(joint: int, video: Path, lag: float) -> None:
    peaks = pd.read_csv(PROJECT / "06_results" / "experiment" / "2015" / CASE / "joints"
                        / f"joint_{joint}_JNT{joint}" / "peaks_a-i.csv")
    items = []
    for _, row in peaks.iterrows():
        jpg = OUTPUT / f"joint_{joint}" / f"peak_{row['peak']}.jpg"
        grab(video, row["time_s"] + lag, jpg)
        text = f"({row['peak']}) t = {row['time_s']:.2f} s, story {joint} drift {row['story_drift_rad']:+.4f} rad"
        fig, ax = plt.subplots(figsize=figure_size(PROJECT_MODE))
        ax.imshow(mpimg.imread(jpg))
        ax.set_title(text, fontsize=plt.rcParams["legend.fontsize"])
        ax.axis("off")
        save_figure(fig, jpg.with_suffix(""), formats=("png",), mode=PROJECT_MODE)
        jpg.unlink()
        items.append((jpg.with_suffix(".png"), text))
    sheet(items, 3, 3, OUTPUT / f"joint_{joint}_peaks_a-i")


def main() -> None:
    apply_style(PROJECT_MODE)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for joint, name in VIDEOS.items():
        lag, r = find_lag(joint, CASE_DIR / name)
        rows.append(dict(joint=joint, video=name, video_time_minus_test_time_s=round(lag, 2), correlation=round(r, 3)))
        print(f"joint {joint}: video = test + {lag:.2f} s (r = {r:.2f})")
    sync = pd.DataFrame(rows).set_index("joint")
    sync.to_csv(OUTPUT / "sync.csv")

    for joint, name in VIDEOS.items():
        lag = sync.loc[joint, "video_time_minus_test_time_s"]
        items = []
        for time in KEY_TIMES:
            path = OUTPUT / f"joint_{joint}" / f"frame_{time:05.2f}s.jpg"
            grab(CASE_DIR / name, time + lag, path)
            items.append((path, caption(joint, time)))
        sheet(items, 3, 3, OUTPUT / f"joint_{joint}_key_frames")

    for joint in (3, 4):
        peak_frames(joint, CASE_DIR / VIDEOS[joint], sync.loc[joint, "video_time_minus_test_time_s"])

    items = [(OUTPUT / f"joint_{joint}" / f"frame_{time:05.2f}s.jpg", caption(joint, time))
             for joint in VIDEOS for time in COMPARISON_TIMES]
    sheet(items, len(VIDEOS), len(COMPARISON_TIMES), OUTPUT / "comparison_joints_3_4_5",
          row_labels=[f"Joint {j}" for j in VIDEOS])


if __name__ == "__main__":
    main()
