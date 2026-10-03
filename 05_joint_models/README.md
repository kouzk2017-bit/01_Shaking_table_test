# Joint (BCJ) numerical models

梁柱节点局部数值模型，区别于试验目录（`01_4-story/`、`02_10-story_2015/`、`03_10-story_2018/`）和整体建筑
数值模型（`04_opensees_model/`）。

- `diana_shell/`：DIANA 层壳节点模型，代码见 `code/python/`，结果见 `../06_results/diana/shell/`。
- `diana_solid/`：DIANA 实体节点模型。
  - `model/`：模型本体和原生分析数据库（`.dpf`/`.dnb`/`.out`，`.dnb` 体积很大 ~15.8 GB），
    整个目录已被 `.gitignore` 排除。
  - `data/raw/`、`data/processed/`：跟 `diana_shell` 一样分导出的原始节点响应和标准化后的
    数据，按工况分子目录（`origin_2015` 梁端铰支基准，及 `_nu_no_reduction`、`_parabolic`、`_parabolic_fine` 混凝土变体）。
  - `code/python/prepare_rebar_response.py`：沿筋应变和 composed line 剪力的处理脚本；变形角复用
    `diana_shell` 的 `calculate_joint_deformation_angle.py`。`config/` 预留。
  - `code/python/plot_solid_results.py --case <工况>`：实体自己的结果包 → `../06_results/diana/solid/<工况>/`。
  - `code/python/plot_solid_variant_comparison.py`：混凝土变体互相比较 → `../06_results/diana/solid/concrete_variants/`。
- `loading_protocols/`：按试验实测 4F 层间位移角历程生成的加载协议（每个工况一个目录：
  `reversal_points.csv`、逐步的 `load_steps.csv`、DIANA 显式步长 `diana_load_steps.txt`），
  由 `comparison/code/python/make_test_history_protocol.py` 生成，检查图在
  `../06_results/loading_protocols/`。步长与标准协议相同（荷载系数 0.1 = 0.0005 rad），
  第 1–10 步仍为轴力，循环从第 11 步开始。
- `drawings/`：两个模型共用的节点详图（DWG），不纳入版本控制。
- `comparison/`：跨模型/跨试验的对比脚本，结果见 `../06_results/comparison/`。
  - `plot_experiment_vs_model_joint_drift.py --model shell|solid`：试验（动力时程）与节点数值模型
    （拟静力）对比，两侧都转换成“响应 vs 层间位移角”（节点变形角、归一化层剪力）后叠加，绕开时程/
    加载步数无法对齐的问题；结果在 `../06_results/comparison/test_vs_<model>/2015_4F_standard_protocol/`。
  - `plot_history_vs_standard_protocol.py`：同一层壳模型在标准协议与试验历程协议下的对比
    （层剪力、节点变形角、钢筋应变、A–D 贡献比），结果见
    `../06_results/comparison/test_vs_shell/2015_4F_history_protocol/`。
  - `plot_history_protocol_vs_test.py`：试验历程协议结果按试验时间叠加到试验数据上
    （节点变形角、梁/柱纵筋应变、归一化层剪力），同一结果目录。
  - `plot_shell_vs_solid_*.py`（变形角、钢筋应变、层剪力，按加载步）：层壳 vs 实体。**暂停**，壳模型
    定稿后再跑，输出到 `../06_results/comparison/shell_vs_solid/`；2026-09 的图留档在
    `../06_results/archive/2026-10-01_shell_vs_solid_preliminary/`。
