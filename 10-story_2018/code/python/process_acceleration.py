"""Process 2018 floor and table acceleration for case 20."""

from __future__ import annotations

import numpy as np

from config import (
    ACC_BAD_TIME,
    ACC_REFERENCE_TIME,
    DATA_DIRECTORY,
    DT,
    GOSA_THRESHOLD,
    OUTPUT_DT,
)
from io_utils import raw_time, read_channels, save_npz
from legacy_signal import resample_decimate


NW_FLOOR_CHANNELS = tuple(range(1, 13)) + tuple(range(16, 37))
SE_FLOOR_CHANNELS = tuple(range(1, 13)) + tuple(range(19, 40))
NW_TABLE_CHANNELS = (43, 44, 45)
SE_TABLE_CHANNELS = (46, 47, 48)


def split_xyz(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return values[:, 0::3], values[:, 1::3], values[:, 2::3]


def apply_gosa(
    se: np.ndarray, nw: np.ndarray, threshold: float
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the thresholded manual NW/SE replacement from the old script."""
    se = se.copy()
    nw = nw.copy()
    large_difference = np.abs(se - nw) > threshold
    replace_se = large_difference & (np.abs(se) > np.abs(nw))
    replace_nw = large_difference & (np.abs(nw) > np.abs(se))
    se[replace_se] = nw[replace_se]
    nw[replace_nw] = se[replace_nw]
    return se, nw


def replace_legacy_bad_interval(
    values: np.ndarray, time: np.ndarray
) -> np.ndarray:
    repaired = values.copy()
    bad = (time >= ACC_BAD_TIME[0]) & (time <= ACC_BAD_TIME[1])
    reference_row = int(np.argmin(np.abs(time - ACC_REFERENCE_TIME)))
    repaired[bad, :] = repaired[reference_row, :]
    if bad.sum() != 601:
        raise ValueError(f"Expected 601 legacy repair samples, found {bad.sum()}")
    return repaired


def process() -> dict[str, np.ndarray]:
    nw_x, nw_y, nw_z = split_xyz(read_channels(7, NW_FLOOR_CHANNELS))
    se_x, se_y, se_z = split_xyz(read_channels(13, SE_FLOOR_CHANNELS))
    if nw_x.shape != se_x.shape or nw_x.shape[1] != 11:
        raise ValueError("Expected matching 1F--RF NW/SE acceleration arrays")

    time_raw = raw_time(nw_x.shape[0])

    # Match old script: gosa and the j==3 bad-interval repair affect 2F--RF.
    se_x[:, 1:], nw_x[:, 1:] = apply_gosa(se_x[:, 1:], nw_x[:, 1:], GOSA_THRESHOLD)
    se_y[:, 1:], nw_y[:, 1:] = apply_gosa(se_y[:, 1:], nw_y[:, 1:], GOSA_THRESHOLD)
    for values in (se_x, nw_x, se_y, nw_y):
        values[:, 1:] = replace_legacy_bad_interval(values[:, 1:], time_raw)

    acceleration_x_raw = (se_x + nw_x) / 2.0
    acceleration_y_raw = (se_y + nw_y) / 2.0
    acceleration_z_raw = (se_z + nw_z) / 2.0

    table_nw = read_channels(7, NW_TABLE_CHANNELS)
    table_se = read_channels(13, SE_TABLE_CHANNELS)
    table_raw = (table_nw + table_se) / 2.0

    result = {
        "time": np.arange(resample_decimate(acceleration_x_raw, DT, OUTPUT_DT).shape[0]) * OUTPUT_DT,
        "acceleration_x": resample_decimate(acceleration_x_raw, DT, OUTPUT_DT),
        "acceleration_y": resample_decimate(acceleration_y_raw, DT, OUTPUT_DT),
        "acceleration_z": resample_decimate(acceleration_z_raw, DT, OUTPUT_DT),
        "table_acceleration": resample_decimate(table_raw, DT, OUTPUT_DT),
        # Keep repaired 1000 Hz horizontal arrays for the shear calculation.
        "acceleration_x_raw": acceleration_x_raw,
        "acceleration_y_raw": acceleration_y_raw,
    }
    save_npz(DATA_DIRECTORY / "acceleration.npz", **result)
    return result


if __name__ == "__main__":
    arrays = process()
    print(f"Acceleration processed: {arrays['time'].size} points at {1 / OUTPUT_DT:.0f} Hz")

