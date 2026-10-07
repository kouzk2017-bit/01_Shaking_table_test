"""Copy the final joint-model figures into ONE flat folder for the progress presentation.

Output: the ppt_folder in final_cases.json; file names are <section>_<nn>_<content>.png in
slide order, plus README.md.  Re-run after regenerating any figure; it only copies, never
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

SECTIONS = {
    "1": ("Test results, joint 4 (5F floor, JNT4)", [
        (SHOT / "jnt_locations_p16.png", "jnt_locations"),
        (TEST / "joint_4_01_drift_and_joint_angle.png", "drift_and_joint_angle"),
        (TEST / "joint_4_02_diagonal_strain.png", "joint_diagonal_strain"),
        (TEST / "joint_4_04_beam_G2_east_end.png", "beam_G2_east_end_bars"),
        (TEST / "joint_4_03_beam_G1_west_end.png", "beam_G1_west_end_bars"),
        (TEST / "joint_4_06_upper_column_foot.png", "upper_column_foot_bars"),
        (TEST / "joint_4_05_lower_column_head.png", "lower_column_head_bars"),
    ]),
    "2": ("Shell model vs test, standard vs test-history loading", [
        (Path(f"{PROTO}_measured_drift_and_reversals.png"), "history_protocol_from_test"),
        (Path(f"{PROTO}_protocol_vs_standard.png"), "history_vs_standard_protocol"),
        (SHELL_H / "01_story_shear_vs_story_drift.png", "hysteresis_standard_vs_history"),
        (SHELL_H / "02_joint_deformation_vs_story_drift.png", "joint_angle_vs_drift_with_test"),
        (SHELL_H / "07_joint_deformation_time_history.png", "joint_angle_time_history"),
        (SHELL_H / "11_normalized_shear_time_history.png", "normalized_shear_time_history"),
        (SHELL_H / "08_beam_bar_strain_time_history.png", "right_beam_bottom_bar_vs_5G21-E01"),
        (SHELL_H / "09_column_bar_strain_time_history.png", "upper_left_column_bar_vs_5F2AC-02"),
    ]),
    "3": ("Shell parametric: column bars (J12/J16) and joint hoops (L/M/H), all cases in one figure", [
        (VARIANTS / "all_variants" / "01_story_shear_skeleton.png", "story_shear"),
        (VARIANTS / "all_variants" / "02_joint_deformation_skeleton.png", "joint_angle"),
        (VARIANTS / "all_variants" / "03_beam_bar_strain_at_reversals.png", "right_beam_bottom_bar"),
        (VARIANTS / "all_variants" / "04_column_bar_strain_at_reversals.png", "upper_left_column_bar"),
        (VARIANTS / "all_variants" / "05_first_yield_drift.png", "first_yield_beam_vs_column"),
    ]),
    "4": ("Solid model (final: Gc 61 N/mm, residual 20 MPa) vs test", [
        (SOLID / "03_normalized_shear_vs_story_drift.png", "normalized_shear_vs_drift"),
        (SOLID / "01_joint_deformation_vs_story_drift.png", "joint_angle_vs_drift"),
        (SOLID / "05_joint_deformation_time_history.png", "joint_angle_time_history"),
        (SOLID / "06_normalized_shear_time_history.png", "normalized_shear_time_history"),
        (SOLID / "07_beam_bar_strain_time_history.png", "right_beam_bottom_bar_vs_5G21-E01"),
        (SOLID / "08_upper_column_bar_strain_time_history.png", "upper_left_column_bar_vs_5F2AC-02"),
    ]),
    "5": ("Slab flange: shell with vs without slab (standard protocol)", [
        (SLAB / "01_story_shear_vs_story_drift.png", "story_shear"),
        (SLAB / "08_joint_deformation_angle_vs_story_drift.png", "joint_angle_vs_drift"),
        (SLAB / "02_beam_longitudinal_strain_vs_case_id.png", "right_beam_bottom_bar"),
        (SLAB / "03_column_longitudinal_strain_vs_case_id.png", "upper_left_column_bar"),
        (SHOT / "slab_E3_step472.png", "joint_core_crushing_E3"),
    ]),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    readme = [f"# Joint model figures ({OUT.name})", "",
              "One flat folder, files in slide order: `<section>_<nn>_<content>.png`. Test = joint 4 (top of story 4, "
              "5F floor, JNT4). Rebar positions everywhere: right beam bottom bar at the column face and upper-column "
              "left bar at the beam face (nodes: `06_results/data_sources/`).", "",
              "Rebuild: `python 07_scripts/presentation/collect_joint_figures.py` (copies only).", ""]
    missing = []
    for number, (title, items) in SECTIONS.items():
        readme += [f"## {number}. {title}", ""]
        for index, (src, content) in enumerate(items, 1):
            name = f"{number}_{index:02d}_{content}{src.suffix}"
            if src.exists():
                shutil.copy2(src, OUT / name)
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
