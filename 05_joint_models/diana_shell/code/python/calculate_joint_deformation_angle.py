"""Calculate DIANA joint deformation angle from four-node X/Z displacement CSVs.

The node layout is:
    623 (upper left)       620 (upper right)
    639 (lower left)       636 (lower right)

Diagonal 1 joins 623--636 and diagonal 2 joins 620--639.  The diagonal
instrument readings requested for the deformation-angle calculation are
the magnitudes of the relative nodal displacements:

    r = sqrt((u_x,b - u_x,a)^2 + (u_z,b - u_z,a)^2)
    gamma = d0 / (2 * a * b) * (r_623_636 - r_620_639)

For reference, the script also calculates each deformed diagonal length and
its signed length change (positive = extension; negative = shortening).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


def read_displacements(path: Path, direction: str, nodes: tuple[int, int, int, int]) -> pd.DataFrame:
    """Read a DIANA displacement export, skipping its units row."""
    frame = pd.read_csv(path, skiprows=[1])
    required = ["case label", "load factor"] + [f"TDt{direction} node {node}" for node in nodes]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")

    frame = frame[required].copy()
    frame = frame[frame["case label"].astype(str).str.startswith("Load-step")].copy()
    frame["load_step"] = frame["case label"].str.extract(r"Load-step\s+(\d+)")[0].astype(int)
    frame = frame.drop(columns="case label")
    frame = frame.rename(columns={f"TDt{direction} node {node}": f"u{direction.lower()}_{node}_mm" for node in nodes})
    return frame


def diagonal_results(data: pd.DataFrame, first: int, second: int, initial_dx: float, initial_dz: float, label: str) -> None:
    """Append relative displacement reading and signed diagonal length change."""
    relative_dx = data[f"ux_{second}_mm"] - data[f"ux_{first}_mm"]
    relative_dz = data[f"uz_{second}_mm"] - data[f"uz_{first}_mm"]
    data[f"{label}_relative_x_mm"] = relative_dx
    data[f"{label}_relative_z_mm"] = relative_dz
    data[f"{label}_reading_mm"] = np.hypot(relative_dx, relative_dz)

    initial_length = np.hypot(initial_dx, initial_dz)
    deformed_length = np.hypot(initial_dx + relative_dx, initial_dz + relative_dz)
    data[f"{label}_length_mm"] = deformed_length
    data[f"{label}_length_change_mm"] = deformed_length - initial_length


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("05_joint_models/diana_shell/data/raw/origin_2015"),
        help="Directory containing TDtX_nodes_620_623_636_639.csv and TDtZ_nodes_620_623_636_639.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("05_joint_models/diana_shell/data/processed/origin/joint_deformation_angle.csv"),
        help="Output CSV path.",
    )
    parser.add_argument("--a-mm", type=float, default=350.0, help="Joint width a in mm.")
    parser.add_argument("--b-mm", type=float, default=350.0, help="Joint height b in mm.")
    parser.add_argument("--upper-left", type=int, default=623, help="Node id at the upper-left corner.")
    parser.add_argument("--upper-right", type=int, default=620, help="Node id at the upper-right corner.")
    parser.add_argument("--lower-left", type=int, default=639, help="Node id at the lower-left corner.")
    parser.add_argument("--lower-right", type=int, default=636, help="Node id at the lower-right corner.")
    parser.add_argument(
        "--node-file-suffix",
        default=None,
        help="Override the '..._nodes_<a>_<b>_<c>_<d>.csv' suffix if it does not match "
        "upper-left_upper-right_lower-left_lower-right in that order (rare).",
    )
    args = parser.parse_args()

    upper_left, upper_right, lower_left, lower_right = (
        args.upper_left, args.upper_right, args.lower_left, args.lower_right,
    )
    nodes = (upper_left, upper_right, lower_left, lower_right)
    diagonal_1 = (upper_left, lower_right)
    diagonal_2 = (upper_right, lower_left)
    diagonal_1_label = f"diagonal_{upper_left}_{lower_right}"
    diagonal_2_label = f"diagonal_{upper_right}_{lower_left}"
    suffix = args.node_file_suffix or f"{upper_right}_{upper_left}_{lower_right}_{lower_left}"

    x_data = read_displacements(args.input_dir / f"TDtX_nodes_{suffix}.csv", "X", nodes)
    z_data = read_displacements(args.input_dir / f"TDtZ_nodes_{suffix}.csv", "Z", nodes)
    data = x_data.merge(z_data, on=["load_step", "load factor"], validate="one_to_one")

    # Coordinates use +X to the right and +Z upward.
    diagonal_results(data, *diagonal_1, args.a_mm, -args.b_mm, diagonal_1_label)
    diagonal_results(data, *diagonal_2, -args.a_mm, -args.b_mm, diagonal_2_label)

    initial_diagonal_mm = np.hypot(args.a_mm, args.b_mm)
    data["deformation_angle_rad"] = (
        initial_diagonal_mm / (2.0 * args.a_mm * args.b_mm)
        * (data[f"{diagonal_1_label}_reading_mm"] - data[f"{diagonal_2_label}_reading_mm"])
    )

    output_columns = [
        "load_step", "load factor",
        f"{diagonal_1_label}_relative_x_mm", f"{diagonal_1_label}_relative_z_mm",
        f"{diagonal_1_label}_reading_mm", f"{diagonal_1_label}_length_mm", f"{diagonal_1_label}_length_change_mm",
        f"{diagonal_2_label}_relative_x_mm", f"{diagonal_2_label}_relative_z_mm",
        f"{diagonal_2_label}_reading_mm", f"{diagonal_2_label}_length_mm", f"{diagonal_2_label}_length_change_mm",
        "deformation_angle_rad",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, columns=output_columns, index=False, float_format="%.8e")
    print(f"Wrote {len(data)} load steps to {args.output}")


if __name__ == "__main__":
    main()
