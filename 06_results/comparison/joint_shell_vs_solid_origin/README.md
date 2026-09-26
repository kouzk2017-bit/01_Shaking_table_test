# DIANA joint models: layered shell vs. solid, origin condition

层壳节点模型（`diana_shell`，工况 `origin`）与实体节点模型（`diana_solid`，工况 `origin_2015`）
的对比。两侧用同一套位移控制加载协议（850 步：1–10 轴力，11–850 循环，层间位移角 =
load factor × 0.005 rad），按加载步直接可比。节点面板 a=300 mm、b=366.67 mm。

## 模型版本（2026-09-25）

- 实体模型为**梁端铰支**版本：梁端加钢垫板，在垫板外侧面中高度沿 y 印刻一条线约束（对应壳模型
  三角垫块顶点约束）。此前梁端整面约束 xyz（固端）的旧模型及其原始导出已删除；旧模型让塑性集中到
  梁端头、不代表真实受力，结论作废。
- 第 111 步（−0.01 rad 峰值后）未收敛（200 次迭代），DIANA 继续计算；其余 849 步收敛。
- 节点变形角按对角线**长度变化**计算（跟试验位移计读数同一个量），见
  `diana_shell/code/python/calculate_joint_deformation_angle.py`。

## 结论

两个模型在 ±0.01 rad 以内基本一致；约 +0.0125 rad（第 155 步）起实体模型节点核心区剪切破坏、
承载力下降约一半，之后变形集中在节点。壳模型是梁、柱纵筋屈服、节点变形适中，跟试验 4F
（0.03 rad 时节点变形角约为层间位移角的 0.5–0.67，梁纵筋 4.65εy，柱纵筋 5.4εy）更接近，
实体模型的节点偏弱。两个模型唯一的材料/建模差别是混凝土受压性能：壳模型分层建模，箍筋内的
核心层用提高后的强度模拟约束增强，保护层用普通参数；实体模型全部用一种（无约束）混凝土参数。
节点剪切破坏由核心区斜压杆压溃控制，这很可能就是原因（待按壳的核心/保护层参数重算实体验证）。

| 层间位移角 | 层剪力 壳 (kN) | 层剪力 实体两根柱 (kN) | 节点变形角 壳 | 节点变形角 实体 |
|---|---|---|---|---|
| +0.01（第 70 步） | 379 | 357 / 373 | 0.0048 | 0.0047 |
| +0.02（第 170 步） | 384 | 235 / 183 | 0.0085 | 0.0198 |
| +0.03（第 350 步） | 331 | 187 / 160 | 0.0146 | 0.0363 |
| −0.03（第 470 步） | −362 | −123 / −202 | −0.0190 | −0.0350 |
| +0.04（第 610 步） | 326 | 167 / 163 | 0.0308 | 0.0501 |

峰值层剪力：壳 392 kN（第 156 步）；实体 357 / 373 kN（第 70 步，+0.01 rad）。
实体节点箍筋最大 12.5εy（壳 4.5εy）；实体梁纵筋最大 2.7εy、柱纵筋最大 2.6εy，都只出现在
柱面/梁面旁的一个单元上，离开节点的位置在第 155 步后随承载力下降而卸载。

## 图

- `01_joint_deformation_angle_by_step.png`：节点变形角。
- `02_joint_stirrup_strain_by_step.png`：节点箍筋（壳 2375 ↔ 实体 10108，两侧单元 2665/2666 都画）。
- `03_beam_longitudinal_strain_by_step.png`：梁纵筋（壳 1628 柱面；实体 10403 紧邻右柱面、10406
  离柱面 4 个单元）。
- `04_column_longitudinal_strain_by_step.png`：柱纵筋（壳 1985；实体 11295 紧邻节点、11292 离节点
  3 个单元）。
- `05_solid_beam_bar_strain_profile.png` / `06_solid_column_bar_strain_profile.png`：实体整根梁纵筋
  （10380–10419）、柱纵筋（11285–11312）在各幅值峰值时的沿筋分布。横轴是节点序号不是距离。
- `07_story_shear_by_step.png` / `08_story_shear_vs_story_drift.png`：层剪力。壳取 composed line
  NX（节点 524）；实体取两根柱 composed line 靠近钢板一段的 NX（单元 1764、1783）。梁端 x 也被约束，
  部分水平力进入梁轴力，所以两根柱剪力不完全相等。

实体测点对应关系（2026-09-26 用户确认）：柱面 梁 10397/10402、柱 11296/11302；箍筋 10108 ↔ 壳 2375。柱面旁第一个单元有压应变尖峰（梁 10397 单元 2948 约
−5~−7εy），是梁柱交界处的局部问题，所以曲线取紧邻的下一个节点。

## 生成

数据：`05_joint_models/diana_solid/code/python/prepare_rebar_response.py`（实体沿筋数据、层剪力）、
`diana_shell/code/python/calculate_joint_deformation_angle.py`（变形角）。图：
`05_joint_models/comparison/code/python/` 下的 `plot_shell_vs_solid_joint_deformation.py`（01）、
`plot_shell_vs_solid_rebar_strain.py`（02–04）、`plot_solid_beam_bar_strain_profile.py`（05–06）、
`plot_shell_vs_solid_story_shear.py`（07–08）。
