# 10-story 2015 Known Issues

## ISSUE-001：钢筋应变工作流仅覆盖指定正式加载工况

- 状态：设计限制
- 现象：`Rebar_Strain.m` 的 `kList` 固定为 `[2, 4, 7, 10, 13, 15, 17, 20]`。
- 影响：其他工况不会由该入口自动处理。
- 后续条件：扩展工况前需确认 JB04、JB05、JB06、JB16 通道布局及残余应变继承关系。

## ISSUE-002：4F 梁筋选用通道原为角柱节点（2026-10-01 已更正）

- 状态：已修复（有意偏离 MATLAB 原结果）
- 现象：`rebar_strain_selected.csv` 的 4F 梁筋原为索引 42（Col44 = 4G1A-STR-E01），位于 G1 东端，也就是**角柱**节点；
  6F 用的是中柱节点（6G21-STR-E01），两层选法不一致。
- 修复：改为索引 57（**Col59 = 4G2A-STR-E01**，中柱节点 G2 东端下筋）。重跑了工况 13、20 的钢筋应变，并重新生成 4F 应变图。
- 影响：与 MATLAB ExternalStrain 表比对时第一列不一致；2026-10-01 以前的 4F 梁筋图、数据（以及日文论文图 3(a) 的 4F 梁筋）来自角柱节点。
- 依据与完整的通道对应：`REBAR_GAUGES.md`。

## 非阻塞代码检查项

MATLAB R2026a 静态检查共报告 23 条既有提示；`project_config.m`、`plot_rebar_strain_results.m`、`Fn_Resampling.m` 和 `function_gosa.m` 无提示。路径重构阶段未修改信号处理、人工修正或残余量继承算法。

- `XLSRD`：`Acceleration_ShearForce.m:13`、`Displacement.m:13`、`Displacement_foundation.m:18`、`Joint_Rad.m:13`、`Rebar_Strain.m:81` 使用旧式 `xlsread`。
- `SAGROW`：`Acceleration_ShearForce.m:42`、`Displacement.m:42`、`Joint_Rad.m:42`，以及 `Displacement_foundation.m:88–131` 的 10 处循环内动态扩展数组。
- `Fn_filtering.m:69`：`NODEF`，变量可能在定义前使用。
- `Displacement_foundation.m:162`：`UNRCH`，存在不可达语句。
- `Joint_Rad.m:26`：`NBRAK2`，存在不必要的方括号。
- `Rebar_Strain.m:730`：`DEFNU`，局部函数可能未使用；`Rebar_Strain.m:795` 为代码分析器隐藏消息提示。

## ISSUE-002：旧 MATLAB 目录暂留两个被占用副本

- 状态：已解决（2026-07-29）
- 原文件：`matlab/PLOTTING_WORKFLOW.md`、`matlab/plot_rebar_strain_results.m`
- 核对结果：说明文件与新位置版本 SHA-256 相同；旧成图脚本仍使用迁移前的 `ExcelData` 路径，新版本已改用 `project_config()`。
- 处理：为保留迁移历史，旧目录整体移入 `09_legacy/migration_residue/10_story_2015_matlab_pre_migration/`，未直接删除。
- 验证：正式入口仍位于 `code/matlab/`，`data/raw/` 未发生变化。
