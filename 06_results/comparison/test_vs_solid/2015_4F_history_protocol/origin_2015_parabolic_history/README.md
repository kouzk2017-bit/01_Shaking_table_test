# 4F joint: 2015 shaking table vs. DIANA solid (parabolic, test-history protocol)

试验 20151211-2(JMAKobe100%) 4F 节点 vs 实体 `origin_2015_parabolic_history`（parabolic 受压曲线，按试验 4F
实测层间位移角转折点加载）。2026-10-02 的运行在第 124 步（+0.016 rad）未收敛，第 137 步（+0.0225 rad）手动停止，
所以只覆盖试验的前两个转折点和第三段的一部分（试验第三个转折点在 +0.028 rad）。
图的格式同 `../../2015_4F_standard_protocol/origin_2015/`：`01` 节点变形角-层间位移角，`02` 转折点包络，`03` 归一化层剪力。

| | 试验 4F | 实体 |
|---|---|---|
| −0.0135 rad 转折点（试验 A 点） | 节点 −0.0045 | 节点 −0.0063，层剪力 −405 kN（峰值 −417 kN @ −0.013） |
| +0.0155 rad | 节点约 0.006，层剪力仍在上升 | 节点 0.006，366 kN |
| +0.016 rad 之后 | 继续上升到 +0.026 rad 才达峰 | 一步之内掉到 192 kN，节点变形角跳到 0.0137 |
| +0.022 rad | 节点约 0.010 | 节点 0.024（大于层间位移角） |

结论：破坏以前（≤ +0.0155 rad）实体跟试验的节点变形角吻合得不错；+0.016 rad 的骤降试验里没有，
三个版本（标准协议、加密步长、试验历程）都在同一位移角出现，所以不是步长或加载历程的问题。

生成：`python 05_joint_models/comparison/code/python/plot_experiment_vs_model_joint_drift.py --model solid --protocol history --diana-condition origin_2015_parabolic_history --diana-label "DIANA solid, parabolic, test-history protocol"`

时程对比 `04`–`08`（层间位移角、节点变形角、归一化层剪力、梁下筋、柱筋应变时程）由 `plot_solid_history_vs_test.py` 生成，图的说明见上一级 README。
