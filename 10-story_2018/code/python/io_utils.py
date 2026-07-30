"""Raw CSV and processed-array I/O helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from config import DT, csv_path


def read_channels(jb: int, channels: list[int] | tuple[int, ...]) -> np.ndarray:
    """Read one-based JB channel numbers; CSV column zero is time."""
    source = csv_path(jb)
    if not source.is_file():
        raise FileNotFoundError(f"Required raw file not found: {source}")
    values = np.loadtxt(
        source,
        delimiter=",",
        skiprows=3,
        usecols=list(channels),
        encoding="cp932",
    )
    if values.ndim == 1:
        values = values[:, None]
    if not np.isfinite(values).all():
        raise ValueError(f"Non-finite values found in {source.name}, channels {channels}")
    return values


def raw_time(point_count: int) -> np.ndarray:
    return np.arange(point_count, dtype=float) * DT


def save_npz(path: Path, **arrays: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)
    return path


def write_csv(path: Path, headers: list[str], columns: list[np.ndarray]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.column_stack(columns)
    if matrix.shape[1] != len(headers):
        raise ValueError(f"Header/data width mismatch for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(matrix.tolist())
    return path


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

