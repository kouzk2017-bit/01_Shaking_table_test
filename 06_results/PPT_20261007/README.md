# Joint model figures (PPT_20261007)

Three folders: `1_test/`, `2_shell/`, `3_solid/`; files in slide order. Test = joint 4 (top of story 4, 5F floor, JNT4). Rebar everywhere: right beam bottom bar (5G21-STR-E01) and upper-column left bar (5F2AC-STR-02); model nodes in `06_results/data_sources/`.

Rebuild: `python 07_scripts/presentation/collect_joint_figures.py` (copies only).

## 1_test

**Test results, joint 4 (5F floor, JNT4)**

- `01_jnt_locations.png` ← `05_joint_models/screenshots/jnt_locations_p16.png`
- `02_drift_and_joint_angle.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_01_drift_and_joint_angle.png`
- `03_joint_diagonal_strain.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_02_diagonal_strain.png`
- `04_right_beam_bottom_bar_5G21-E01.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_07_right_beam_bottom_bar_5G21-STR-E01.png`
- `05_upper_left_column_bar_5F2AC-02.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_08_upper_column_left_bar_5F2AC-STR-02.png`

## 2_shell

**Shell vs test, standard vs test-history loading**

- `1_vs_test_01_history_protocol_from_test.png` ← `06_results/loading_protocols/2015_20151211-2(JMAKobe100%)_4F_measured_drift_and_reversals.png`
- `1_vs_test_02_history_vs_standard_protocol.png` ← `06_results/loading_protocols/2015_20151211-2(JMAKobe100%)_4F_protocol_vs_standard.png`
- `1_vs_test_03_hysteresis_standard_vs_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/01_story_shear_vs_story_drift.png`
- `1_vs_test_04_joint_angle_vs_drift_with_test.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/02_joint_deformation_vs_story_drift.png`
- `1_vs_test_05_joint_angle_time_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/07_joint_deformation_time_history.png`
- `1_vs_test_06_normalized_shear_time_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/11_normalized_shear_time_history.png`
- `1_vs_test_07_right_beam_bottom_bar_vs_5G21-E01.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/08_beam_bar_strain_time_history.png`
- `1_vs_test_08_upper_left_column_bar_vs_5F2AC-02.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/09_column_bar_strain_time_history.png`

**Parametric: column bars (J12/J16) x joint hoops (L/M/H), all cases with the original in one figure**

- `2_parametric_01_story_shear.png` ← `06_results/comparison/shell_variants/all_variants/01_story_shear_skeleton.png`
- `2_parametric_02_joint_angle.png` ← `06_results/comparison/shell_variants/all_variants/02_joint_deformation_skeleton.png`
- `2_parametric_03_right_beam_bottom_bar.png` ← `06_results/comparison/shell_variants/all_variants/03_beam_bar_strain_at_reversals.png`
- `2_parametric_04_upper_left_column_bar.png` ← `06_results/comparison/shell_variants/all_variants/04_column_bar_strain_at_reversals.png`
- `2_parametric_05_first_yield_beam_vs_column.png` ← `06_results/comparison/shell_variants/all_variants/05_first_yield_drift.png`

**Slab flange: with vs without slab (standard protocol)**

- `3_slab_01_story_shear.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/01_story_shear_vs_story_drift.png`
- `3_slab_02_joint_angle_vs_drift.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/08_joint_deformation_angle_vs_story_drift.png`
- `3_slab_03_right_beam_bottom_bar.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/02_beam_longitudinal_strain_vs_case_id.png`
- `3_slab_04_upper_left_column_bar.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/03_column_longitudinal_strain_vs_case_id.png`
- `3_slab_05_joint_core_crushing_E3.png` ← `05_joint_models/screenshots/slab_E3_step472.png`

## 3_solid

**Solid (final: Gc 61 N/mm, residual 20 MPa) vs test**

- `01_normalized_shear_vs_drift.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/03_normalized_shear_vs_story_drift.png`
- `02_joint_angle_vs_drift.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/01_joint_deformation_vs_story_drift.png`
- `03_joint_angle_time_history.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/05_joint_deformation_time_history.png`
- `04_normalized_shear_time_history.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/06_normalized_shear_time_history.png`
- `05_right_beam_bottom_bar_vs_5G21-E01.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/07_beam_bar_strain_time_history.png`
- `06_upper_left_column_bar_vs_5F2AC-02.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/08_upper_column_bar_strain_time_history.png`
