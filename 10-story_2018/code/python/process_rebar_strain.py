"""Process case-20 4F/6F longitudinal-rebar strain measurements."""

from __future__ import annotations

import numpy as np

from config import (
    CSV_DIRECTORY,
    DATA_DIRECTORY,
    DT,
    OUTPUT_DT,
    REBAR_CHANNELS,
    REBAR_PLOT_CHANNELS,
    STRAIN_BASELINE_DURATION,
    STRAIN_YIELD_MICROSTRAIN,
)
from io_utils import read_channels, save_npz, write_csv, write_json
from legacy_signal import resample_decimate


def _key(group: str) -> str:
    return group.lower().replace(" ", "_")


def process() -> dict[str, np.ndarray]:
    """Baseline-correct, FFT-resample and normalize all candidate channels.

    Case 20 is treated independently because the same JB04/JB06 strain
    acquisition layout is not present in cases 2--17. No high-pass filter or
    inherited residual is applied, preserving the plastic residual plateau.
    """
    baseline_points = int(round(STRAIN_BASELINE_DURATION / DT))
    if baseline_points < 1:
        raise ValueError("Strain baseline duration must contain at least one point")

    arrays: dict[str, np.ndarray] = {}
    channel_arrays: dict[str, np.ndarray] = {}
    time: np.ndarray | None = None

    for group, (jb, channels) in REBAR_CHANNELS.items():
        raw = read_channels(jb, channels)
        if raw.shape[0] < baseline_points:
            raise ValueError(f"{group} record is shorter than the baseline interval")
        corrected = raw - np.mean(raw[:baseline_points, :], axis=0)
        normalized = resample_decimate(corrected, DT, OUTPUT_DT) / STRAIN_YIELD_MICROSTRAIN
        group_time = np.arange(normalized.shape[0], dtype=float) * OUTPUT_DT
        if time is None:
            time = group_time
        elif not np.array_equal(time, group_time):
            raise ValueError(f"Resampled time mismatch in {group}")
        arrays[_key(group)] = normalized
        channel_arrays[f"{_key(group)}_channels"] = np.asarray(channels, dtype=int)

    assert time is not None
    save_npz(
        DATA_DIRECTORY / "rebar_strain.npz",
        time=time,
        **arrays,
        **channel_arrays,
    )

    all_headers = ["Time_s"]
    all_columns = [time]
    for group, (jb, channels) in REBAR_CHANNELS.items():
        values = arrays[_key(group)]
        for index, channel in enumerate(channels):
            all_headers.append(f"{group}_JB{jb:02d}_CH{channel:02d}_eps_over_epsy")
            all_columns.append(values[:, index])
    write_csv(CSV_DIRECTORY / "rebar_strain_all.csv", all_headers, all_columns)

    selected_headers = ["Time_s"]
    selected_columns = [time]
    for group, (jb, selected_channels) in REBAR_PLOT_CHANNELS.items():
        configured_jb, channels = REBAR_CHANNELS[group]
        if jb != configured_jb or any(channel not in channels for channel in selected_channels):
            raise ValueError(f"Selected plot channels JB{jb:02d} {selected_channels} are not in {group}")
        indices = [channels.index(channel) for channel in selected_channels]
        channel_label = "_".join(f"CH{channel:02d}" for channel in selected_channels)
        selected_headers.append(f"{group}_JB{jb:02d}_{channel_label}_mean_eps_over_epsy")
        selected_columns.append(np.mean(arrays[_key(group)][:, indices], axis=1))
    write_csv(CSV_DIRECTORY / "rebar_strain_selected.csv", selected_headers, selected_columns)

    write_json(
        DATA_DIRECTORY / "rebar_strain_metadata.json",
        {
            "case": "case 20 only",
            "raw_unit": "microstrain",
            "yield_strain_microstrain": STRAIN_YIELD_MICROSTRAIN,
            "baseline": f"mean of first {STRAIN_BASELINE_DURATION:g} s subtracted per channel",
            "residual_inheritance": False,
            "high_pass_filter": False,
            "resampling": "legacy mirrored FFT anti-alias resampling, 1000 Hz to 100 Hz",
            "candidate_channels": {
                group: {"jb": jb, "channels": list(channels)}
                for group, (jb, channels) in REBAR_CHANNELS.items()
            },
            "plot_channels": {
                group: {"jb": jb, "channels": list(channels), "combination": "arithmetic mean"}
                for group, (jb, channels) in REBAR_PLOT_CHANNELS.items()
            },
        },
    )
    return {"time": time, **arrays}


if __name__ == "__main__":
    result = process()
    print(f"Processed rebar strain: {result['time'].size} points at {1 / OUTPUT_DT:.0f} Hz")
