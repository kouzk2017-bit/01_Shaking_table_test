# 10-story 2018 Known Issues

## ISSUE-001：工况表与现有原始数据覆盖范围不同

- 状态：已记录，非迁移阻塞项
- 现象：`metadata/folder_list.xlsx` 包含 27 行工况，但现有原始数据只覆盖其中 10 个正式试验目录；白噪声、平衡及部分工况没有对应原始 CSV。
- 影响：不能假定工况表中的每一行均可直接重算。
- 当前处理：以原始文件完整的第 20 行 `20190109-2(JMAKobe100%)` 作为迁移基准。
- 后续条件：新增其他基准前，逐工况核对所需 JB 文件是否齐全。

## ISSUE-002：旧 Python 工作流仅配置 Case 20

- 状态：已解决（2026-07-30）
- 处理：新增 `code/python/run_pipeline.py`，支持按工况、全部加载工况和全部现存工况运行，并在运行前检查 JB 文件。
- 说明：旧 `run_case20.py` 暂时保留用于追溯，不再是正式入口。

## ISSUE-004：Case 20 历史累积位移使用旧残余状态

- 状态：已记录
- 现象：历史 MATLAB 工作簿的当前工况位移与当前算法一致，但累计工作表加载的 `residual_disp_7.mat` 从首个加载工况起便与当前算法从 Raw Data 重算的状态不同。
- 当前处理：Python 确定性计算逐项对照 MATLAB；累计位移从 Raw Data 按加载顺序重新建立，并在 `validation_against_matlab.json` 中单独标记历史状态差异。

## ISSUE-005：Case 20 以前的位移工作簿属于旧算法版本

- 状态：已记录
- 现象：Case 2 等较早历史 `Drift_Results_*.xlsx` 与当前封存 MATLAB 的通道组合均不一致；它们早于 Case 20 等价基准，不能作为当前算法的严格数值基准。
- 当前处理：批处理统一按封存 MATLAB 源码从 Raw Data 重算；Case 20 作为当前算法的正式确定性基准，旧工作簿继续保留用于版本追溯。

## 非阻塞代码检查项

MATLAB R2026a 静态检查共报告 8 条既有提示；`project_config.m` 无提示。本次迁移仅统一路径，不改变这些算法：

- `Displacement.m:13`、`Joint_Rad.m:13`、`Rebar_Strain.m:13`：`XLSRD`，建议将旧式 `xlsread` 改为 `readtable`、`readmatrix` 或 `readcell`。
- `Displacement.m:40`、`Joint_Rad.m:40`、`Rebar_Strain.m:40`：`SAGROW`，循环内动态扩展数组，可在性能维护阶段预分配。
- `Fn_filtering.m:69`：`NODEF`，变量可能在定义前使用，后续修改前应建立针对该函数的单元基准。
- `Joint_Rad.m:24`：`NBRAK2`，存在不必要的方括号。

Python README 已列出 Case 20 继承的人工修正规则。

## ISSUE-003：旧 MATLAB 空目录暂时被占用

- 状态：已解决（2026-07-29）
- 原现象：所有文件已经迁入 `code/matlab/`，但旧的空 `matlab/` 目录曾被 MATLAB 会话占用。
- 处理：确认无 MATLAB 进程且目录为空后移除旧目录；同时删除 13 个均有对应 `.py` 源文件的可再生 `.pyc` 缓存。
- 验证：`data/raw/` 的文件数量和总字节数保持不变。
