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


NODES = (620, 623, 636, 639)
DIAGONAL_1 = (623, 636)
DIAGONAL_2 = (620, 639)


def read_displacements(path: Path, direction: str) -> pd.DataFrame:
    """Read a DIANA displacement export, skipping its units row."""
    frame = pd.read_csv(path, skiprows=[1])
    required = ["case label", "load factor"] + [f"TDt{direction} node {node}" for node in NODES]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")

    frame = frame[required].copy()
    frame = frame[frame["case label"].astype(str).str.startswith("Load-step")].copy()
    frame["load_step"] = frame["case label"].str.extract(r"Load-step\s+(\d+)")[0].astype(int)
    frame = frame.drop(columns="case label")
    frame = frame.rename(columns={f"TDt{direction} node {node}": f"u{direction.lower()}_{node}_mm" for node in NODES})
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
        default=Path("diana/data/raw/origin"),
        help="Directory containing TDtX_nodes_620_623_636_639.csv and TDtZ_nodes_620_623_636_639.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("diana/data/processed/origin/joint_deformation_angle.csv"),
        help="Output CSV path.",
    )
    parser.add_argument("--a-mm", type=float, default=350.0, help="Joint width a in mm.")
    parser.add_argument("--b-mm", type=float, default=350.0, help="Joint height b in mm.")
    args = parser.parse_args()

    x_data = read_displacements(args.input_dir / "TDtX_nodes_620_623_636_639.csv", "X")
    z_data = read_displacements(args.input_dir / "TDtZ_nodes_620_623_636_639.csv", "Z")
    data = x_data.merge(z_data, on=["load_step", "load factor"], validate="one_to_one")

    # Coordinates use +X to the right and +Z upward.
    diagonal_results(data, *DIAGONAL_1, args.a_mm, -args.b_mm, "diagonal_623_636")
    diagonal_results(data, *DIAGONAL_2, -args.a_mm, -args.b_mm, "diagonal_620_639")

    initial_diagonal_mm = np.hypot(args.a_mm, args.b_mm)
    data["deformation_angle_rad"] = (
        initial_diagonal_mm / (2.0 * args.a_mm * args.b_mm)
        * (data["diagonal_623_636_reading_mm"] - data["diagonal_620_639_reading_mm"])
    )

    output_columns = [
        "load_step", "load factor",
        "diagonal_623_636_relative_x_mm", "diagonal_623_636_relative_z_mm",
        "diagonal_623_636_reading_mm", "diagonal_623_636_length_mm", "diagonal_623_636_length_change_mm",
        "diagonal_620_639_relative_x_mm", "diagonal_620_639_relative_z_mm",
        "diagonal_620_639_reading_mm", "diagonal_620_639_length_mm", "diagonal_620_639_length_change_mm",
        "deformation_angle_rad",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, columns=output_columns, index=False, float_format="%.8e")
    print(f"Wrote {len(data)} load steps to {args.output}")


if __name__ == "__main__":
    main()
