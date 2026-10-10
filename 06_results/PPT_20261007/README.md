# Joint model figures (PPT_20261007)

Folders: `1_test_story4_joint4/`, `2_shell/`, `3_solid/`, `4_test_story3_joint3/`; files in slide order. Models = joint 4 (top of story 4, 5F floor, JNT4). Rebar everywhere: right beam bottom bar (5G21-STR-E01) and upper-column left bar (5F2AC-STR-02); model nodes in `06_results/data_sources/`.

Rebuild: `python 07_scripts/presentation/collect_joint_figures.py` (copies only).

## 1_test_story4_joint4

**Test, joint 4 (top of story 4, 5F floor, JNT4): peaks a-i from 13 s**

- `01_jnt_locations.png` ← `05_joint_models/screenshots/jnt_locations_p16.png`
- `02_drift_and_joint_angle_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/07_drift_and_joint_angle_peaks_a-i.png`
- `03_story_shear_vs_drift_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/11_story_shear_vs_drift_peaks_a-i.png`
- `04_story_shear_time_history_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/10_story_shear_time_history_peaks_a-i.png`
- `05_joint_ratio_at_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/09_joint_ratio_at_peaks_a-i.png`
- `06_joint_diagonal_strain.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/04_joint_diagonal_strain_time_history.png`
- `07_rebar_negative_drift_left_beam_upper_column_right.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/08a_rebar_negative_drift_pair_peaks_a-i.png`
- `08_rebar_positive_drift_right_beam_upper_column_left.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_4_JNT4/08b_rebar_positive_drift_pair_peaks_a-i.png`
- `09_video_peaks_a-i_sheet.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4_peaks_a-i.png`
- `10_video_peak_a.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_a.png`
- `11_video_peak_b.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_b.png`
- `12_video_peak_c.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_c.png`
- `13_video_peak_d.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_d.png`
- `14_video_peak_e.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_e.png`
- `15_video_peak_f.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_f.png`
- `16_video_peak_g.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_g.png`
- `17_video_peak_h.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_h.png`
- `18_video_peak_i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_4/peak_i.png`

## 2_shell

**Shell vs test, standard vs test-history loading**

- `1_vs_test_01_history_protocol_from_test.png` ← `06_results/loading_protocols/2015_20151211-2(JMAKobe100%)_4F_measured_drift_and_reversals.png`
- `1_vs_test_02_history_vs_standard_protocol.png` ← `06_results/loading_protocols/2015_20151211-2(JMAKobe100%)_4F_protocol_vs_standard.png`
- `1_vs_test_03_hysteresis_standard_vs_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/01_story_shear_vs_story_drift.png`
- `1_vs_test_04_joint_angle_vs_drift_with_test.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/02_joint_deformation_vs_story_drift.png`
- `1_vs_test_05_joint_angle_time_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/07_joint_deformation_time_history.png`
- `1_vs_test_06_normalized_shear_time_history.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/11_normalized_shear_time_history.png`
- `1_vs_test_07_neg_left_beam_bottom_vs_5G11-W01.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/16_left_beam_bar_strain_time_history.png`
- `1_vs_test_08_neg_upper_column_right_vs_5F2AC-09.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/17_upper_column_right_bar_strain_time_history.png`
- `1_vs_test_09_pos_right_beam_bottom_vs_5G21-E01.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/08_beam_bar_strain_time_history.png`
- `1_vs_test_10_pos_upper_column_left_vs_5F2AC-02.png` ← `06_results/comparison/test_vs_shell/2015_4F_history_protocol/origin_history/09_column_bar_strain_time_history.png`

**Parametric: column bars (J12/J16) x joint hoops (L/M/H), all cases with the original in one figure**

- `2_parametric_01_story_shear.png` ← `06_results/comparison/shell_variants/all_variants/01_story_shear_skeleton.png`
- `2_parametric_02_joint_angle.png` ← `06_results/comparison/shell_variants/all_variants/02_joint_deformation_skeleton.png`
- `2_parametric_03_neg_left_beam_bottom.png` ← `06_results/comparison/shell_variants/all_variants/05_neg_left_beam_bottom_strain_at_reversals.png`
- `2_parametric_04_neg_upper_column_right.png` ← `06_results/comparison/shell_variants/all_variants/06_neg_upper_column_right_strain_at_reversals.png`
- `2_parametric_05_pos_right_beam_bottom.png` ← `06_results/comparison/shell_variants/all_variants/03_pos_right_beam_bottom_strain_at_reversals.png`
- `2_parametric_06_pos_upper_column_left.png` ← `06_results/comparison/shell_variants/all_variants/04_pos_upper_column_left_strain_at_reversals.png`
- `2_parametric_07_first_yield_beam_vs_column_by_direction.png` ← `06_results/comparison/shell_variants/all_variants/07_first_yield_by_direction.png`

**Slab flange: with vs without slab (standard protocol)**

- `3_slab_01_story_shear.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/01_story_shear_skeleton.png`
- `3_slab_02_joint_angle.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/02_joint_deformation_skeleton.png`
- `3_slab_03_neg_left_beam_bottom.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/05_neg_left_beam_bottom_strain_at_reversals.png`
- `3_slab_04_neg_upper_column_right.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/06_neg_upper_column_right_strain_at_reversals.png`
- `3_slab_05_pos_right_beam_bottom.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/03_pos_right_beam_bottom_strain_at_reversals.png`
- `3_slab_06_pos_upper_column_left.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/04_pos_upper_column_left_strain_at_reversals.png`
- `3_slab_07_first_yield_beam_vs_column_by_direction.png` ← `06_results/comparison/shell_variants/slab_vs_origin_skeleton/07_first_yield_by_direction.png`
- `3_slab_08_joint_core_crushing_E3.png` ← `05_joint_models/screenshots/slab_E3_step472.png`

## 3_solid

**Solid (final: Gc 61 N/mm, residual 20 MPa) vs test**

- `01_normalized_shear_vs_drift.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/03_normalized_shear_vs_story_drift.png`
- `02_joint_angle_vs_drift.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/01_joint_deformation_vs_story_drift.png`
- `03_joint_angle_time_history.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/05_joint_deformation_time_history.png`
- `04_normalized_shear_time_history.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/06_normalized_shear_time_history.png`
- `05_neg_left_beam_bottom_vs_5G11-W01.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/10_left_beam_bar_strain_time_history.png`
- `06_neg_upper_column_right_vs_5F2AC-09.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/11_upper_column_right_bar_strain_time_history.png`
- `07_pos_right_beam_bottom_vs_5G21-E01.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/07_beam_bar_strain_time_history.png`
- `08_pos_upper_column_left_vs_5F2AC-02.png` ← `06_results/comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/08_upper_column_bar_strain_time_history.png`

## 4_test_story3_joint3

**Test, joint 3 (top of story 3, 4F floor, JNT3): peaks a-i from 13 s**

- `01_drift_and_joint_angle_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/07_drift_and_joint_angle_peaks_a-i.png`
- `02_story_shear_vs_drift_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/11_story_shear_vs_drift_peaks_a-i.png`
- `03_story_shear_time_history_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/10_story_shear_time_history_peaks_a-i.png`
- `04_joint_ratio_at_peaks_a-i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/09_joint_ratio_at_peaks_a-i.png`
- `05_joint_diagonal_strain.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/04_joint_diagonal_strain_time_history.png`
- `06_beam_end_elongation_left_vs_right.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/12_beam_end_elongation_peaks_a-i.png`
- `07_column_end_opening.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/13_column_end_opening_peaks_a-i.png`
- `08_beam_end_rotation_left_vs_right.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/14_beam_end_rotation_peaks_a-i.png`
- `09_column_end_rotation.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/15_column_end_rotation_peaks_a-i.png`
- `10_rebar_negative_drift_left_beam_upper_column_right.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/08a_rebar_negative_drift_pair_peaks_a-i.png`
- `11_rebar_positive_drift_right_beam_upper_column_left.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/joint_3_JNT3/08b_rebar_positive_drift_pair_peaks_a-i.png`
- `12_video_peaks_a-i_sheet.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3_peaks_a-i.png`
- `13_video_peak_a.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_a.png`
- `14_video_peak_b.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_b.png`
- `15_video_peak_c.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_c.png`
- `16_video_peak_d.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_d.png`
- `17_video_peak_e.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_e.png`
- `18_video_peak_f.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_f.png`
- `19_video_peak_g.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_g.png`
- `20_video_peak_h.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_h.png`
- `21_video_peak_i.png` ← `06_results/experiment/2015/20151211-2(JMAKobe100%)/joint_videos/joint_3/peak_i.png`
