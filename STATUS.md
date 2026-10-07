# 01 RC 节点研究：现状（更新 2026-10-06）

**三个入口**：结果层 `06_results/`（只放最终版；每条曲线的节点/应变片见 `06_results/data_sources/`（表格图 PNG，内容在同名 CSV））｜汇报用图 `06_results/PPT_20261007/`｜本文件。
最终版登记在 `final_cases.json`；新增或重跑工况：`python 05_joint_models/update_case.py --model solid --case <工况> [--ppt]`。

## 下一步
1. ~~钢筋取点统一~~ 完成（10-07）：所有壳工况（标准/历程、楼板、j12、j16、v2018）统一取**右梁下筋柱面 + 上柱左筋梁面**（与试验 5G21-STR-E01 / 5F2AC-STR-02 同位置）；模型对模型用面上节点，对试验用距面 100 mm 节点。节点表见 `06_results/data_sources/`。箍筋取点尚未统一（各工况层位不同）。
   同位置首次屈服（标准协议）：origin 柱 +0.009 / 梁 −0.010；楼板 柱 +0.0085 / 梁 −0.014；j12_h、j12_m 同 origin（柱先）；j16_l、j16_m 梁柱同步（+0.011–0.0115）；**j16_h 梁先（−0.010）柱后（+0.011）；v2018 梁先（+0.0105）柱后（+0.012）**。→ 柱筋加到 16 根后屈服顺序向试验的"梁先"靠近。
2. 柱筋屈服顺序与试验不一致的原因：楼板已排除（同位置取点）；柱筋量影响明显（j16_h、v2018 梁先），剩余候选＝单节点边界（塑性无法向相邻楼层转移）、单元局部化与应变片位置。
3. 实体模型补"壳给不了"的图：箍筋沿高度分布（三层箍筋已导出）、平面外膨胀。
4. 以后：IMK 整体模型第 4 层提前倒塌的原因。

---

对象：2015 年 10 层试件中柱 2-A 节点。试验对比节点 = **节点 4**（第 4 层顶部，5F 楼板，位移计 JNT4）。

## A. 壳模型（辻的原始模型，`diana_shell/`）

| 工况 | 内容 | 加载 | 用途 | 状态 |
|---|---|---|---|---|
| `origin` | 2015 原设计（辻模型） | 标准协议 ±1/200…1/25 | 基准；破坏机理 | 完成 |
| `j12_h` `j12_m` `j16_l` `j16_m` `j16_h` | 柱纵筋 12/16 根 × 节点箍筋 L/M/H | 标准协议 | 防止方法（参数分析，模型对模型） | 完成，结果 `06_results/comparison/shell_variants/<工况>_vs_origin/` |
| `v2018` | 2018 试件 | 标准协议 | 防止方法：对照 2018 | 完成 |
| `origin_history` | origin + 试验历程协议 | 试验历程 | 与试验按时间对比 | 完成，`comparison/test_vs_shell/2015_4F_history_protocol/origin_history/` |
| `origin_history_slab` | 再加楼板等效翼缘 | 试验历程 | 检验楼板影响 | 已核对（γ/位移角可 >1，属正常）；梁柱近弹性、节点压溃；待标准协议重跑 |
| `origin_slab` | 同上楼板翼缘模型（同网格） | 标准协议 | 楼板影响（对 origin） | 完成，850 步全收敛；图 `06_results/comparison/shell_variants/origin_slab_vs_origin/`。Vmax +455/−441 kN（origin +392/−384，约 +15%）；同位置首次屈服（上柱左筋 1559 / 右梁下筋 1254）：柱 +0.0085（origin 1839 +0.009），梁 −0.014（origin 1628 −0.010），箍筋 +0.015（origin +0.013）→ **仍柱先梁后，楼板使梁筋屈服更晚（最大约 3εy）**；≥0.03 rad 节点角/位移角 0.9–1.2，箍筋 6–9εy，变形集中于节点 |
| `origin_2015_history_slab_jointflange_wrong` | 建错的楼板版本 | — | 无 | 可删除 |

## B. 实体模型（自建，`diana_solid/`）

| 工况 | 改动 | 结论 |
|---|---|---|
| `origin_2015` | 基准，标准协议 | +0.0125 rad 起节点软化 |
| `origin_2015_nu_no_reduction` | 泊松比不折减 | 更差，弃用 |
| `origin_2015_parabolic` / `_fine` | parabolic 受压 | +0.016 rad 不收敛骤降（与步长无关） |
| `origin_2015_parabolic_history` | + 试验历程协议 | 同上，第 124 步 |
| `origin_2015_parabolic_residual_history` | + 残余 9.6 MPa | 骤降消失，大位移角偏软 |
| `origin_2015_parabolic_gc61_residual_history` | + Gc 61 | 正向吻合，负向偏弱 |
| **`origin_2015_parabolic_gc61_residual20_history`** | + 残余 20 MPa | **最终版**，正负向吻合 |

结果层只留 `origin_2015` 和最终版（`06_results/diana/solid/`、`comparison/test_vs_solid/`）；其余中间工况在 `06_results/archive/2026-10-06_intermediate_cases/`。

## C. 试验数据

节点 3/4/6：`06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/`（`02_10-story_2015/code/python/process_joint_data.py`）；
通道与楼层对应：`02_10-story_2015/REBAR_GAUGES.md` 第 5 节。

## D. 结论文档

- 破坏机理（试验 vs 壳 vs 实体）：`06_results/comparison/failure_mechanism/README.md`
- 壳 vs 实体直接对比：暂停（壳模型定稿后再做），旧图在 `06_results/archive/2026-10-01_shell_vs_solid_preliminary/`

## 论文结构对应

1. 试验：节点 4 的破坏特征（C）
2. 壳模型重现 + 防止方法参数分析（A：origin、j*、v2018）
3. 实体模型：参数依据与调整过程（B）
4. 三者破坏机理对比与局限（D）
5. 楼板影响（`origin_slab`、`origin_history_slab`）：强度 +15%，柱先梁后不变；今后：整体模型
