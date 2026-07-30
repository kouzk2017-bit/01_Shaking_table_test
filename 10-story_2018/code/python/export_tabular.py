"""Export processed NumPy arrays to machine-readable CSV files and metadata."""

from __future__ import annotations

import numpy as np

from config import (
    ACC_BAD_TIME,
    ACC_REFERENCE_TIME,
    CASE_NAME,
    CSV_DIRECTORY,
    DATA_DIRECTORY,
    GOSA_THRESHOLD,
    OUTPUT_DT,
    RESULT_DIRECTORY,
)
from io_utils import write_csv, write_json


def process() -> list[str]:
    acceleration = np.load(DATA_DIRECTORY / "acceleration.npz")
    shear = np.load(DATA_DIRECTORY / "story_shear.npz")
    drift = np.load(DATA_DIRECTORY / "story_drift.npz")
    joint = np.load(DATA_DIRECTORY / "joint_rotation.npz")
    metrics = np.load(DATA_DIRECTORY / "figure_metrics.npz")
    time = acceleration["time"]
    floor_acc = [f"{floor}F_m_per_s2" for floor in range(1, 11)] + ["RF_m_per_s2"]
    story_labels = [f"{floor}F" for floor in range(1, 11)]

    outputs = []
    for direction, key in (("x", "acceleration_x"), ("y", "acceleration_y"), ("z", "acceleration_z")):
        path = write_csv(
            CSV_DIRECTORY / f"floor_acceleration_{direction}.csv",
            ["Time_s", *floor_acc],
            [time, *[acceleration[key][:, i] for i in range(11)]],
        )
        outputs.append(str(path))

    outputs.append(str(write_csv(
        CSV_DIRECTORY / "table_acceleration.csv",
        ["Time_s", "TBL_X_m_per_s2", "TBL_Y_m_per_s2", "TBL_Z_m_per_s2"],
        [time, *[acceleration["table_acceleration"][:, i] for i in range(3)]],
    )))
    for direction, key in (("x", "shear_x"), ("y", "shear_y")):
        outputs.append(str(write_csv(
            CSV_DIRECTORY / f"story_shear_{direction}.csv",
            ["Time_s", *[f"{name}_kN" for name in story_labels]],
            [time, *[shear[key][:, i] for i in range(10)]],
        )))
    for direction in ("x", "y"):
        outputs.append(str(write_csv(
            CSV_DIRECTORY / f"story_displacement_{direction}.csv",
            ["Time_s", *[f"{name}_mm" for name in story_labels]],
            [time, *[drift[f"story_displacement_{direction}"][:, i] for i in range(10)]],
        )))
        outputs.append(str(write_csv(
            CSV_DIRECTORY / f"story_drift_{direction}.csv",
            ["Time_s", *[f"{name}_rad" for name in story_labels]],
            [time, *[drift[f"story_drift_{direction}"][:, i] for i in range(10)]],
        )))
        outputs.append(str(write_csv(
            CSV_DIRECTORY / f"absolute_displacement_{direction}.csv",
            ["Time_s", *[f"{name}_mm" for name in story_labels]],
            [time, *[drift[f"absolute_displacement_{direction}"][:, i] for i in range(10)]],
        )))
    outputs.append(str(write_csv(
        CSV_DIRECTORY / "joint_rotation.csv",
        ["Time_s", *[f"JNT{i}_rad" for i in range(1, 7)]],
        [time, *[joint["joint_rotation"][:, i] for i in range(6)]],
    )))

    metadata = {
        "case": CASE_NAME,
        "point_count": int(time.size),
        "time_start_s": float(time[0]),
        "time_end_s": float(time[-1]),
        "time_step_s": OUTPUT_DT,
        "manual_corrections": {
            "gosa_threshold_m_per_s2": GOSA_THRESHOLD,
            "acceleration_bad_time_s": list(ACC_BAD_TIME),
            "acceleration_reference_time_s": ACC_REFERENCE_TIME,
            "displacement": [
                "8F NW bottom X replaced by 8F NW top X",
                "10F SE bottom X replaced by 10F SE top X",
                "story displacement is the mean of NW/SE top/bottom gauges",
            ],
        },
        "max_abs_story_shear_x_kN": float(np.max(np.abs(shear["shear_x"]))),
        "max_abs_story_shear_y_kN": float(np.max(np.abs(shear["shear_y"]))),
        "figure_peak_times_s": {
            "4F": metrics["4F_peak_times"].tolist(),
            "6F": metrics["6F_peak_times"].tolist(),
        },
        "joint_contribution": {
            "4F": metrics["4F_contribution"].tolist(),
            "6F": metrics["6F_contribution"].tolist(),
        },
    }
    write_json(RESULT_DIRECTORY / "metadata.json", metadata)
    return outputs


if __name__ == "__main__":
    files = process()
    print(f"Generated {len(files)} CSV files")

