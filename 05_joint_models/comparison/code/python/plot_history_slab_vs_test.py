"""Shell joint model with and without the slab flange, against the 2015 test.

Both shell runs use the 2015 Kobe 100% 4F test-history protocol:
  origin_history       no slab           raw origin_2015_history
  origin_history_slab  slab as a flange  raw origin_2015_history_slab
The slab model is remeshed, so its nodes differ (same positions):
  beam bottom bar at the column face  1628 -> 1254
  upper-column left bar at beam face  1839 -> 1559
  story shear                          524 -> 196
  joint stirrup                       2375 -> 2127
  joint frame corners  620/623/636/639 (300 x 366.67 mm)
                    -> 248/242/279/278 (375 x 361.42 mm)
The two measuring frames differ from each other and from the test anchors
(the 2015 pipeline uses a 270 x 270 mm JNT frame), so the joint angles are compared as given.

Each analysis step is placed on the test time axis with the protocol's
step-time map; the slab run may stop early and is plotted up to its last
step.  Outputs: 06_results/comparison/test_vs_shell/2015_4F_history_protocol/
origin_history_slab/ (each case in its own subfolder, like origin_history/).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(HERE))

from plot_history_protocol_vs_test import map_steps_to_time, read_group, test_series  # noqa: E402
from publication_style import COLORS, apply_style, figure_size, format_axis, reference_line_kwargs, save_figure  # noqa: E402

PROCESSED = WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed"
OUTPUT = WORKSPACE / "06_results" / "comparison" / "test_vs_shell" / "2015_4F_history_protocol" / "origin_history_slab"
PLOT_CONFIG = WORKSPACE / "08_common" / "config" / "plot_config.json"
YIELD_STRAIN = 0.002
FLOOR = 4
# Protocol steps of interest: A, the first large positive peak, B, +0.030.
KEY_STEPS = {"A (-0.0135)": 65, "+0.028": 148, "B (-0.022)": 248, "+0.030": 352, "-0.030": 472, "+0.030 (2nd)": 592, "D (-0.0255)": 703}

MODELS = (
    ("origin_history", "No slab", COLORS["accent"], "--"),
    ("origin_history_slab", "Slab flange", COLORS["primary"], "-"),
)


def read_processed(condition: str) -> dict[str, np.ndarray]:
    """Steps common to the joint-angle and cyclic tables of one condition."""
    def rows(name):
        with (PROCESSED / condition / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))
    cyclic = {int(r["case_id"]): r for r in rows("cyclic_response.csv")}
    joint = {int(r["load_step"]): float(r["deformation_angle_rad"]) for r in rows("joint_deformation_angle.csv")}
    stirrup = {int(r["case_id"]): float(r["joint_stirrup_exx"]) for r in rows("joint_stirrup_response.csv")}
    steps = np.asarray(sorted(set(cyclic) & set(joint) & set(stirrup)))
    return {
        "step": steps,
        "drift": np.asarray([float(cyclic[s]["story_drift_rad"]) for s in steps]),
        "shear": np.asarray([float(cyclic[s]["story_shear_kN"]) for s in steps]),
        "beam": np.asarray([float(cyclic[s]["beam_strain"]) for s in steps]) / YIELD_STRAIN,
        "column": np.asarray([float(cyclic[s]["column_strain"]) for s in steps]) / YIELD_STRAIN,
        "joint": np.asarray([joint[s] for s in steps]),
        "stirrup": np.asarray([stirrup[s] for s in steps]) / YIELD_STRAIN,
    }


def main() -> None:
    mode = json.loads(PLOT_CONFIG.read_text(encoding="utf-8"))["figure"]["style_mode"]
    apply_style(mode)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    drift_t, drift = test_series("story_drift_y.csv", f"{FLOOR}F_rad")
    mapping = map_steps_to_time(drift_t, drift)
    models = {name: read_processed(name) for name, *_ in MODELS}
    for data in models.values():
        data["time"] = np.asarray([mapping[int(s)] for s in data["step"]])
    # Both processed columns are the upper-column left bar at the beam face (1839 / 1559).
    last_step = int(min(data["step"][-1] for data in models.values()))
    window = (10.0, max(mapping[last_step], 12.0) + 0.3)

    angle_t, angle = test_series("joint_rotation.csv", f"{FLOOR}F_rad")
    # Joint 4 sits at the 5F floor: same gauges as plot_solid_history_vs_test.py
    # (G2 east-end bottom bar = DIANA right beam; 5th-story column foot).
    beam_t, beam = read_group(6, range(20, 21))
    column_t, column = read_group(16, range(2, 3))
    tests = {
        "joint": (angle_t, angle, "Test JNT (4F)"),
        "beam": (beam_t, beam["5G21-STR-E01"], "Test 5G21-STR-E01"),
        "column": (column_t, column["5F2AC-STR-02"], "Test 5F2AC-STR-02"),
    }
    figures = (
        ("joint", "Joint deformation angle (rad)", "01_joint_deformation_time_history"),
        ("beam", r"Beam bottom bar strain at column face $\epsilon/\epsilon_y$", "02_beam_bottom_bar_strain_time_history"),
        ("column", r"Upper column bar strain at beam face $\epsilon/\epsilon_y$", "03_upper_column_bar_strain_time_history"),
    )
    for key, ylabel, name in figures:
        fig, ax = plt.subplots(figsize=figure_size(mode))
        t, y, label = tests[key]
        mask = (t >= window[0]) & (t <= window[1])
        ax.plot(t[mask], y[mask], color="0.6", label=label)
        for condition, model_label, color, style in MODELS:
            data = models[condition]
            keep = (data["step"] <= last_step) & (data["time"] >= window[0])
            ax.plot(data["time"][keep], data[key][keep], color=color, linestyle=style, label=model_label)
        ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
        ax.set_xlim(window)
        format_axis(ax, xlabel="Time (s)", ylabel=ylabel, legend=True)
        save_figure(fig, OUTPUT / name, formats=("png",), mode=mode)

    fig, ax = plt.subplots(figsize=figure_size(mode))
    for condition, model_label, color, style in MODELS:
        data = models[condition]
        keep = data["step"] <= last_step
        ax.plot(data["drift"][keep], data["shear"][keep], color=color, linestyle=style, label=model_label)
    ax.axhline(0.0, **reference_line_kwargs(), zorder=0)
    ax.axvline(0.0, **reference_line_kwargs(), zorder=0)
    format_axis(ax, xlabel="Story drift (rad)", ylabel="Story shear (kN)", legend=True)
    save_figure(fig, OUTPUT / "04_story_shear_vs_story_drift", formats=("png",), mode=mode)
    plt.close("all")

    rows = []
    for label, step in KEY_STEPS.items():
        time = mapping[step]
        row = {"point": label, "step": step, "test_time_s": round(time, 2),
               "test_joint_angle": round(float(np.interp(time, angle_t, angle)), 5),
               "test_contribution": round(abs(float(np.interp(time, angle_t, angle) / np.interp(time, drift_t, drift))), 3),
               "test_beam": round(float(np.interp(time, beam_t, beam["5G21-STR-E01"])), 2),
               "test_column": round(float(np.interp(time, column_t, column["5F2AC-STR-02"])), 2)}
        for condition, model_label, *_ in MODELS:
            data = models[condition]
            index = np.flatnonzero(data["step"] == step)
            if not index.size:
                continue
            i = index[0]
            tag = "slab" if condition.endswith("slab") else "noslab"
            row.update({f"{tag}_shear_kN": round(float(data["shear"][i]), 1),
                        f"{tag}_contribution": round(abs(float(data["joint"][i] / data["drift"][i])), 3),
                        f"{tag}_beam": round(float(data["beam"][i]), 2),
                        f"{tag}_column": round(float(data["column"][i]), 2),
                        f"{tag}_stirrup": round(float(data["stirrup"][i]), 2)})
        rows.append(row)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (OUTPUT / "key_points.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)
    print(f"Slab run compared up to step {last_step} (test time {mapping[last_step]:.2f} s)")


if __name__ == "__main__":
    main()
