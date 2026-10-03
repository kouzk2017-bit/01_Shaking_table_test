# 4F joint: 2015 shaking table vs. DIANA solid (origin_2015)

试验 20151211-2(JMAKobe100%) 4F 节点（动力时程）与实体节点模型 `origin_2015`（梁端铰支，标准拟静力协议
±0.005/0.01/0.02/0.03/0.04 rad 各一圈）。两边都画成“响应-层间位移角”，不按时间或加载步对齐。

- `01_joint_deformation_vs_story_drift.png`：节点变形角-层间位移角全轨迹，试验标出 A–D 负向峰值。
- `02_joint_deformation_vs_story_drift_envelope.png`：只保留转折点的简化包络。
- `03_normalized_shear_vs_story_drift.png`：层剪力各自除以自身峰值（试验是 4F 整层剪力 3691 kN，
  模型是一个节点 373 kN，只比形状）。

| | 试验 4F | 实体 origin_2015 |
|---|---|---|
| 层剪力峰值出现的层间位移角 | +0.026 rad | +0.010 rad，之后骤降到约 0.5 V_max |
| 节点变形角 @ +0.03 rad | 0.015 | 0.036 |
| 节点变形角 @ −0.03 rad | −0.018（C 点） | −0.035 |
| 节点变形角 @ −0.02 rad 附近 | −0.012（B 点，−0.022） | −0.021 |

结论：实体模型的节点在约 0.01–0.0125 rad 就剪切软化，承载力峰值来得太早，之后节点变形角约为试验的 2 倍；
试验到 0.026 rad 才达峰，节点变形角约为层间位移角的一半。实体节点偏弱。

注意未修正的差异：动力加载应变率、惯性和阻尼、加载幅值序列和圈数不同（地震动不规则）。

生成：`python 05_joint_models/comparison/code/python/plot_experiment_vs_model_joint_drift.py --model solid`（默认 origin_2015、standard）
