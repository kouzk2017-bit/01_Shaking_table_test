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
TEST = R / "experiment" / "2015" / "20151211-2(JMAKobe100%)" / "joints"
PROTO = R / "loading_protocols" / "2015_20151211-2(JMAKobe100%)_4F"
SHELL_H = R / "comparison" / "test_vs_shell" / "2015_4F_history_protocol" / "origin_history"
VARIANTS = R / "comparison" / "shell_variants"
SOLID = R / "comparison" / "test_vs_solid" / "2015_4F_history_protocol" / final_cases.case("solid")
SLAB = VARIANTS / "origin_slab_vs_origin"
SHOT = ROOT / "05_joint_models" / "screenshots"

# folder -> list of (group title, file prefix, [(source, content name)])
FOLDERS = {
    "1_test": [
        ("Test results, joint 4 (5F floor, JNT4)", "", [
            (SHOT / "jnt_locations_p16.png", "jnt_locations"),
            (TEST / "joint_4_01_drift_and_joint_angle.png", "drift_and_joint_angle"),
            (TEST / "joint_4_02_diagonal_strain.png", "joint_diagonal_strain"),
            (TEST / "joint_4_07_right_beam_bottom_bar_5G21-STR-E01.png", "right_beam_bottom_bar_5G21-E01"),
            (TEST / "joint_4_08_upper_column_left_bar_5F2AC-STR-02.png", "upper_left_column_bar_5F2AC-02"),
        ]),
    ],
    "2_shell": [
        ("Shell vs test, standard vs test-history loading", "1_vs_test_", [
            (Path(f"{PROTO}_measured_drift_and_reversals.png"), "history_protocol_from_test"),
            (Path(f"{PROTO}_protocol_vs_standard.png"), "history_vs_standard_protocol"),
            (SHELL_H / "01_story_shear_vs_story_drift.png", "hysteresis_standard_vs_history"),
            (SHELL_H / "02_joint_deformation_vs_story_drift.png", "joint_angle_vs_drift_with_test"),
            (SHELL_H / "07_joint_deformation_time_history.png", "joint_angle_time_history"),
            (SHELL_H / "11_normalized_shear_time_history.png", "normalized_shear_time_history"),
            (SHELL_H / "08_beam_bar_strain_time_history.png", "right_beam_bottom_bar_vs_5G21-E01"),
            (SHELL_H / "09_column_bar_strain_time_history.png", "upper_left_column_bar_vs_5F2AC-02"),
        ]),
        ("Parametric: column bars (J12/J16) x joint hoops (L/M/H), all cases with the original in one figure",
         "2_parametric_", [
            (VARIANTS / "all_variants" / "01_story_shear_skeleton.png", "story_shear"),
            (VARIANTS / "all_variants" / "02_joint_deformation_skeleton.png", "joint_angle"),
            (VARIANTS / "all_variants" / "03_beam_bar_strain_at_reversals.png", "right_beam_bottom_bar"),
            (VARIANTS / "all_variants" / "04_column_bar_strain_at_reversals.png", "upper_left_column_bar"),
            (VARIANTS / "all_variants" / "05_first_yield_drift.png", "first_yield_beam_vs_column"),
        ]),
        ("Slab flange: with vs without slab (standard protocol)", "3_slab_", [
            (SLAB / "01_story_shear_vs_story_drift.png", "story_shear"),
            (SLAB / "08_joint_deformation_angle_vs_story_drift.png", "joint_angle_vs_drift"),
            (SLAB / "02_beam_longitudinal_strain_vs_case_id.png", "right_beam_bottom_bar"),
            (SLAB / "03_column_longitudinal_strain_vs_case_id.png", "upper_left_column_bar"),
            (SHOT / "slab_E3_step472.png", "joint_core_crushing_E3"),
        ]),
    ],
    "3_solid": [
        ("Solid (final: Gc 61 N/mm, residual 20 MPa) vs test", "", [
            (SOLID / "03_normalized_shear_vs_story_drift.png", "normalized_shear_vs_drift"),
            (SOLID / "01_joint_deformation_vs_story_drift.png", "joint_angle_vs_drift"),
            (SOLID / "05_joint_deformation_time_history.png", "joint_angle_time_history"),
            (SOLID / "06_normalized_shear_time_history.png", "normalized_shear_time_history"),
            (SOLID / "07_beam_bar_strain_time_history.png", "right_beam_bottom_bar_vs_5G21-E01"),
            (SOLID / "08_upper_column_bar_strain_time_history.png", "upper_left_column_bar_vs_5F2AC-02"),
        ]),
    ],
}


def main() -> None:
    if OUT.exists():  # generated folder: rebuild from scratch so no stale copies remain
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    readme = [f"# Joint model figures ({OUT.name})", "",
              "Three folders: `1_test/`, `2_shell/`, `3_solid/`; files in slide order. Test = joint 4 (top of story 4, "
              "5F floor, JNT4). Rebar everywhere: right beam bottom bar (5G21-STR-E01) and upper-column left bar "
              "(5F2AC-STR-02); model nodes in `06_results/data_sources/`.", "",
              "Rebuild: `python 07_scripts/presentation/collect_joint_figures.py` (copies only).", ""]
    missing = []
    for folder, groups in FOLDERS.items():
        (OUT / folder).mkdir()
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
