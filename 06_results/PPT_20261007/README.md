# Joint model figures (PPT_20261007)

One flat folder, files in slide order: `<section>_<nn>_<content>.png`. Test = joint 4 (top of story 4, 5F floor, JNT4). Rebar positions everywhere: right beam bottom bar at the column face and upper-column left bar at the beam face (nodes: `06_results/data_sources/`).

Rebuild: `python 07_scripts/presentation/collect_joint_figures.py` (copies only).

## 1. Test results, joint 4 (5F floor, JNT4)

- `1_01_jnt_locations.png` ← `05_joint_models/screenshots/jnt_locations_p16.png`
- `1_02_drift_and_joint_angle.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_01_drift_and_joint_angle.png`
- `1_03_joint_diagonal_strain.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_02_diagonal_strain.png`
- `1_04_beam_G2_east_end_bars.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_04_beam_G2_east_end.png`
- `1_05_beam_G1_west_end_bars.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_03_beam_G1_west_end.png`
- `1_06_upper_column_foot_bars.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_06_upper_column_foot.png`
- `1_07_lower_column_head_bars.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_05_lower_column_head.png`

## 2. Shell model vs test, standard vs test-history loading

- `2_01_history_protocol_from_test.png` ← `06_results/loading_protocols/2015_20151211-2(JMAKobe100%)_4F_measured_drift_and_reversals.png`
- `2_02_history_vs_standard_protocol.png` ← `06_results/loading_protocols/2015_20151211-2(JMAKobe100%)_4F_protocol_vs_standard.png`
- `2_03_hysteresis_standard_vs_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/01_story_shear_vs_story_drift.png`
- `2_04_joint_angle_vs_drift_with_test.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/02_joint_deformation_vs_story_drift.png`
- `2_05_joint_angle_time_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/07_joint_deformation_time_history.png`
- `2_06_normalized_shear_time_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/11_normalized_shear_time_history.png`
- `2_07_right_beam_bottom_bar_vs_5G21-E01.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/08_beam_bar_strain_time_history.png`
- `2_08_upper_left_column_bar_vs_5F2AC-02.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/09_column_bar_strain_time_history.png`

## 3. Shell parametric: column bars (J12/J16) and joint hoops (L/M/H), all cases in one figure

- `3_01_story_shear.png` ← `06_results/comparison/shell_variants/all_variants/01_story_shear_skeleton.png`
- `3_02_joint_angle.png` ← `06_results/comparison/shell_variants/all_variants/02_joint_deformation_skeleton.png`
- `3_03_right_beam_bottom_bar.png` ← `06_results/comparison/shell_variants/all_variants/03_beam_bar_strain_at_reversals.png`
- `3_04_upper_left_column_bar.png` ← `06_results/comparison/shell_variants/all_variants/04_column_bar_strain_at_reversals.png`
- `3_05_first_yield_beam_vs_column.png` ← `06_results/comparison/shell_variants/all_variants/05_first_yield_drift.png`

## 4. Solid model (final: Gc 61 N/mm, residual 20 MPa) vs test

- `4_01_normalized_shear_vs_drift.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/03_normalized_shear_vs_story_drift.png`
- `4_02_joint_angle_vs_drift.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/01_joint_deformation_vs_story_drift.png`
- `4_03_joint_angle_time_history.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/05_joint_deformation_time_history.png`
- `4_04_normalized_shear_time_history.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/06_normalized_shear_time_history.png`
- `4_05_right_beam_bottom_bar_vs_5G21-E01.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/07_beam_bar_strain_time_history.png`
- `4_06_upper_left_column_bar_vs_5F2AC-02.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/08_upper_column_bar_strain_time_history.png`

## 5. Slab flange: shell with vs without slab (standard protocol)

- `5_01_story_shear.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/01_story_shear_vs_story_drift.png`
- `5_02_joint_angle_vs_drift.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/08_joint_deformation_angle_vs_story_drift.png`
- `5_03_right_beam_bottom_bar.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/02_beam_longitudinal_strain_vs_case_id.png`
- `5_04_upper_left_column_bar.png` ← `06_results/comparison/shell_variants/origin_slab_vs_origin/03_column_longitudinal_strain_vs_case_id.png`
- `5_05_joint_core_crushing_E3.png` ← `05_joint_models/screenshots/slab_E3_step472.png`
