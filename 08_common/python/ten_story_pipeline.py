"""Raw-data-to-CSV workflow shared by the 2015 and 2018 ten-story tests."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from legacy_signal import fft_filter, resample_decimate


DT = 0.001
OUTPUT_DT = 0.01
STORY_HEIGHTS_MM = np.asarray(
    (2800.0, 2600.0, 2600.0, 2600.0, 2550.0,
     2550.0, 2550.0, 2500.0, 2500.0, 2500.0),
    dtype=float,
)


@dataclass(frozen=True)
class Case:
    index: int
    name: str
    test_date: str
    test_folder: str
    csv_prefix: str


@dataclass(frozen=True)
class ProjectSpec:
    year: int
    project_root: Path
    results_root: Path
    baseline_root: Path
    cases: tuple[Case, ...]
    loading_indices: tuple[int, ...]
    rebar_indices: tuple[int, ...]

    def case(self, selector: int | str) -> Case:
        if isinstance(selector, int) or str(selector).isdigit():
            index = int(selector)
            for item in self.cases:
                if item.index == index:
                    return item
        else:
            text = str(selector).casefold()
            matches = [item for item in self.cases if text in item.name.casefold()]
            if len(matches) == 1:
                return matches[0]
        raise ValueError(f"Unknown or ambiguous case selector: {selector}")

    @property
    def raw_root(self) -> Path:
        return self.project_root / "data" / "raw"

    def raw_directory(self, case: Case) -> Path:
        return self.raw_root / case.test_date / case.test_folder

    def result_directory(self, case: Case) -> Path:
        return self.results_root / case.name


def _raw_path(spec: ProjectSpec, case: Case, jb: int) -> Path:
    return spec.raw_directory(case) / f"{case.csv_prefix}{jb:02d}.csv"


def available_jbs(spec: ProjectSpec, case: Case) -> set[int]:
    directory = spec.raw_directory(case)
    found: set[int] = set()
    if not directory.is_dir():
        return found
    for path in directory.glob("*.csv"):
        suffix = path.stem[-2:]
        if suffix.isdigit():
            found.add(int(suffix))
    return found


def read_channels(
    spec: ProjectSpec,
    case: Case,
    jb: int,
    channels: Sequence[int],
) -> np.ndarray:
    """Read one-based channel numbers; CSV column zero is the time column."""
    source = _raw_path(spec, case, jb)
    if not source.is_file():
        raise FileNotFoundError(f"Required raw file not found: {source}")
    try:
        values = np.loadtxt(
            source,
            delimiter=",",
            skiprows=3,
            usecols=list(channels),
            # Only numeric rows are parsed. Latin-1 safely decodes the mixed
            # Japanese/UTF-8/CP932 header bytes found across acquisition files.
            encoding="latin1",
        )
    except (ValueError, UnicodeDecodeError):
        # Some acquisition files have ragged footer records. Preserve every
        # physical row and represent unavailable cells as NaN; dropping a
        # ragged row would shift the remaining time history.
        parsed: list[list[float]] = []
        with source.open("r", encoding="latin1", newline="") as stream:
            reader = csv.reader(stream)
            for _ in range(3):
                next(reader, None)
            for row in reader:
                current: list[float] = []
                for channel in channels:
                    try:
                        current.append(float(row[channel]))
                    except (IndexError, ValueError):
                        current.append(float("nan"))
                parsed.append(current)
        values = np.asarray(parsed, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    valid_rows = np.flatnonzero(np.any(np.isfinite(values), axis=1))
    if not valid_rows.size:
        raise ValueError(f"No numeric data in {source}")
    values = values[: valid_rows[-1] + 1]
    return np.asarray(values, dtype=float)


def _interpolate_nonfinite(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    x = np.arange(result.shape[0])
    for column in range(result.shape[1]):
        good = np.isfinite(result[:, column])
        if not np.any(good):
            raise ValueError(f"Channel {column + 1} contains no finite samples")
        if not np.all(good):
            result[:, column] = np.interp(x, x[good], result[good, column])
    return result


def _time(point_count: int) -> np.ndarray:
    return np.arange(point_count, dtype=float) * OUTPUT_DT


def _write_csv(
    path: Path,
    headers: Sequence[str],
    columns: Sequence[np.ndarray] | np.ndarray,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.column_stack(columns) if not isinstance(columns, np.ndarray) else columns
    if matrix.ndim != 2 or matrix.shape[1] != len(headers):
        raise ValueError(f"Header/data width mismatch for {path.name}")
    np.savetxt(
        path,
        matrix,
        delimiter=",",
        header=",".join(headers),
        comments="",
        fmt="%.17g",
    )
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _apply_smaller_absolute(
    side_a: np.ndarray,
    side_b: np.ndarray,
    threshold: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    a = side_a.copy()
    b = side_b.copy()
    eligible = np.ones(a.shape, dtype=bool)
    if threshold is not None:
        eligible = np.abs(a - b) > threshold
    replace_a = eligible & (np.abs(a) > np.abs(b))
    replace_b = eligible & (np.abs(b) > np.abs(a))
    a[replace_a] = b[replace_a]
    b[replace_b] = a[replace_b]
    return a, b


def _split_xyz(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return values[:, 0::3], values[:, 1::3], values[:, 2::3]


def _process_acceleration_2015(
    spec: ProjectSpec,
    case: Case,
) -> dict[str, np.ndarray]:
    jb13 = read_channels(spec, case, 13, range(1, 61))
    jb14 = read_channels(spec, case, 14, range(1, 22))
    raw = np.column_stack((jb13, jb14))
    processed = resample_decimate(
        fft_filter(raw, 1 / DT, (0.02, 100.0), "fft_BPF"),
        DT,
        OUTPUT_DT,
    )
    se_x = processed[:, 0:61:6]
    se_y = processed[:, 1:62:6]
    se_z = processed[:, 2:63:6]
    nw_x = processed[:, 3:64:6]
    nw_y = processed[:, 4:65:6]
    nw_z = processed[:, 5:66:6]
    # The archived script corrects only its first ten columns; RF is untouched.
    se_x[:, :10], nw_x[:, :10] = _apply_smaller_absolute(
        se_x[:, :10], nw_x[:, :10], None
    )
    se_y[:, :10], nw_y[:, :10] = _apply_smaller_absolute(
        se_y[:, :10], nw_y[:, :10], None
    )
    bf1 = processed[:, 72:78]
    bf1_x_a, bf1_x_b = _apply_smaller_absolute(bf1[:, 0:1], bf1[:, 3:4], None)
    bf1_y_a, bf1_y_b = _apply_smaller_absolute(bf1[:, 1:2], bf1[:, 4:5], None)
    acceleration_x = (se_x + nw_x) / 2.0
    acceleration_y = (se_y + nw_y) / 2.0
    acceleration_z = (se_z + nw_z) / 2.0
    bf1_center = np.column_stack(
        ((bf1_x_a[:, 0] + bf1_x_b[:, 0]) / 2.0,
         (bf1_y_a[:, 0] + bf1_y_b[:, 0]) / 2.0,
         (bf1[:, 2] + bf1[:, 5]) / 2.0)
    )
    masses = np.asarray(
        ((889 + 57) / 9.8, (817 + 28) / 9.8, (798 + 28) / 9.8,
         (780 + 28) / 9.8, (618 + 188) / 9.8, (949 + 28) / 9.8,
         (716 + 28) / 9.8, (694 + 28) / 9.8, (740 + 57) / 9.8,
         725 / 9.8),
        dtype=float,
    )
    force_x = -acceleration_x[:, 1:] * masses
    force_y = -acceleration_y[:, 1:] * masses
    shear_x = np.flip(np.cumsum(np.flip(force_x, axis=1), axis=1), axis=1)
    shear_y = np.flip(np.cumsum(np.flip(force_y, axis=1), axis=1), axis=1)
    return {
        "time": _time(processed.shape[0]),
        "acceleration_x": acceleration_x,
        "acceleration_y": acceleration_y,
        "acceleration_z": acceleration_z,
        "shear_x": shear_x,
        "shear_y": shear_y,
        "table_acceleration": processed[:, 66:69],
        "foundation_acceleration_bf1": bf1_center,
        "foundation_acceleration_bf2": processed[:, 78:81],
    }


def _process_acceleration_2018(
    spec: ProjectSpec,
    case: Case,
) -> dict[str, np.ndarray]:
    nw = read_channels(spec, case, 7, range(1, 65))
    se = read_channels(spec, case, 13, range(1, 65))
    nw_floor = nw[:, list(range(0, 12)) + list(range(15, 36))]
    se_floor = se[:, list(range(0, 12)) + list(range(18, 39))]
    nw_x, nw_y, nw_z = _split_xyz(nw_floor)
    se_x, se_y, se_z = _split_xyz(se_floor)
    se_x[:, 1:], nw_x[:, 1:] = _apply_smaller_absolute(
        se_x[:, 1:], nw_x[:, 1:], 1.0
    )
    se_y[:, 1:], nw_y[:, 1:] = _apply_smaller_absolute(
        se_y[:, 1:], nw_y[:, 1:], 1.0
    )
    if case.test_folder == "2019-0109-006-1":
        raw_time = np.arange(nw.shape[0], dtype=float) * DT
        bad = (raw_time >= 18.4) & (raw_time <= 19.0)
        reference = int(np.argmin(np.abs(raw_time - 30.0)))
        for values in (se_x, nw_x, se_y, nw_y):
            values[bad, 1:] = values[reference, 1:]
    acceleration_x_raw = (se_x + nw_x) / 2.0
    acceleration_y_raw = (se_y + nw_y) / 2.0
    acceleration_z_raw = (se_z + nw_z) / 2.0
    table_raw = (nw[:, 42:45] + se[:, 45:48]) / 2.0
    masses = np.asarray(
        ((848 + 57) / 9.81, (750 + 28) / 9.81, (732 + 28) / 9.81,
         (716 + 28) / 9.81, (870 + 188) / 9.81, (721 + 29) / 9.81,
         (657 + 28) / 9.81, (639 + 28) / 9.81, (706 + 57) / 9.81,
         579 / 9.81),
        dtype=float,
    )
    force_x = -acceleration_x_raw[:, 1:] * masses
    force_y = -acceleration_y_raw[:, 1:] * masses
    shear_x_raw = np.flip(np.cumsum(np.flip(force_x, axis=1), axis=1), axis=1)
    shear_y_raw = np.flip(np.cumsum(np.flip(force_y, axis=1), axis=1), axis=1)
    acceleration_x = resample_decimate(acceleration_x_raw, DT, OUTPUT_DT)
    acceleration_y = resample_decimate(acceleration_y_raw, DT, OUTPUT_DT)
    acceleration_z = resample_decimate(acceleration_z_raw, DT, OUTPUT_DT)
    table = resample_decimate(table_raw, DT, OUTPUT_DT)
    shear_x = resample_decimate(
        fft_filter(shear_x_raw, 1 / DT, 50.0, "fft_LPF"), DT, OUTPUT_DT
    )
    shear_y = resample_decimate(
        fft_filter(shear_y_raw, 1 / DT, 50.0, "fft_LPF"), DT, OUTPUT_DT
    )
    return {
        "time": _time(acceleration_x.shape[0]),
        "acceleration_x": acceleration_x,
        "acceleration_y": acceleration_y,
        "acceleration_z": acceleration_z,
        "shear_x": shear_x,
        "shear_y": shear_y,
        "table_acceleration": table,
    }


def process_acceleration(spec: ProjectSpec, case: Case) -> dict[str, np.ndarray]:
    return (
        _process_acceleration_2015(spec, case)
        if spec.year == 2015
        else _process_acceleration_2018(spec, case)
    )


def _process_displacement_current(
    spec: ProjectSpec,
    case: Case,
) -> dict[str, np.ndarray]:
    if spec.year == 2015:
        raw = np.column_stack(
            (read_channels(spec, case, 7, range(1, 57)),
             read_channels(spec, case, 10, range(1, 61)))
        )
        displacement = resample_decimate(raw, DT, OUTPUT_DT)
        nw_top_x = displacement[:, 0:73:8]
        nw_top_y = displacement[:, 2:75:8]
        se_top_x = displacement[:, 4:77:8]
        se_top_y = displacement[:, 6:79:8]
        if case.index == 10:
            se_top_x[:, 5] = nw_top_x[:, 5]
    else:
        raw = np.column_stack(
            (read_channels(spec, case, 7, range(50, 54)),
             read_channels(spec, case, 10, range(29, 65)),
             read_channels(spec, case, 12, range(1, 41)))
        )
        displacement = resample_decimate(raw, DT, OUTPUT_DT)
        nw_top_x = displacement[:, 0:40:4]
        nw_top_y = displacement[:, 2:40:4]
        se_top_x = displacement[:, 40:80:4]
        se_top_y = displacement[:, 42:80:4]
    story_x = (nw_top_x + se_top_x) / 2.0
    story_y = (nw_top_y + se_top_y) / 2.0
    return {
        "time": _time(story_x.shape[0]),
        "story_displacement_x": story_x,
        "story_displacement_y": story_y,
        "story_drift_x": story_x / STORY_HEIGHTS_MM,
        "story_drift_y": story_y / STORY_HEIGHTS_MM,
        "absolute_displacement_x": np.cumsum(story_x, axis=1),
        "absolute_displacement_y": np.cumsum(story_y, axis=1),
    }


def process_displacement(
    spec: ProjectSpec,
    case: Case,
    previous_residual: tuple[np.ndarray, np.ndarray] | None,
) -> tuple[dict[str, np.ndarray], tuple[np.ndarray, np.ndarray] | None]:
    result = _process_displacement_current(spec, case)
    if case.index not in spec.loading_indices:
        return result, previous_residual
    total_x = result["story_displacement_x"].copy()
    total_y = result["story_displacement_y"].copy()
    if previous_residual is not None:
        total_x += previous_residual[0]
        total_y += previous_residual[1]
    result.update({
        "total_story_displacement_x": total_x,
        "total_story_displacement_y": total_y,
        "total_story_drift_x": total_x / STORY_HEIGHTS_MM,
        "total_story_drift_y": total_y / STORY_HEIGHTS_MM,
        "total_absolute_displacement_x": np.cumsum(total_x, axis=1),
        "total_absolute_displacement_y": np.cumsum(total_y, axis=1),
    })
    return result, (total_x[-1].copy(), total_y[-1].copy())


def process_joint_rotation(spec: ProjectSpec, case: Case) -> dict[str, np.ndarray]:
    count = 38 if spec.year == 2015 else 12
    raw = read_channels(spec, case, 11, range(1, count + 1))
    displacement = resample_decimate(
        fft_filter(raw, 1 / DT, (0.05, 100.0), "fft_BPF"),
        DT,
        OUTPUT_DT,
    )
    if spec.year == 2015:
        coefficient = np.sqrt(270.0**2 + 270.0**2) / (2 * 270.0 * 270.0)
        rotation = np.column_stack(
            [coefficient * (displacement[:, i] - displacement[:, i + 1])
             for i in range(0, 10, 2)]
        )
    else:
        beam_depths = (550.0, 500.0, 500.0, 500.0, 500.0, 500.0)
        a1 = np.asarray((100, 100, 100, 100, 100, 100, 53, 50, 100, 100, 60, 60))
        a2 = np.asarray((100, 100, 100, 100, 100, 100, 60, 60, 100, 100, 55, 55))
        rotation_columns = []
        for node, beam_depth in enumerate(beam_depths):
            low = 2 * node
            high = low + 1
            span_a = 500.0 - 60.0 - 60.0
            span_b = (
                (beam_depth - a1[low] - a2[low])
                + (beam_depth - a1[high] - a2[high])
            ) / 2.0
            coefficient = np.sqrt(span_a**2 + span_b**2) / (2 * span_a * span_b)
            rotation_columns.append(
                coefficient * (displacement[:, low] - displacement[:, high])
            )
        rotation = np.column_stack(rotation_columns)
    return {"time": _time(rotation.shape[0]), "joint_rotation": rotation}


def process_foundation_displacement(
    spec: ProjectSpec,
    case: Case,
) -> dict[str, np.ndarray]:
    if spec.year != 2015:
        return {}
    raw = np.column_stack(
        (read_channels(spec, case, 10, range(25, 33)),
         read_channels(spec, case, 11, range(51, 55)))
    )
    displacement = resample_decimate(
        fft_filter(raw, 1 / DT, (0.02, 100.0), "fft_BPF"),
        DT,
        OUTPUT_DT,
    )
    x_indices = (0, 3, 4, 7, 8, 9, 10, 11)
    y_indices = (1, 2, 5, 6)
    return {
        "time": _time(displacement.shape[0]),
        "foundation_displacement_x": displacement[:, x_indices],
        "foundation_displacement_y": displacement[:, y_indices],
    }


def _read_rebar_matrix_2015(spec: ProjectSpec, case: Case) -> np.ndarray:
    parts = [
        read_channels(spec, case, 4, range(1, 53)),
        read_channels(spec, case, 5, range(1, 51)),
        read_channels(spec, case, 6, range(1, 63)),
        read_channels(spec, case, 16, range(1, 23)),
    ]
    length = min(part.shape[0] for part in parts)
    return _interpolate_nonfinite(np.column_stack([part[:length] for part in parts]))


def _process_rebar_2015(
    spec: ProjectSpec,
    case: Case,
    previous_residual: np.ndarray | None,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    raw = _read_rebar_matrix_2015(spec, case)
    baseline = np.mean(raw[: min(1000, raw.shape[0])], axis=0)
    corrected = raw - baseline
    if previous_residual is not None:
        corrected += previous_residual
    strain = resample_decimate(corrected, DT, OUTPUT_DT)
    residual = np.mean(strain[-min(100, strain.shape[0]):], axis=0)
    time = _time(strain.shape[0])
    window = (time >= 10.0) & (time <= 30.0)
    normalized = strain[window] / 2000.0
    selected_indices = (42, 103, 177, 183)
    return ({
        "time": time[window],
        "rebar_strain_all": normalized,
        "rebar_strain_selected": normalized[:, selected_indices],
    }, residual)


REBAR_2018_SELECTED_INDICES = (
    81, 83, 86, 88, 89, 90,
    7, 9, 12, 14, 15, 16,
    17, 19, 22, 24, 25, 26,
    141, 143, 146, 148, 149, 150,
    151, 153, 156, 158, 159, 160,
    181, 183, 186, 188, 189, 190,
    32, 35, 36, 37, 40, 41,
    161, 164, 165, 166, 169, 170,
    171, 174, 175, 176, 179, 180,
)

REBAR_2018_HEADERS = (
    "C3F_U_BR", "C3F_U_TR", "C3F_U_BL", "C3F_U_TL", "C3F_U_Stir_V", "C3F_U_Stir_H",
    "C4F_L_BR", "C4F_L_TR", "C4F_L_BL", "C4F_L_TL", "C4F_L_Stir_V", "C4F_L_Stir_H",
    "C4F_U_BR", "C4F_U_TR", "C4F_U_BL", "C4F_U_TL", "C4F_U_Stir_V", "C4F_U_Stir_H",
    "C5F_L_BR", "C5F_L_TR", "C5F_L_BL", "C5F_L_TL", "C5F_L_Stir_V", "C5F_L_Stir_H",
    "C5F_U_BR", "C5F_U_TR", "C5F_U_BL", "C5F_U_TL", "C5F_U_Stir_V", "C5F_U_Stir_H",
    "C6F_L_BR", "C6F_L_TR", "C6F_L_BL", "C6F_L_TL", "C6F_L_Stir_V", "C6F_L_Stir_H",
    "B4F_L_TL", "B4F_L_BL", "B4F_L_Stir", "B4F_R_TL", "B4F_R_BL", "B4F_R_Stir",
    "B5F_L_TL", "B5F_L_BL", "B5F_L_Stir", "B5F_R_TL", "B5F_R_BL", "B5F_R_Stir",
    "B6F_L_TL", "B6F_L_BL", "B6F_L_Stir", "B6F_R_TL", "B6F_R_BL", "B6F_R_Stir",
)


def _process_rebar_2018(spec: ProjectSpec, case: Case) -> dict[str, np.ndarray]:
    raw = np.column_stack(
        [read_channels(spec, case, jb, range(1, 65)) for jb in (4, 5, 6)]
    )
    strain = resample_decimate(
        fft_filter(raw, 1 / DT, (0.05, 100.0), "fft_BPF"),
        DT,
        OUTPUT_DT,
    )
    return {
        "time": _time(strain.shape[0]),
        "rebar_strain_all": strain,
        "rebar_strain_selected": strain[:, REBAR_2018_SELECTED_INDICES],
    }


def process_rebar(
    spec: ProjectSpec,
    case: Case,
    previous_residual: np.ndarray | None,
) -> tuple[dict[str, np.ndarray], np.ndarray | None]:
    if spec.year == 2015:
        return _process_rebar_2015(spec, case, previous_residual)
    return _process_rebar_2018(spec, case), previous_residual


def export_case_csv(
    spec: ProjectSpec,
    case: Case,
    results: dict[str, dict[str, np.ndarray]],
) -> list[Path]:
    csv_directory = spec.result_directory(case) / "csv"
    outputs: list[Path] = []
    floor_acc_headers = [f"{floor}F_m_per_s2" for floor in range(1, 11)] + ["RF_m_per_s2"]
    story_headers = [f"{floor}F" for floor in range(1, 11)]
    acceleration = results.get("acceleration", {})
    if acceleration:
        time = acceleration["time"]
        for direction in "xyz":
            outputs.append(_write_csv(
                csv_directory / f"floor_acceleration_{direction}.csv",
                ["Time_s", *floor_acc_headers],
                np.column_stack((time, acceleration[f"acceleration_{direction}"])),
            ))
        for direction in "xy":
            outputs.append(_write_csv(
                csv_directory / f"story_shear_{direction}.csv",
                ["Time_s", *[f"{name}_kN" for name in story_headers]],
                np.column_stack((time, acceleration[f"shear_{direction}"])),
            ))
        outputs.append(_write_csv(
            csv_directory / "table_acceleration.csv",
            ["Time_s", "TBL_X_m_per_s2", "TBL_Y_m_per_s2", "TBL_Z_m_per_s2"],
            np.column_stack((time, acceleration["table_acceleration"])),
        ))
        for key in ("foundation_acceleration_bf1", "foundation_acceleration_bf2"):
            if key in acceleration:
                outputs.append(_write_csv(
                    csv_directory / f"{key}.csv",
                    ["Time_s", "X_m_per_s2", "Y_m_per_s2", "Z_m_per_s2"],
                    np.column_stack((time, acceleration[key])),
                ))
    displacement = results.get("displacement", {})
    if displacement:
        time = displacement["time"]
        for key, unit in (
            ("story_displacement", "mm"),
            ("story_drift", "rad"),
            ("absolute_displacement", "mm"),
            ("total_story_displacement", "mm"),
            ("total_story_drift", "rad"),
            ("total_absolute_displacement", "mm"),
        ):
            for direction in "xy":
                data_key = f"{key}_{direction}"
                if data_key in displacement:
                    outputs.append(_write_csv(
                        csv_directory / f"{data_key}.csv",
                        ["Time_s", *[f"{name}_{unit}" for name in story_headers]],
                        np.column_stack((time, displacement[data_key])),
                    ))
    joint = results.get("joint", {})
    if joint:
        count = joint["joint_rotation"].shape[1]
        labels = ("1F", "2F", "3F", "4F", "6F") if spec.year == 2015 else tuple(f"{i}F" for i in range(1, 7))
        outputs.append(_write_csv(
            csv_directory / "joint_rotation.csv",
            ["Time_s", *[f"{label}_rad" for label in labels[:count]]],
            np.column_stack((joint["time"], joint["joint_rotation"])),
        ))
    foundation = results.get("foundation", {})
    if foundation:
        x_names = ("SLP-DX-SSW", "SLP-DX-NNW", "SLP-DX-NNE", "SLP-DX-SSE",
                   "SLP-DX-SSW-W", "SLP-DX-NNW-W", "SLP-DX-NNE-W", "SLP-DX-SSE-W")
        y_names = ("SLP-DY-WSW", "SLP-DY-WNW", "SLP-DY-ENE", "SLP-DY-ESE")
        outputs.append(_write_csv(
            csv_directory / "foundation_displacement_x.csv",
            ["Time_s", *x_names],
            np.column_stack((foundation["time"], foundation["foundation_displacement_x"])),
        ))
        outputs.append(_write_csv(
            csv_directory / "foundation_displacement_y.csv",
            ["Time_s", *y_names],
            np.column_stack((foundation["time"], foundation["foundation_displacement_y"])),
        ))
    rebar = results.get("rebar", {})
    if rebar:
        if spec.year == 2015:
            all_headers = [f"CH{i:03d}_eps_over_epsy" for i in range(1, 187)]
            selected_headers = (
                "4F_Beam_Longitudinal_Rebar_Col44",
                "4F_Column_Longitudinal_Rebar_Col105",
                "6F_Beam_Longitudinal_Rebar_Col179",
                "6F_Column_Longitudinal_Rebar_Col185",
            )
        else:
            all_headers = [f"CH{i:03d}_microstrain" for i in range(1, 193)]
            selected_headers = REBAR_2018_HEADERS
        outputs.append(_write_csv(
            csv_directory / "rebar_strain_all.csv",
            ["Time_s", *all_headers],
            np.column_stack((rebar["time"], rebar["rebar_strain_all"])),
        ))
        outputs.append(_write_csv(
            csv_directory / "rebar_strain_selected.csv",
            ["Time_s", *selected_headers],
            np.column_stack((rebar["time"], rebar["rebar_strain_selected"])),
        ))
    return outputs


def _prior_loading_cases(spec: ProjectSpec, case: Case) -> list[Case]:
    return [
        spec.case(index)
        for index in spec.loading_indices
        if index < case.index and spec.raw_directory(spec.case(index)).is_dir()
    ]


def _prepare_displacement_residual(
    spec: ProjectSpec,
    case: Case,
) -> tuple[np.ndarray, np.ndarray] | None:
    residual = None
    for previous in _prior_loading_cases(spec, case):
        _, residual = process_displacement(spec, previous, residual)
    return residual


def _prepare_rebar_residual(spec: ProjectSpec, case: Case) -> np.ndarray | None:
    if spec.year != 2015 or case.index not in spec.rebar_indices:
        return None
    residual = None
    for index in spec.rebar_indices:
        if index >= case.index:
            break
        previous = spec.case(index)
        if spec.raw_directory(previous).is_dir():
            _, residual = process_rebar(spec, previous, residual)
    return residual


def run_case(
    spec: ProjectSpec,
    case: Case,
    analyses: Iterable[str] = ("acceleration", "displacement", "joint", "foundation", "rebar"),
) -> dict:
    """Process one case directly from raw CSV and export machine-readable CSV."""
    selected = set(analyses)
    jbs = available_jbs(spec, case)
    if not jbs:
        raise FileNotFoundError(f"No raw CSV directory for {case.name}")
    results: dict[str, dict[str, np.ndarray]] = {}
    skipped: dict[str, str] = {}
    requirements = {
        "acceleration": {13, 14} if spec.year == 2015 else {7, 13},
        "displacement": {7, 10} if spec.year == 2015 else {7, 10, 12},
        "joint": {11},
        "foundation": {10, 11} if spec.year == 2015 else set(),
        "rebar": {4, 5, 6, 16} if spec.year == 2015 else {4, 5, 6},
    }
    for analysis in tuple(selected):
        if analysis not in requirements:
            raise ValueError(f"Unknown analysis: {analysis}")
        required = requirements[analysis]
        if not required:
            skipped[analysis] = "not applicable to this test"
            continue
        missing = required - jbs
        if missing:
            skipped[analysis] = f"missing raw JB files: {sorted(missing)}"
            continue
        if analysis == "acceleration":
            results[analysis] = process_acceleration(spec, case)
        elif analysis == "displacement":
            residual = _prepare_displacement_residual(spec, case)
            results[analysis], _ = process_displacement(spec, case, residual)
        elif analysis == "joint":
            results[analysis] = process_joint_rotation(spec, case)
        elif analysis == "foundation":
            results[analysis] = process_foundation_displacement(spec, case)
        elif analysis == "rebar":
            if spec.year == 2015 and case.index not in spec.rebar_indices:
                skipped[analysis] = "not one of the archived MATLAB rebar-loading cases"
            else:
                residual = _prepare_rebar_residual(spec, case)
                results[analysis], _ = process_rebar(spec, case, residual)
    outputs = export_case_csv(spec, case, results)
    metadata = {
        "project_year": spec.year,
        "case_index": case.index,
        "case": case.name,
        "test_date": case.test_date,
        "test_folder": case.test_folder,
        "raw_directory": str(spec.raw_directory(case)),
        "raw_data_policy": "read-only",
        "sample_interval_s": OUTPUT_DT,
        "completed_analyses": sorted(results),
        "skipped_analyses": skipped,
        "csv_files": [str(path) for path in outputs],
        "algorithm_reference": "archived MATLAB code",
    }
    _write_json(spec.result_directory(case) / "metadata.json", metadata)
    return metadata


def list_available_cases(spec: ProjectSpec) -> list[dict]:
    return [
        {
            "index": case.index,
            "name": case.name,
            "test_folder": case.test_folder,
            "available_jbs": sorted(available_jbs(spec, case)),
        }
        for case in spec.cases
        if spec.raw_directory(case).is_dir()
    ]


def load_csv(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream))
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data[None, :]
    return header, data
