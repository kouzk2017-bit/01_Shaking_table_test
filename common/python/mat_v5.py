"""Minimal reader for numeric vectors in MATLAB level-5 MAT files."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np


MI_INT8 = 1
MI_INT32 = 5
MI_UINT32 = 6
MI_DOUBLE = 9
MI_MATRIX = 14
MI_COMPRESSED = 15


def _elements(data: bytes):
    offset = 0
    while offset + 8 <= len(data):
        first = struct.unpack_from("<I", data, offset)[0]
        small_size = first >> 16
        small_type = first & 0xFFFF
        if small_size:
            yield small_type, data[offset + 4: offset + 4 + small_size]
            offset += 8
            continue
        data_type, size = struct.unpack_from("<II", data, offset)
        start = offset + 8
        yield data_type, data[start:start + size]
        # MATLAB commonly stores consecutive miCOMPRESSED elements without
        # the eight-byte padding used by ordinary elements.
        offset = start + size if data_type == MI_COMPRESSED else start + ((size + 7) // 8) * 8


def _matrix(payload: bytes) -> tuple[str, np.ndarray]:
    name = ""
    dimensions: tuple[int, ...] = ()
    values = None
    for data_type, data in _elements(payload):
        if data_type == MI_INT32 and not dimensions:
            dimensions = struct.unpack(f"<{len(data) // 4}i", data)
        elif data_type == MI_INT8 and not name:
            name = data.decode("ascii")
        elif data_type == MI_DOUBLE:
            values = np.frombuffer(data, dtype="<f8").copy()
    if not name or values is None:
        raise ValueError("Unsupported or incomplete MATLAB matrix")
    if dimensions and np.prod(dimensions) == values.size:
        values = values.reshape(dimensions, order="F")
    return name, values.squeeze()


def read_numeric_vectors(path: Path) -> dict[str, np.ndarray]:
    raw = path.read_bytes()
    if not raw.startswith(b"MATLAB 5.0 MAT-file"):
        raise ValueError(f"Not a MATLAB level-5 file: {path}")
    result: dict[str, np.ndarray] = {}
    for data_type, payload in _elements(raw[128:]):
        if data_type == MI_COMPRESSED:
            nested = zlib.decompress(payload)
            for nested_type, nested_payload in _elements(nested):
                if nested_type == MI_MATRIX:
                    name, values = _matrix(nested_payload)
                    result[name] = values
        elif data_type == MI_MATRIX:
            name, values = _matrix(payload)
            result[name] = values
    return result
