# 01 RC 节点研究：现状（更新 2026-10-06）

**三个入口**：结果层 `06_results/`（只放最终版）｜汇报用图 `06_results/PPT_20261006/`｜本文件。
最终版登记在 `final_cases.json`；新增或重跑工况：`python 05_joint_models/update_case.py --model solid --case <工况> [--ppt]`。

## 下一步
1. 楼板壳模型用标准协议重跑（导出到 `05_joint_models/diana_shell/data/raw/origin_2015_slab/`，导出整根梁/柱筋和全部箍筋），登记后并入参数分析。
2. 柱筋屈服顺序与试验不一致的原因（候选：楼板、单节点边界）——楼板结果出来后再看。
3. 实体模型补"壳给不了"的图：箍筋沿高度分布（三层箍筋已导出）、平面外膨胀。
4. 以后：IMK 整体模型第 4 层提前倒塌的原因。

---

对象：2015 年 10 层试件中柱 2-A 节点。试验对比节点 = **节点 4**（第 4 层顶部，5F 楼板，位移计 JNT4）。

## A. 壳模型（辻的原始模型，`diana_shell/`）

| 工况 | 内容 | 加载 | 用途 | 状态 |
|---|---|---|---|---|
| `origin` | 2015 原设计（辻模型） | 标准协议 ±1/200…1/25 | 基准；破坏机理 | 完成 |
| `j12_h` `j12_m` `j16_l` `j16_m` `j16_h` | 柱纵筋 12/16 根 × 节点箍筋 L/M/H | 标准协议 | 防止方法（参数分析，模型对模型） | 完成，结果 `06_results/diana/shell/*_comparison/` |
| `v2018` | 2018 试件 | 标准协议 | 防止方法：对照 2018 | 完成 |
| `origin_history` | origin + 试验历程协议 | 试验历程 | 与试验按时间对比 | 完成，`comparison/test_vs_shell/2015_4F_history_protocol/` |
| `origin_history_slab` | 再加楼板等效翼缘 | 试验历程 | 检验楼板影响 | 已核对（γ/位移角可 >1，属正常）；梁柱近弹性、节点压溃；待标准协议重跑 |
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
5. 今后：楼板（`origin_history_slab`）、整体模型
