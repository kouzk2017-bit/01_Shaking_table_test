"""Copy the final joint-model figures into one folder for the progress presentation.

Output: the ppt_folder in final_cases.json (re-run after regenerating any figure; it only
copies, never computes). Folder order follows the presentation outline in that folder's README.
Screenshots taken in DIANA during the 2026-10 discussion are not reproducible by script; they were
copied once into <output>/_screenshots and are linked from here by name.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "08_common" / "python"))
import final_cases  # noqa: E402
R = ROOT / "06_results"
JM = ROOT / "05_joint_models"
OUT = final_cases.ppt_folder()
TEST = R / "experiment" / "2015" / "20151211-2(JMAKobe100%)" / "joints"
SHELL_H = R / "comparison" / "test_vs_shell" / "2015_4F_history_protocol"
SOLID_H = R / "comparison" / "test_vs_solid" / "2015_4F_history_protocol"
FINAL = SOLID_H / final_cases.case("solid")
SOLID_RAW = JM / "diana_solid" / "data" / "raw" / final_cases.case("solid") / "contours"
SHELL_RAW = JM / "diana_shell" / "data" / "raw" / final_cases.raw("shell_history") / "contours"
SHOT = OUT / "_screenshots"
PROTO = R / "loading_protocols" / "2015_20151211-2(JMAKobe100%)_4F"

FILES = {
    "01_test_joint4": [
        (SHOT / "jnt_locations_p16.png", "00_jnt_locations_p16.png"),
        (TEST / "joint_4_01_drift_and_joint_angle.png", "01_drift_and_joint_angle.png"),
        (TEST / "joint_4_02_diagonal_strain.png", "02_diagonal_strain.png"),
        (TEST / "joint_4_03_beam_G1_west_end.png", "03_beam_G1_west_end_left.png"),
        (TEST / "joint_4_04_beam_G2_east_end.png", "04_beam_G2_east_end_right.png"),
        (TEST / "joint_4_05_lower_column_head.png", "05_lower_column_head.png"),
        (TEST / "joint_4_06_upper_column_foot.png", "06_upper_column_foot.png"),
    ],
    "02_loading_protocol": [
        (Path(f"{PROTO}_measured_drift_and_reversals.png"), "01_measured_drift_and_reversals.png"),
        (Path(f"{PROTO}_protocol_vs_standard.png"), "02_protocol_vs_standard.png"),
    ],
    "03_shell": [
        (SHELL_H / "01_story_shear_vs_story_drift.png", "01_hysteresis_standard_vs_history.png"),
        (SHELL_H / "02_joint_deformation_vs_story_drift.png", "02_joint_deformation_vs_drift_with_test.png"),
        (SHELL_H / "07_joint_deformation_time_history.png", "03_joint_deformation_time_history.png"),
        (SHELL_H / "11_normalized_shear_time_history.png", "04_normalized_shear_time_history.png"),
        (SHELL_H / "08_beam_bar_strain_time_history.png", "05_right_beam_bar_time_history.png"),
        (SHELL_H / "09_column_bar_strain_time_history.png", "06_upper_column_bar_time_history.png"),
        (SHELL_H / "12_lower_column_bar_strain_time_history.png", "07_lower_column_bar_time_history.png"),
    ],
    "04_shell_parametric": [
        (R / "diana" / "shell" / f"{v}_comparison" / src, f"{v}_{dst}")
        for v in ("j12_m", "j12_h", "j16_l", "j16_m", "j16_h", "v2018_vs_j16h")
        for src, dst in (("01_story_shear_vs_story_drift.png", "01_story_shear.png"),
                         ("08_joint_deformation_angle_vs_story_drift.png", "02_joint_angle_vs_drift.png"))
    ],
    "05_solid_calibration": [
        (SHOT / "solid_parabolic_E3_step123.png", "01_crushing_E3_step123_before_snap.png"),
        (SHOT / "solid_parabolic_E3_step124.png", "02_crushing_E3_step124_snap.png"),
        (SOLID_H / "summary_01_shear_at_reversals.png", "03_parameter_cases_shear.png"),
        (SOLID_H / "summary_02_joint_ratio_at_reversals.png", "04_parameter_cases_joint_ratio.png"),
    ],
    "06_solid_final": [
        (FINAL / "03_normalized_shear_vs_story_drift.png", "01_normalized_shear_vs_drift.png"),
        (FINAL / "01_joint_deformation_vs_story_drift.png", "02_joint_deformation_vs_drift.png"),
        (FINAL / "05_joint_deformation_time_history.png", "03_joint_deformation_time_history.png"),
        (FINAL / "06_normalized_shear_time_history.png", "04_normalized_shear_time_history.png"),
        (FINAL / "10_left_beam_bar_strain_time_history.png", "05_left_beam_bar.png"),
        (FINAL / "07_beam_bar_strain_time_history.png", "06_right_beam_bar.png"),
        (FINAL / "08_upper_column_bar_strain_time_history.png", "07_upper_column_bar.png"),
        (FINAL / "09_lower_column_bar_strain_time_history.png", "08_lower_column_bar.png"),
    ],
    "07_mechanism_contours": [
        (SOLID_RAW / "148.png", "01_solid_S3_step148_+0.028.png"),
        (SOLID_RAW / "148-2.png", "02_solid_E1_step148_+0.028.png"),
        (SOLID_RAW / "472.png", "03_solid_S3_step472_-0.030.png"),
        (SOLID_RAW / "472-2.png", "04_solid_E1_step472_-0.030.png"),
        (SHELL_RAW / "148.png", "05_shell_cover_S3_step148.png"),
        (SHELL_RAW / "148-2.png", "06_shell_core_S3_step148.png"),
        (SHELL_RAW / "472.png", "07_shell_cover_S3_step472.png"),
        (SHELL_RAW / "472-2.png", "08_shell_core_S3_step472.png"),
    ],
    "08_mechanism_tables": [
        (R / "comparison" / "failure_mechanism" / "README.md", "failure_mechanism_summary.md"),
        (R / "comparison" / "failure_mechanism" / "reversal_states.csv", "reversal_states.csv"),
        (R / "comparison" / "failure_mechanism" / "mechanism_stages.csv", "first_yield.csv"),
    ],
    "09_slab": [
        (SHELL_H / "origin_history_slab" / "04_story_shear_vs_story_drift.png", "01_story_shear_slab_vs_noslab.png"),
        (SHELL_H / "origin_history_slab" / "01_joint_deformation_time_history.png", "02_joint_deformation_time_history.png"),
        (SHOT / "slab_E3_step472.png", "03_slab_E3_step472.png"),
        (SHOT / "slab_measuring_frame.png", "04_slab_measuring_frame_nodes.png"),
    ],
}


def main() -> None:
    missing = []
    for folder, items in FILES.items():
        (OUT / folder).mkdir(parents=True, exist_ok=True)
        for src, dst in items:
            if src.exists():
                shutil.copy2(src, OUT / folder / dst)
            else:
                missing.append(str(src))
    print(f"Copied into {OUT}")
    for m in missing:
        print("MISSING", m)


if __name__ == "__main__":
    main()
