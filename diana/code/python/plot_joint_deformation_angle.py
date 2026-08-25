"""Plot DIANA joint deformation angle and its comparison with story drift.

The first figure compares the joint deformation angles of the original and
50%-axial-force conditions. The second compares joint angle (solid) and story
drift (dashed) for both conditions. Steps 1--10 are excluded.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


CONDITIONS = {
    "origin": {"label": "Original axial force", "color": "#0072B2"},
    "50pct_axial_force": {"label": "50% axial force", "color": "#D55E00"},
}


def read_condition(processed_dir: Path, condition: str) -> pd.DataFrame:
    """Join processed joint-angle and cyclic-response data by load step."""
    folder = processed_dir / condition
    joint = pd.read_csv(folder / "joint_deformation_angle.csv")
    cyclic = pd.read_csv(folder / "cyclic_response.csv")
    if not {"load_step", "deformation_angle_rad"}.issubset(joint.columns):
        raise ValueError(f"{condition}: joint deformation-angle CSV has unexpected columns.")
    if not {"case_id", "story_drift_rad"}.issubset(cyclic.columns):
        raise ValueError(f"{condition}: cyclic-response CSV has unexpected columns.")

    joint = joint[joint["load_step"] > 10].copy()
    cyclic = cyclic[cyclic["case_id"] > 10].copy()
    if joint["load_step"].duplicated().any() or cyclic["case_id"].duplicated().any():
        raise ValueError(f"{condition}: duplicated load step found.")
    data = joint.merge(cyclic[["case_id", "story_drift_rad"]], left_on="load_step", right_on="case_id", how="inner", validate="one_to_one")
    if len(data) != len(joint) or len(data) != len(cyclic):
        raise ValueError(f"{condition}: joint-angle and story-drift load steps do not match.")
    return data.sort_values("load_step")


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
    parser.add_argument("--output-dir", type=Path, default=Path("results/diana/joint_deformation_angle"))
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
    save_figure(figure, args.output_dir, "joint_deformation_angle_by_step")

    figure, axis = plt.subplots(figsize=(7.2, 4.5))
    for condition, style in CONDITIONS.items():
        frame = data[condition]
        axis.plot(frame["load_step"], frame["deformation_angle_rad"], color=style["color"], linewidth=1.25, label=f"{style['label']} — joint")
        axis.plot(frame["load_step"], frame["story_drift_rad"], color=style["color"], linewidth=1.25, linestyle="--", label=f"{style['label']} — story drift")
    style_axis(axis)
    axis.legend(frameon=False, ncol=2)
    save_figure(figure, args.output_dir, "joint_deformation_angle_vs_story_drift")
    print(f"Wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
