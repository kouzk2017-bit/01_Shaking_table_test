# 01 RC 节点研究：现状（更新 2026-10-06）

**三个入口**：结果层 `06_results/`（只放最终版；每条曲线的节点/应变片见 `06_results/data_sources/`（表格图 PNG，内容在同名 CSV））｜汇报用图 `06_results/PPT_20261007/`｜本文件。
最终版登记在 `final_cases.json`；新增或重跑工况：`python 05_joint_models/update_case.py --model solid --case <工况> [--ppt]`。

## 下一步
1. ~~钢筋取点统一~~ 完成（10-07）：所有壳工况（标准/历程、楼板、j12、j16、v2018）统一取**右梁下筋柱面 + 上柱左筋梁面**（与试验 5G21-STR-E01 / 5F2AC-STR-02 同位置）；模型对模型用面上节点，对试验用距面 100 mm 节点。节点表见 `06_results/data_sources/`。箍筋取点尚未统一（各工况层位不同）。
   同位置首次**受拉**屈服（标准协议，10-08 更正：此前把受压屈服也算进去）：origin 柱 +0.009 / 右梁 +0.014；J12 同 origin；J16-L、J16-M 梁柱同时（+0.011–0.0115）；J16-H 柱 +0.011 / 梁 +0.012（几乎同时）；v2018 梁 +0.0105 / 柱 +0.012（梁先）。
2. 屈服顺序（10-08 同位置、只算受拉重新对比，见破坏机理 README 第 1 节）：正向顺序三者一致；差别在第一次大幅负向——试验只有左梁下筋屈服（7.5εy），模型上柱右筋、下柱左筋也同时屈服。旧结论"模型柱先、试验梁先"作废（模型取了任意柱面）。原因候选：试验左右梁端不对称（左 7.5εy、右 1.2εy）、单节点边界、楼板。
3. **钢筋对比按方向分两组（10-09）**：负向 = 左梁下筋 5G11-W01 + 上柱右筋 5F2AC-09；正向 = 右梁下筋 5G21-E01 + 上柱左筋 5F2AC-02（节点 3 对应 4G1A-W02、4F2AC-09、4G2A-E01、4F2AC-02）。试验图、壳/实体历程对比、PPT 已按此改。负向组 10-09 已补齐：J12、J16、v2018、楼板（标准/历程）、实体 origin_2015 左柱；壳 origin 标准协议也已补齐（1623/1979），**所有工况四个位置齐全**。参数分析和楼板图已改为按方向四个位置 + 按方向的首次屈服（`shell_variants/all_variants/`、`slab_vs_origin_skeleton/`）。
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
| `joint3` | 节点 3 壳模型，真实配筋，轴力 343/393 kN，8 节点（`model/JNT3.dpf`，10-10 重算） | 标准协议 | 节点 3 vs 试验节点 3 | Vmax ±303 kN；**梁先屈服（±0.010），柱后（0.0165–0.0195）**，与试验节点 3 顺序一致；但节点变形占比仅 0.21–0.37（试验 0.39→0.75），滞回比试验饱满。图 `comparison/test_vs_shell/2015_3F_standard_protocol/joint3/`。4 节点旧结果在 raw/joint3_2015/superseded_4node（无效） |
| `beam_rebar` | origin + 真实梁配筋（±1000 mm 截断，左梁上筋少一根），轴力 243 kN，8 节点（`model/test.dpf`，10-10 重算） | 标准协议 | 真实配筋的影响（对 origin） | 与 origin 几乎相同：Vmax +395/−387；仍柱先（0.009），负向左梁屈服 0.018（origin 0.0155）。4 节点旧结果在 superseded_4node（无效） |
| `beam_rebar_free` | beam_rebar + 梁端轴向不约束（`model/test.dpf`，10-10 14:14–16:52，第 608 步 +0.039 未收敛、无跳动） | 标准协议 | 梁轴向约束的影响（对 beam_rebar） | Vmax +284/−293（−27%）；**梁先屈服** 0.0075，柱 0.022/0.029，与试验顺序一致；节点角/位移角 0.22–0.41（约束时 0.43–0.81）。图：shell_variants/beam_rebar_free_vs_beam_rebar、beam_axial_free_vs_restrained_skeleton |
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

**原始数据 → CSV**（Python，2026-07 起取代 MATLAB；MATLAB 原代码封存在 `09_legacy/matlab_archive/`）：
- 入口：`02_10-story_2015/code/python/run_pipeline.py`（2018：`03_10-story_2018/code/python/run_pipeline.py`），用法见各自 README。
- 两个试验的试验数据处理代码：`08_common/python/ten_story_pipeline.py`（2015、2018 用同一套算法，只是通道号和质量不同；平时不直接运行，由上面的入口调用）。
- 输出：`06_results/experiment/<年>/<工况>/csv/`——各层加速度、层剪力（`story_shear_x/y`，列 `nF_kN` = 第 n 层）、层间位移/位移角（`story_drift_x/y`）、节点变形角（`joint_rotation`）、钢筋应变等。节点模型的对比都读这里。
- **画图/对比脚本只通过 `02_10-story_2015/code/python/test_data.py` 读这些 CSV，不再读原始数据**（10-08 统一）。处理上的选择做成开关：`02_10-story_2015/config/test_data_options.json`
  - `rebar_include_previous_runs_residual`：钢筋应变是否带前几次加载的残余。10-08 定为 **false**：只分析最后一个工况、模型也不含前次损伤；Kang 图 16 也是这样处理的
  - `joint_angle_geometry` / `joint_diagonal_geometry`：节点变形角、对角线应变用的测量框，10-08 定为两者都用 Kang 的 270×270（对角线 381.8 mm）
- 流程的精选钢筋 `rebar_strain_selected.csv` 10-08 起是节点 4 的 4 个应变片（5G21-E01、5F2AC-02、5G11-W01、4F2AC-18），此前是错层的 4F/6F 楼板节点；2015 的这一项不再和 MATLAB 比对。
- 流程新增输出：`joint_diagonal_displacement.csv`（未滤波对角线位移）、`rebar_channel_map.csv`（CH 列 ↔ 应变片编号 ↔ 前次残余）。
- 2018 Kobe 100% 还没用 Python 重跑到当前目录（只有 `06_results/archive/2026-07-30_before_cleanup/` 里的旧版）。


节点 1–6（一个节点一个文件夹 `joint_<n>_JNT<n>/`，另有 `overview/`）：`06_results/experiment/2015/20151211-2(JMAKobe100%)/joints/`（`02_10-story_2015/code/python/process_joint_data.py`）；
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
