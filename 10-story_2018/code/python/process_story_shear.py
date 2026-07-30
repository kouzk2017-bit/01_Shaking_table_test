"""Calculate 1F--10F story shear from 2F--RF inertial forces."""

from __future__ import annotations

import numpy as np

from config import DATA_DIRECTORY, DT, MASSES_T, OUTPUT_DT
from io_utils import save_npz
from legacy_signal import fft_filter, resample_decimate


def process() -> dict[str, np.ndarray]:
    source_path = DATA_DIRECTORY / "acceleration.npz"
    if not source_path.is_file():
        raise FileNotFoundError("Run process_acceleration.py first")
    source = np.load(source_path)
    masses = np.asarray(MASSES_T, dtype=float)

    force_x = -source["acceleration_x_raw"][:, 1:] * masses
    force_y = -source["acceleration_y_raw"][:, 1:] * masses
    shear_x_raw = np.flip(np.cumsum(np.flip(force_x, axis=1), axis=1), axis=1)
    shear_y_raw = np.flip(np.cumsum(np.flip(force_y, axis=1), axis=1), axis=1)

    # Old script filtered story shear, rather than floor acceleration, at 50 Hz.
    shear_x = resample_decimate(fft_filter(shear_x_raw, 1 / DT, 50.0, "fft_LPF"), DT, OUTPUT_DT)
    shear_y = resample_decimate(fft_filter(shear_y_raw, 1 / DT, 50.0, "fft_LPF"), DT, OUTPUT_DT)
    time = np.arange(shear_x.shape[0], dtype=float) * OUTPUT_DT
    result = {"time": time, "shear_x": shear_x, "shear_y": shear_y}
    save_npz(DATA_DIRECTORY / "story_shear.npz", **result)
    return result


if __name__ == "__main__":
    arrays = process()
    print(f"Maximum X story shear: {np.max(np.abs(arrays['shear_x'])):.3f} kN")
    print(f"Maximum Y story shear: {np.max(np.abs(arrays['shear_y'])):.3f} kN")

