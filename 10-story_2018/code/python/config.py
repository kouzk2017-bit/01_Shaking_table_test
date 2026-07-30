"""Configuration for the 2018 E-Defense 10-story case 20 analysis."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASE_NAME = "20190109-2(JMAKobe100%)"
TEST_DATE = "2019-0109"
TEST_FOLDER = "2019-0109-006-1"
CSV_PREFIX = "2019-0109-006-1_ENG_001-"
RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / TEST_DATE / TEST_FOLDER
RESULT_DIRECTORY = PROJECT_ROOT / "results" / "python" / CASE_NAME
DATA_DIRECTORY = RESULT_DIRECTORY / "data"
CSV_DIRECTORY = RESULT_DIRECTORY / "csv"
FIGURE_DIRECTORY = RESULT_DIRECTORY / "figures"

DT = 0.001
OUTPUT_DT = 0.01
OUTPUT_FS = 100.0
PLOT_START = 10.0
PLOT_END = 30.0

# Rebar strain processing. Raw values are microstrain; the paper plots
# strain normalized by the 2015 yield-strain value of 2000 microstrain.
STRAIN_YIELD_MICROSTRAIN = 2000.0
STRAIN_BASELINE_DURATION = 1.0

# Longitudinal-rebar channels confirmed from the 2019-01-09 raw headers.
# Stirrup channels JB04 CH16/17, CH37/42 and JB06 CH48/53, CH62/63 are
# intentionally excluded.
REBAR_CHANNELS = {
    "4F_column": (4, (8, 9, 10, 11, 12, 13, 14, 15)),
    "4F_beam": (4, (33, 34, 35, 36, 38, 39, 40, 41)),
    "6F_beam": (6, (44, 45, 46, 47, 49, 50, 51, 52)),
    "6F_column": (6, (54, 55, 56, 57, 58, 59, 60, 61)),
}

# Paired longitudinal gauges used by the publication-style 4F/6F plots.
# The two gauges at each selected reinforcing-bar position are averaged.
# All individual candidates remain available in rebar_strain.npz and
# rebar_strain_all.csv.
REBAR_PLOT_CHANNELS = {
    "4F_beam": (4, (40, 41)),
    "4F_column": (4, (14, 15)),
    "6F_beam": (6, (51, 52)),
    "6F_column": (6, (60, 61)),
}

# Old 2018 script: only replace one side when |SE-NW| > 1 m/s2.
GOSA_THRESHOLD = 1.0

# Old j==3 manual acceleration repair.  The legacy script used local rows
# 8400:9000 after selecting MATLAB rows 10000:30000.  Those rows correspond
# to approximately 18.398--18.998 s in the original zero-based time axis.
ACC_BAD_TIME = (18.398, 18.998)
ACC_REFERENCE_TIME = 29.999

# Old j==3 manual displacement-channel repairs (zero-based story columns).
# NW bottom X at 8F <- NW top X at 8F; SE bottom X at 10F <- SE top X at 10F.
NW_BOTTOM_X_REPLACE_STORY = 7
SE_BOTTOM_X_REPLACE_STORY = 9

# Weights [kN] and corresponding 2F--RF lumped masses [t].
GRAVITY = 9.81
WEIGHTS_KN = (905.0, 778.0, 760.0, 744.0, 1058.0,
              750.0, 685.0, 667.0, 763.0, 579.0)
MASSES_T = tuple(value / GRAVITY for value in WEIGHTS_KN)

STORY_HEIGHTS_MM = (2800.0, 2600.0, 2600.0, 2600.0, 2550.0,
                    2550.0, 2550.0, 2500.0, 2500.0, 2500.0)

# JB11 JNT1--JNT6 geometry copied from the 2018 Joint_Rad.m workflow.
JOINT_BEAM_DEPTHS_MM = (550.0, 500.0, 500.0, 500.0, 500.0, 500.0)
JOINT_COLUMN_WIDTH_MM = 500.0
JOINT_A1_MM = (100, 100, 100, 100, 100, 100, 53, 50, 100, 100, 60, 60)
JOINT_A2_MM = (100, 100, 100, 100, 100, 100, 60, 60, 100, 100, 55, 55)
JOINT_B1_MM = (60,) * 12
JOINT_B2_MM = (60,) * 12


def csv_path(jb: int) -> Path:
    """Return the raw CSV path for one junction box."""
    return RAW_DIRECTORY / f"{CSV_PREFIX}{jb:02d}.csv"
