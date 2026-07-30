"""Legacy FFT filtering and resampling compatible with the MATLAB helpers."""

from __future__ import annotations

import numpy as np


def _as_2d(data: np.ndarray) -> tuple[np.ndarray, bool]:
    values = np.asarray(data, dtype=float)
    was_1d = values.ndim == 1
    if was_1d:
        values = values[:, None]
    if values.ndim != 2:
        raise ValueError("Signal data must be one- or two-dimensional")
    return values, was_1d


def fft_filter(
    data: np.ndarray,
    sampling_frequency: float,
    cutoff: float | tuple[float, float],
    filter_type: str,
) -> np.ndarray:
    """Apply the mirrored ideal FFT filter used by ``Fn_filtering.m``."""
    values, was_1d = _as_2d(data)
    mirrored = np.concatenate((values, values[::-1]), axis=0)
    frequency = np.abs(np.fft.fftfreq(mirrored.shape[0], d=1.0 / sampling_frequency))
    spectrum = np.fft.fft(mirrored, axis=0)

    if filter_type == "fft_LPF":
        reject = frequency > float(cutoff)
    elif filter_type == "fft_HPF":
        reject = frequency < float(cutoff)
    elif filter_type == "fft_BPF":
        low, high = cutoff
        reject = (frequency < float(low)) | (frequency > float(high))
    else:
        raise ValueError(f"Unsupported legacy filter type: {filter_type}")

    spectrum[reject, :] = 0.0
    filtered = np.fft.ifft(spectrum, axis=0).real[: values.shape[0], :]
    return filtered[:, 0] if was_1d else filtered


def resample_decimate(data: np.ndarray, old_dt: float, new_dt: float) -> np.ndarray:
    """Reproduce the downsampling branch of ``Fn_Resampling.m``.

    The 2018 workflow only uses integer decimation from 1000 Hz to 100 Hz.
    The mirrored FFT record is low-pass limited at the new Nyquist frequency
    before every tenth sample is retained.
    """
    values, was_1d = _as_2d(data)
    factor = new_dt / old_dt
    decimation = int(round(factor))
    if decimation < 1 or not np.isclose(factor, decimation, atol=1e-12):
        raise ValueError("This legacy resampler requires an integer decimation factor")
    if decimation == 1:
        result = values.copy()
    else:
        mirrored = np.concatenate((values, values[::-1]), axis=0)
        frequency = np.abs(np.fft.fftfreq(mirrored.shape[0], d=old_dt))
        spectrum = np.fft.fft(mirrored, axis=0)
        spectrum[frequency > 0.5 / new_dt, :] = 0.0
        reconstructed = np.fft.ifft(spectrum, axis=0).real
        result = reconstructed[: values.shape[0] : decimation, :]
    return result[:, 0] if was_1d else result

