"""Calculate JNT1--JNT6 rotations from JB11 diagonal displacement gauges."""

from __future__ import annotations

import numpy as np

from config import (
    DATA_DIRECTORY,
    DT,
    JOINT_A1_MM,
    JOINT_A2_MM,
    JOINT_B1_MM,
    JOINT_B2_MM,
    JOINT_BEAM_DEPTHS_MM,
    JOINT_COLUMN_WIDTH_MM,
    OUTPUT_DT,
)
from io_utils import read_channels, save_npz
from legacy_signal import fft_filter, resample_decimate


def process() -> dict[str, np.ndarray]:
    raw = read_channels(11, tuple(range(1, 13)))
    filtered = fft_filter(raw, 1 / DT, (0.05, 100.0), "fft_BPF")
    displacement = resample_decimate(filtered, DT, OUTPUT_DT)

    a1 = np.asarray(JOINT_A1_MM, dtype=float)
    a2 = np.asarray(JOINT_A2_MM, dtype=float)
    b1 = np.asarray(JOINT_B1_MM, dtype=float)
    b2 = np.asarray(JOINT_B2_MM, dtype=float)
    rotation = np.empty((displacement.shape[0], 6), dtype=float)

    for node in range(6):
        low = 2 * node
        high = low + 1
        beam_depth = JOINT_BEAM_DEPTHS_MM[node]
        span_a = ((JOINT_COLUMN_WIDTH_MM - b1[low] - b2[low]) +
                  (JOINT_COLUMN_WIDTH_MM - b1[high] - b2[high])) / 2.0
        span_b = ((beam_depth - a1[low] - a2[low]) +
                  (beam_depth - a1[high] - a2[high])) / 2.0
        coefficient = np.sqrt(span_a**2 + span_b**2) / (2.0 * span_a * span_b)
        rotation[:, node] = coefficient * (displacement[:, low] - displacement[:, high])

    time = np.arange(rotation.shape[0], dtype=float) * OUTPUT_DT
    result = {"time": time, "joint_rotation": rotation}
    save_npz(DATA_DIRECTORY / "joint_rotation.npz", **result)
    return result


if __name__ == "__main__":
    arrays = process()
    print(f"Joint rotation processed: JNT1--JNT{arrays['joint_rotation'].shape[1]}")

