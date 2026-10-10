"""Copy the final joint-model figures into the presentation folder: 1_test/, 2_shell/, 3_solid/.

Output: the ppt_folder in final_cases.json (rebuilt from scratch each run); files in slide order,
plus README.md.  Re-run after regenerating any figure; it only copies, never
computes.  DIANA screenshots (not reproducible by script) live in 05_joint_models/screenshots/.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "08_common" / "python"))
import final_cases  # noqa: E402
R = ROOT / "06_results"
OUT = final_cases.ppt_folder()
EXPERIMENT = R / "experiment" / "2015" / "20151211-2(JMAKobe100%)"
JOINT = lambda n: EXPERIMENT / "joints" / f"joint_{n}_JNT{n}"
VIDEO = EXPERIMENT / "joint_videos"
PROTO = R / "loading_protocols" / "2015_20151211-2(JMAKobe100%)_4F"
SHELL_H = R / "comparison" / "test_vs_shell" / "2015_4F_history_protocol" / "origin_history"
VARIANTS = R / "comparison" / "shell_variants"
SOLID = R / "comparison" / "test_vs_solid" / "2015_4F_history_protocol" / final_cases.case("solid")
SLAB = VARIANTS / "origin_slab_vs_origin"
SLAB_SK = VARIANTS / "slab_vs_origin_skeleton"
SHOT = ROOT / "05_joint_models" / "screenshots"

# folder -> list of (group title, file prefix, [(source, content name)])
FOLDERS = {
    "1_test_story4_joint4": [
        ("Test, joint 4 (top of story 4, 5F floor, JNT4): peaks a-i from 13 s", "", [
            (SHOT / "jnt_locations_p16.png", "jnt_locations"),
            (JOINT(4) / "07_drift_and_joint_angle_peaks_a-i.png", "drift_and_joint_angle_peaks_a-i"),
            (JOINT(4) / "11_story_shear_vs_drift_peaks_a-i.png", "story_shear_vs_drift_peaks_a-i"),
            (JOINT(4) / "10_story_shear_time_history_peaks_a-i.png", "story_shear_time_history_peaks_a-i"),
            (JOINT(4) / "09_joint_ratio_at_peaks_a-i.png", "joint_ratio_at_peaks_a-i"),
            (JOINT(4) / "04_joint_diagonal_strain_time_history.png", "joint_diagonal_strain"),
            (JOINT(4) / "08a_rebar_negative_drift_pair_peaks_a-i.png", "rebar_negative_drift_left_beam_upper_column_right"),
            (JOINT(4) / "08b_rebar_positive_drift_pair_peaks_a-i.png", "rebar_positive_drift_right_beam_upper_column_left"),
            (VIDEO / "joint_4_peaks_a-i.png", "video_peaks_a-i_sheet"),
        ] + [(VIDEO / "joint_4" / f"peak_{k}.png", f"video_peak_{k}") for k in "abcdefghi"]),
    ],
    "2_shell": [
        ("Shell vs test, standard vs test-history loading", "1_vs_test_", [
            (Path(f"{PROTO}_measured_drift_and_reversals.png"), "history_protocol_from_test"),
            (Path(f"{PROTO}_protocol_vs_standard.png"), "history_vs_standard_protocol"),
            (SHELL_H / "01_story_shear_vs_story_drift.png", "hysteresis_standard_vs_history"),
            (SHELL_H / "02_joint_deformation_vs_story_drift.png", "joint_angle_vs_drift_with_test"),
            (SHELL_H / "07_joint_deformation_time_history.png", "joint_angle_time_history"),
            (SHELL_H / "11_normalized_shear_time_history.png", "normalized_shear_time_history"),
            (SHELL_H / "16_left_beam_bar_strain_time_history.png", "neg_left_beam_bottom_vs_5G11-W01"),
            (SHELL_H / "17_upper_column_right_bar_strain_time_history.png", "neg_upper_column_right_vs_5F2AC-09"),
            (SHELL_H / "08_beam_bar_strain_time_history.png", "pos_right_beam_bottom_vs_5G21-E01"),
            (SHELL_H / "09_column_bar_strain_time_history.png", "pos_upper_column_left_vs_5F2AC-02"),
        ]),
        ("Parametric: column bars (J12/J16) x joint hoops (L/M/H), all cases with the original in one figure",
         "2_parametric_", [
            (VARIANTS / "all_variants" / "01_story_shear_skeleton.png", "story_shear"),
            (VARIANTS / "all_variants" / "02_joint_deformation_skeleton.png", "joint_angle"),
            (VARIANTS / "all_variants" / "05_neg_left_beam_bottom_strain_at_reversals.png", "neg_left_beam_bottom"),
            (VARIANTS / "all_variants" / "06_neg_upper_column_right_strain_at_reversals.png", "neg_upper_column_right"),
            (VARIANTS / "all_variants" / "03_pos_right_beam_bottom_strain_at_reversals.png", "pos_right_beam_bottom"),
            (VARIANTS / "all_variants" / "04_pos_upper_column_left_strain_at_reversals.png", "pos_upper_column_left"),
            (VARIANTS / "all_variants" / "07_first_yield_by_direction.png", "first_yield_beam_vs_column_by_direction"),
        ]),
        ("Slab flange: with vs without slab (standard protocol)", "3_slab_", [
            (SLAB_SK / "01_story_shear_skeleton.png", "story_shear"),
            (SLAB_SK / "02_joint_deformation_skeleton.png", "joint_angle"),
            (SLAB_SK / "05_neg_left_beam_bottom_strain_at_reversals.png", "neg_left_beam_bottom"),
            (SLAB_SK / "06_neg_upper_column_right_strain_at_reversals.png", "neg_upper_column_right"),
            (SLAB_SK / "03_pos_right_beam_bottom_strain_at_reversals.png", "pos_right_beam_bottom"),
            (SLAB_SK / "04_pos_upper_column_left_strain_at_reversals.png", "pos_upper_column_left"),
            (SLAB_SK / "07_first_yield_by_direction.png", "first_yield_beam_vs_column_by_direction"),
            (SHOT / "slab_E3_step472.png", "joint_core_crushing_E3"),
        ]),
    ],
    "3_solid": [
        ("Solid (final: Gc 61 N/mm, residual 20 MPa) vs test", "", [
            (SOLID / "03_normalized_shear_vs_story_drift.png", "normalized_shear_vs_drift"),
            (SOLID / "01_joint_deformation_vs_story_drift.png", "joint_angle_vs_drift"),
            (SOLID / "05_joint_deformation_time_history.png", "joint_angle_time_history"),
            (SOLID / "06_normalized_shear_time_history.png", "normalized_shear_time_history"),
            (SOLID / "10_left_beam_bar_strain_time_history.png", "neg_left_beam_bottom_vs_5G11-W01"),
            (SOLID / "11_upper_column_right_bar_strain_time_history.png", "neg_upper_column_right_vs_5F2AC-09"),
            (SOLID / "07_beam_bar_strain_time_history.png", "pos_right_beam_bottom_vs_5G21-E01"),
            (SOLID / "08_upper_column_bar_strain_time_history.png", "pos_upper_column_left_vs_5F2AC-02"),
        ]),
    ],
    "4_test_story3_joint3": [
        ("Test, joint 3 (top of story 3, 4F floor, JNT3): peaks a-i from 13 s", "", [
            (JOINT(3) / "07_drift_and_joint_angle_peaks_a-i.png", "drift_and_joint_angle_peaks_a-i"),
            (JOINT(3) / "11_story_shear_vs_drift_peaks_a-i.png", "story_shear_vs_drift_peaks_a-i"),
            (JOINT(3) / "10_story_shear_time_history_peaks_a-i.png", "story_shear_time_history_peaks_a-i"),
            (JOINT(3) / "09_joint_ratio_at_peaks_a-i.png", "joint_ratio_at_peaks_a-i"),
            (JOINT(3) / "04_joint_diagonal_strain_time_history.png", "joint_diagonal_strain"),
            (JOINT(3) / "12_beam_end_elongation_peaks_a-i.png", "beam_end_elongation_left_vs_right"),
            (JOINT(3) / "13_column_end_opening_peaks_a-i.png", "column_end_opening"),
            (JOINT(3) / "14_beam_end_rotation_peaks_a-i.png", "beam_end_rotation_left_vs_right"),
            (JOINT(3) / "15_column_end_rotation_peaks_a-i.png", "column_end_rotation"),
            (JOINT(3) / "08a_rebar_negative_drift_pair_peaks_a-i.png", "rebar_negative_drift_left_beam_upper_column_right"),
            (JOINT(3) / "08b_rebar_positive_drift_pair_peaks_a-i.png", "rebar_positive_drift_right_beam_upper_column_left"),
            (VIDEO / "joint_3_peaks_a-i.png", "video_peaks_a-i_sheet"),
        ] + [(VIDEO / "joint_3" / f"peak_{k}.png", f"video_peak_{k}") for k in "abcdefghi"]),
    ]
}


def main() -> None:
    # Generated folder: empty it (not the folder itself, which may be open in Explorer) so no stale copies remain.
    OUT.mkdir(parents=True, exist_ok=True)
    for child in OUT.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    readme = [f"# Joint model figures ({OUT.name})", "",
              "Folders: `1_test_story4_joint4/`, `2_shell/`, `3_solid/`, `4_test_story3_joint3/`; files in slide order. Models = joint 4 (top of story 4, "
              "5F floor, JNT4). Rebar everywhere: right beam bottom bar (5G21-STR-E01) and upper-column left bar "
              "(5F2AC-STR-02); model nodes in `06_results/data_sources/`.", "",
              "Rebuild: `python 07_scripts/presentation/collect_joint_figures.py` (copies only).", ""]
    missing = []
    for folder, groups in FOLDERS.items():
        (OUT / folder).mkdir(exist_ok=True)
        readme += [f"## {folder}", ""]
        for title, prefix, items in groups:
            readme += [f"**{title}**", ""]
            for index, (src, content) in enumerate(items, 1):
                name = f"{prefix}{index:02d}_{content}{src.suffix}"
                if src.exists():
                    shutil.copy2(src, OUT / folder / name)
                    readme.append(f"- `{name}` ← `{src.relative_to(ROOT).as_posix()}`")
                else:
                    missing.append(str(src))
            readme.append("")
    (OUT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print(f"Copied into {OUT}")
    for m in missing:
        print("MISSING", m)


if __name__ == "__main__":
    main()
