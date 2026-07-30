# 10-story 2015 Known Issues

## ISSUE-001：钢筋应变工作流仅覆盖指定正式加载工况

- 状态：设计限制
- 现象：`Rebar_Strain.m` 的 `kList` 固定为 `[2, 4, 7, 10, 13, 15, 17, 20]`。
- 影响：其他工况不会由该入口自动处理。
- 后续条件：扩展工况前需确认 JB04、JB05、JB06、JB16 通道布局及残余应变继承关系。

## ISSUE-002：钢筋应变成图依赖项目外公共代码

- 状态：已知依赖
- 现象：`plot_rebar_strain_results.m` 使用 `03_Common_Code/plotting/matlab/plot_style.m`。
- 影响：计算结果不受影响，但独立复制本项目时成图入口可能缺少依赖。
- 后续条件：需要独立分发时，将公共绘图依赖作为明确环境要求或打包副本。

## 非阻塞代码检查项

MATLAB R2026a 静态检查共报告 23 条既有提示；`project_config.m`、`plot_rebar_strain_results.m`、`Fn_Resampling.m` 和 `function_gosa.m` 无提示。路径重构阶段未修改信号处理、人工修正或残余量继承算法。

- `XLSRD`：`Acceleration_ShearForce.m:13`、`Displacement.m:13`、`Displacement_foundation.m:18`、`Joint_Rad.m:13`、`Rebar_Strain.m:81` 使用旧式 `xlsread`。
- `SAGROW`：`Acceleration_ShearForce.m:42`、`Displacement.m:42`、`Joint_Rad.m:42`，以及 `Displacement_foundation.m:88–131` 的 10 处循环内动态扩展数组。
- `Fn_filtering.m:69`：`NODEF`，变量可能在定义前使用。
- `Displacement_foundation.m:162`：`UNRCH`，存在不可达语句。
- `Joint_Rad.m:26`：`NBRAK2`，存在不必要的方括号。
- `Rebar_Strain.m:730`：`DEFNU`，局部函数可能未使用；`Rebar_Strain.m:795` 为代码分析器隐藏消息提示。

## ISSUE-003：旧 MATLAB 目录暂留两个被占用副本

- 状态：已解决（2026-07-29）
- 原文件：`matlab/PLOTTING_WORKFLOW.md`、`matlab/plot_rebar_strain_results.m`
- 核对结果：说明文件与新位置版本 SHA-256 相同；旧成图脚本仍使用迁移前的 `ExcelData` 路径，新版本已改用 `project_config()`。
- 处理：为保留迁移历史，旧目录整体移入 `legacy/migration_residue/10_story_2015_matlab_pre_migration/`，未直接删除。
- 验证：正式入口仍位于 `code/matlab/`，`data/raw/` 未发生变化。
