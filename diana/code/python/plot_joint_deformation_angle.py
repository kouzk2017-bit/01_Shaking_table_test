"""Plot DIANA joint deformation angle and its comparison with story drift.

The first figure compares the joint deformation angles of the original and
changed-column-longitudinal-rebar conditions. The second compares joint angle (solid) and story
drift (dashed) for both conditions. Steps 1--10 are excluded.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


CONDITIONS = {
    "origin": {"label": "Original axial force", "color": "#0072B2"},
    "changed_column_longitudinal_rebar": {"label": "Changed column longitudinal rebar", "color": "#D55E00"},
}


def read_condition(processed_dir: Path, condition: str) -> dict[str, np.ndarray]:
    """Join processed joint-angle and cyclic-response data by load step."""
    folder = processed_dir / condition
    with (folder / "joint_deformation_angle.csv").open(newline="", encoding="utf-8") as stream:
        joint_rows = list(csv.DictReader(stream))
    with (folder / "cyclic_response.csv").open(newline="", encoding="utf-8") as stream:
        cyclic_rows = list(csv.DictReader(stream))
    if not joint_rows or not cyclic_rows:
        raise ValueError(f"{condition}: expected processed rows are missing.")
    required_joint = {"load_step", "deformation_angle_rad"}
    required_cyclic = {"case_id", "story_drift_rad"}
    if not required_joint.issubset(joint_rows[0]) or not required_cyclic.issubset(cyclic_rows[0]):
        raise ValueError(f"{condition}: processed CSV has unexpected columns.")

    joint_by_step = {int(row["load_step"]): float(row["deformation_angle_rad"]) for row in joint_rows if int(row["load_step"]) > 10}
    drift_by_step = {int(row["case_id"]): float(row["story_drift_rad"]) for row in cyclic_rows if int(row["case_id"]) > 10}
    if len(joint_by_step) != sum(int(row["load_step"]) > 10 for row in joint_rows):
        raise ValueError(f"{condition}: duplicated joint-angle load step found.")
    if len(drift_by_step) != sum(int(row["case_id"]) > 10 for row in cyclic_rows):
        raise ValueError(f"{condition}: duplicated cyclic-response step found.")
    if set(joint_by_step) != set(drift_by_step):
        raise ValueError(f"{condition}: joint-angle and story-drift load steps do not match.")
    steps = np.asarray(sorted(joint_by_step), dtype=int)
    return {
        "load_step": steps,
        "deformation_angle_rad": np.asarray([joint_by_step[step] for step in steps]),
        "story_drift_rad": np.asarray([drift_by_step[step] for step in steps]),
    }

def save_figure(figure: plt.Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_dir / f"{stem}.svg", bbox_inches="tight")
    figure.savefig(output_dir / f"{stem}.png", dpi=600, bbox_inches="tight")
    plt.close(figure)


def style_axis(axis: plt.Axes) -> None:
    axis.axhline(0.0, color="0.45", linewidth=0.8, zorder=0)
    axis.grid(True, color="0.9", linewidth=0.7)
    axis.set_xlabel("Analysis step")
    axis.set_ylabel("Deformation angle (rad)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("diana/data/processed"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    data = {condition: read_condition(args.processed_dir, condition) for condition in CONDITIONS}
    ranges = {condition: (frame["load_step"].min(), frame["load_step"].max()) for condition, frame in data.items()}
    if len(set(ranges.values())) != 1:
        raise ValueError(f"Cyclic load-step ranges differ between conditions: {ranges}")

    figure, axis = plt.subplots(figsize=(7.2, 4.5))
    for condition, style in CONDITIONS.items():
        frame = data[condition]
        axis.plot(frame["load_step"], frame["deformation_angle_rad"], color=style["color"], linewidth=1.25, label=style["label"])
    style_axis(axis)
    axis.legend(frameon=False)
    save_figure(figure, args.output_dir, "07_joint_deformation_angle_by_step")

    figure, axis = plt.subplots(figsize=(7.2, 4.5))
    for condition, style in CONDITIONS.items():
        frame = data[condition]
        axis.plot(frame["load_step"], frame["deformation_angle_rad"], color=style["color"], linewidth=1.25, label=f"{style['label']} — joint")
        axis.plot(frame["load_step"], frame["story_drift_rad"], color=style["color"], linewidth=1.25, linestyle="--", label=f"{style['label']} — story drift")
    style_axis(axis)
    axis.legend(frameon=False, ncol=2)
    save_figure(figure, args.output_dir, "08_joint_deformation_angle_vs_story_drift")
    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
