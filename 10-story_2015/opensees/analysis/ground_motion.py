"""Read the measured 2015 table motion without writing to the raw data tree.

Only NumPy and the standard library are required. Coordinates X/Y/Z are the
instrument coordinates; the caller must map them to the structural model axes.
"""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import numpy as np


# Original one-based case numbers from code/python/workflow_config.py. These are
# actual recorded motions, whose amplitude already includes the named percent.
LOADING_CASES = {
    2: ("20151125-2(JMAKobe10%)", "2015-1125", "2015-1125-012-1"),
    4: ("20151125-4(JMAKobe25%)", "2015-1125", "2015-1125-014-1"),
    7: ("20151125-7(JMAKobe50%)", "2015-1125", "2015-1125-017-1"),
    10: ("20151127-2(JMAKobe100%)", "2015-1127", "2015-1127-007-1"),
    13: ("20151209-2(JMAKobe10%)", "2015-1209", "2015-1209-006-1"),
    15: ("20151209-4(JMAKobe25%)", "2015-1209", "2015-1209-008-1"),
    17: ("20151209-6(JMAKobe50%)", "2015-1209", "2015-1209-010-1"),
    20: ("20151211-2(JMAKobe100%)", "2015-1211", "2015-1211-006-1"),
    22: ("20151211-4(JMAKobe60%)", "2015-1211", "2015-1211-008-1"),
}

SOURCE_CHANNELS = (7, 8, 9)
SOURCE_SENSOR_NAMES = ("839-TBL-AX-SW", "840-TBL-AY-SW", "841-TBL-AZ-SW")
OUTPUT_DT_S = 0.01


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_headers(path: Path) -> tuple[float, int]:
    # Mixed legacy Japanese encodings occur in the headers; the inspected fields
    # and sensor names are ASCII, so latin1 avoids irrelevant decoding failures.
    with path.open("r", encoding="latin1", newline="") as stream:
        reader = csv.reader(stream)
        acquisition, names, units = (next(reader) for _ in range(3))
    values = [item.strip() for item in acquisition]
    sample_index = values.index("SAMPLING_TIME")
    unit = values[sample_index + 2]
    if unit not in {"ms", "s"}:
        raise ValueError(f"Unsupported acquisition time unit: {unit!r}")
    dt = float(values[sample_index + 1]) * (0.001 if unit == "ms" else 1.0)
    count = int(values[values.index("DATA_NUMBER") + 1])
    for channel, expected_name in zip(SOURCE_CHANNELS, SOURCE_SENSOR_NAMES):
        if names[channel].strip() != expected_name:
            raise ValueError(f"JB14 CH{channel} is {names[channel]!r}, expected {expected_name!r}")
        if units[channel].strip() != "m/s^2":
            raise ValueError(f"Unexpected acceleration unit at JB14 CH{channel}: {units[channel]!r}")
    if units[0].strip() != "%s":
        raise ValueError(f"Unexpected raw time unit: {units[0]!r}")
    return dt, count


def _filter_and_decimate(values: np.ndarray, raw_dt: float) -> np.ndarray:
    """Match the shared pipeline's mirrored FFT filter and anti-alias resampler.

    The two FFT operations intentionally mirror separately: the legacy code
    mirrors the filtered original-length record again before decimation.
    """
    factor = OUTPUT_DT_S / raw_dt
    decimation = int(round(factor))
    if decimation < 1 or not np.isclose(factor, decimation, rtol=0, atol=1e-9):
        raise ValueError("Source dt must divide the 0.01 s output interval")
    count = values.shape[0]
    mirrored = np.concatenate((values, values[::-1]), axis=0)
    frequency = np.abs(np.fft.fftfreq(len(mirrored), d=raw_dt))
    spectrum = np.fft.fft(mirrored, axis=0)
    spectrum[(frequency < 0.02) | (frequency > 100.0), :] = 0.0
    filtered = np.fft.ifft(spectrum, axis=0).real[:count]
    if decimation == 1:
        return filtered
    mirrored = np.concatenate((filtered, filtered[::-1]), axis=0)
    spectrum = np.fft.fft(mirrored, axis=0)
    spectrum[frequency > 0.5 / OUTPUT_DT_S, :] = 0.0
    return np.fft.ifft(spectrum, axis=0).real[:count:decimation]


def load_ground_motion(
    project_root: Path,
    case_index: int = 2,
    duration_s: float | None = 10.0,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return time [s], measured X/Y/Z acceleration [mm/s²], and provenance.

    ``project_root`` is the ``10-story_2015`` directory. The full source is
    filtered before any truncation; its first sample and all prehistory remain.
    A zero sample is inserted at analysis t=0, and the measured record starts at
    t=0.01 s. Thus OpenSees can start from rest and interpolate to the first
    measured sample. The caller must NOT add another ``-prependZero`` or change
    the returned time origin. ``duration_s`` includes this 0.01 s shift; None
    returns the complete record. A fractional final interval is interpolated.

    Case 2 has its largest horizontal pulse near raw t=13.6 s, so a 20 s trial
    includes that pulse; the default 10 s only tests low-amplitude response.
    This reader applies no percent/g multiplier and no direction/sign rotation.
    """
    if case_index not in LOADING_CASES:
        raise ValueError(f"Unknown earthquake case {case_index}; choose from {sorted(LOADING_CASES)}")
    if duration_s is not None and (not math.isfinite(duration_s) or duration_s <= 0):
        raise ValueError("duration_s must be positive and finite, or None")
    project_root = Path(project_root).resolve()
    name, date, folder = LOADING_CASES[case_index]
    path = project_root / "data" / "raw" / date / folder / f"{folder}_ENG_001-14.csv"
    raw_dt, expected_count = _read_headers(path)
    source = np.loadtxt(
        path, delimiter=",", skiprows=3, usecols=(0, *SOURCE_CHANNELS), encoding="latin1"
    )
    if source.ndim != 2 or source.shape[1] != 4 or len(source) != expected_count:
        raise ValueError(f"Raw data count/shape differs from its header: {source.shape}, expected {expected_count}")
    if not np.isfinite(source).all():
        raise ValueError("Non-finite raw time or table acceleration; no automatic repair applied")
    if not np.isclose(source[0, 0], 0.0, atol=1e-10):
        raise ValueError("Expected the acquisition time to start at zero")
    if not np.allclose(np.diff(source[:, 0]), raw_dt, rtol=1e-7, atol=1e-10):
        raise ValueError("Actual raw time increments do not match the acquisition header")

    filtered = _filter_and_decimate(source[:, 1:], raw_dt)
    acceleration = np.vstack((np.zeros((1, 3)), filtered * 1000.0))
    times = np.arange(len(acceleration), dtype=float) * OUTPUT_DT_S
    complete_duration = float(times[-1])
    full_pga = np.max(np.abs(filtered), axis=0)
    full_peak_times = np.argmax(np.abs(filtered), axis=0) * OUTPUT_DT_S
    if duration_s is not None:
        if duration_s > complete_duration + 1e-9:
            raise ValueError(f"Requested {duration_s} s exceeds the {complete_duration:.6g} s available record")
        final_time = min(float(duration_s), complete_duration)
        count = int(np.searchsorted(times, final_time, side="right"))
        if count < len(times) and final_time > times[count - 1] + 1e-10:
            endpoint = np.asarray([np.interp(final_time, times, acceleration[:, j]) for j in range(3)])
            acceleration = np.vstack((acceleration[:count], endpoint))
            times = np.append(times[:count], final_time)
        else:
            acceleration = acceleration[:count]
            times = times[:count]

    metadata = {
        "case_index": int(case_index),
        "case_name": name,
        "test_base_condition": "sliding" if case_index <= 10 else "fixed",
        "test_history_note": (
            "First earthquake loading in the sliding-base series."
            if case_index == 2
            else "Continues preceding sliding-base earthquake loadings."
            if case_index <= 10
            else "Fixed-base series follows the sliding-base 10/25/50/100 percent series; do not assume an undamaged specimen."
        ),
        "base_condition_source": "documents/specimen_information/実験計画書・実験報告書/実験結果の報告.pdf, PDF pp.5-6; 実験計画書_10層RC.pdf, PDF p.7",
        "source_file": str(path),
        "source_relative_path": path.relative_to(project_root).as_posix(),
        "source_sha256": _sha256(path),
        "source_channels_one_based": list(SOURCE_CHANNELS),
        "source_sensor_names": list(SOURCE_SENSOR_NAMES),
        "source_units": "m/s^2",
        "output_units": "mm/s^2",
        "unit_conversion_factor": 1000.0,
        "additional_amplitude_scale": 1.0,
        "directions": ["X", "Y", "Z"],
        "direction_note": "Instrument axes and signs; map to model axes explicitly.",
        "raw_dt_s": float(raw_dt),
        "raw_sample_count": int(len(source)),
        "raw_last_time_s": float(source[-1, 0]),
        "nominal_output_dt_s": OUTPUT_DT_S,
        "output_sample_count": int(len(times)),
        "duration_requested_s": None if duration_s is None else float(duration_s),
        "duration_returned_s": float(times[-1]),
        "complete_duration_s": complete_duration,
        "analysis_time_shift_s": OUTPUT_DT_S,
        "initial_condition": "Explicit zero sample at t=0; original first sample at t=0.01 s; use returned times, no extra prependZero.",
        "filter": "Full-record mirrored ideal FFT band-pass 0.02-100 Hz; separately mirrored anti-alias low-pass 50 Hz; decimate to 0.01 s; then truncate.",
        "full_record_pga_m_s2_xyz": full_pga.tolist(),
        "full_record_peak_raw_time_s_xyz": full_peak_times.tolist(),
        "returned_pga_mm_s2_xyz": np.max(np.abs(acceleration), axis=0).tolist(),
        "percent_note": "Measured table record already represents the named test intensity; no further percent scaling.",
    }
    return times, acceleration, metadata
