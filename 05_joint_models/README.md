# Joint (BCJ) numerical models

梁柱节点局部数值模型，区别于试验目录（`01_4-story/`、`02_10-story_2015/`、`03_10-story_2018/`）和整体建筑
数值模型（`04_building_models/`）。

- `diana_shell/`：DIANA 层壳节点模型，代码见 `code/python/`，结果见 `../06_results/diana/shell/`。
- `diana_solid/`：DIANA 实体节点模型。
  - `model/`：模型本体和原生分析数据库（`.dpf`/`.dnb`/`.out`，`.dnb` 体积很大 ~15.8 GB），
    整个目录已被 `.gitignore` 排除。
  - `data/raw/`、`data/processed/`：跟 `diana_shell` 一样分导出的原始节点响应和标准化后的
    数据，按工况分子目录（当前 `origin_2015`，梁端铰支模型）。
  - `code/python/prepare_rebar_response.py`：沿筋应变和 composed line 剪力的处理脚本；变形角复用
    `diana_shell` 的 `calculate_joint_deformation_angle.py`。`config/` 预留。
  - 跟层壳模型的对比结果在 `../06_results/comparison/joint_shell_vs_solid_origin/`。
- `drawings/`：两个模型共用的节点详图（DWG），不纳入版本控制。
- `comparison/`：跨模型/跨试验的对比脚本，结果见 `../06_results/comparison/`。
  - `plot_experiment_vs_model_joint_drift.py`：试验（动力时程）与节点数值模型（拟静力）
    对比，把两侧都转换成"节点变形角 vs 层间位移角"的响应-响应曲线后叠加，绕开时程/
    加载步数无法对齐的问题。
  - `plot_shell_vs_solid_joint_deformation.py`：层壳与实体两种节点模型的变形角对比，
    按加载步（两侧协议、步数一致，可直接比）。
  - `plot_shell_vs_solid_rebar_strain.py`：层壳与实体的节点箍筋、梁纵筋、柱纵筋应变对比
    （按加载步）。
  - `plot_solid_beam_bar_strain_profile.py`：实体整根梁纵筋、柱纵筋的沿筋应变分布。
  - `plot_shell_vs_solid_story_shear.py`：层壳与实体的层剪力对比（按加载步、按层间位移角）。
