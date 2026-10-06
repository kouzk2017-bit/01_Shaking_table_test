# DIANA solid joint model results

`05_joint_models/diana_solid/` 实体节点模型自己的结果，只用实体的处理数据，不画壳模型和试验曲线。
跟试验的对比在 `../../comparison/test_vs_solid/`。

模型：梁端钢垫板 + 中高度 y 向线约束（铰支），100 mm 网格，total strain crack 混凝土，加载协议为标准
850 步（1–10 轴力，11–850 循环，层间位移角 = 荷载系数 × 0.005 rad）。

## 工况文件夹（名字跟 `diana_solid/data/processed/` 一致）

| 工况 | 改动 | 状态 |
|---|---|---|
| `origin_2015` | 基准：multi-linear 受压曲线，泊松比按损伤折减 | 850 步完成，第 111 步未收敛 |
| `origin_2015_nu_no_reduction` | 泊松比不折减 | 完成，第 106 步未收敛 |
| `origin_2015_parabolic` | 受压曲线改 parabolic | 中间导出约 260 步，第 163 步未收敛后承载力崩塌 |
| `origin_2015_parabolic_fine` | parabolic + 约 +0.0125 rad 起加密步长 | 约 250 步，第 170/171 步（+0.01625 rad）未收敛后崩塌 |
| `origin_2015_parabolic_history` | parabolic + 2015 4F 试验历程协议（`05_joint_models/loading_protocols/`） | 模型 `solid_BCJs - parabolic.dpf`，2026-10-02；第 124 步（+0.016 rad）未收敛，用户在第 137 步手动停止；只导出上柱剪力、角点位移、梁纵筋、整圈箍筋 |
| `origin_2015_parabolic_residual_history` | 同上 + 受压残余强度 9.6 MPa | 2026-10-02，415 步全部收敛，第 414 步手动停止（非不收敛）；导出齐全（无梁剪力） |
| `origin_2015_parabolic_gc61_residual_history` | 同上 + Gc 26.6 → 61 N/mm（Nakamura & Higai 8.8√fc） | 2026-10-02，到第 608 步全部收敛（导出到 607 步） |
| `origin_2015_parabolic_gc61_residual20_history` | 同上 + 残余强度 9.6 → 20 MPa | 2026-10-02，1119 步全部完成、全部收敛；箍筋只导出一半（x 肢 2663–2667、右 y 肢 2679–2684） |

每个工况的图（缺导出的跳过）：`01` 层剪力-层间位移角（上柱 e1783），`02` 层剪力-加载步，`03` 节点变形角-加载步，
`04` 节点变形角-层间位移角，`05` 节点箍筋 x 肢（10108/2665），`06` 节点箍筋 y 肢最大值（EYY，10122–10126），
`07` 右柱面旁梁纵筋（10403/2954），`08` 上梁面旁柱纵筋（11295/3839），`09`/`10` 梁/柱纵筋沿筋应变分布（各幅值首次峰值）。

`concrete_variants/`：四个工况叠在一起比较，见其中 README。

## 收尾状态（2026-10-06）

最终采用 `origin_2015_parabolic_gc61_residual20_history`（Gc 61 N/mm、残余抗压强度 20 MPa）。对比对象为试验节点 4（第 4 层顶部，JNT4），节点变形占比、层剪力、对角线膨胀与试验吻合；钢筋只比较屈服与否和时间。结论与局限见 `../../comparison/failure_mechanism/README.md`。

## 当前问题（历史记录）

`origin_2015_parabolic_gc61_residual20_history`（2026-10-03 整理）：大位移角正负向强度和节点变形占比都跟试验吻合（见对比 README）；
剩余差异：起始两个转折点偏刚偏强、小幅循环偏强，柱纵筋在梁面单元 8–12εy（试验约 5.4εy）。


`origin_2015_parabolic_gc61_residual_history`（2026-10-02）：正向 +0.028/+0.030 rad 层剪力 0.92/0.90 Vmax、节点占比 0.41/0.65，
跟试验（0.92/0.87、0.37/0.50）接近；负向 −0.022 rad 只有 0.67 Vmax（试验 0.88）。柱纵筋在梁面单元 10.7εy，偏大（试验约 5.4εy）。


`origin_2015_parabolic_residual_history`（2026-10-02）：残余强度 9.6 MPa 后 +0.016 rad 的骤降消失、全部收敛，梁纵筋屈服
（+0.028 rad 4.9εy），但 +0.019 rad 以后正向仍软化偏多（+0.030 rad 0.51 Vmax，试验 0.87），节点变形角占比 0.66–0.83
（试验 0.37–0.54）。详见 `../../comparison/test_vs_solid/2015_4F_history_protocol/origin_2015_parabolic_residual_history/`。

以下为此前的诊断：

`origin_2015_parabolic_history`（2026-10-02）：−0.0135 rad 转折点正常（峰值 −417 kN），正向到 +0.0155 rad
（第 123 步）366 kN、节点变形角 0.006；第 124 步（+0.016 rad，未收敛）一步之内层剪力 366 → 192 kN、节点变形角
0.006 → 0.0137，右柱面梁纵筋 1.07 → 0.35εy 卸载，之后层间位移几乎全部进入节点（+0.0215 rad 时节点 0.024）。
破坏前左柱面那一个梁筋单元（e2948，节点 10397 端）的压应变从 +0.0115 rad 的 −2.2εy 涨到 −6.9εy，同一单元另一端
却是 +1.2εy，说明压碎集中在柱面的一排单元里。

所有版本都在 +0.0125~+0.016 rad 附近柱面旁梁上下区混凝土压坏、承载力骤降；parabolic 版本的骤降
正好发生在未收敛步，分不清是物理破坏还是数值发散。下一步先解决收敛，再跑试验历程协议。

## 生成

```
python 05_joint_models/diana_solid/code/python/plot_solid_results.py --case origin_2015
python 05_joint_models/diana_solid/code/python/plot_solid_variant_comparison.py
```
