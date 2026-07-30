# 10-story 2018 Known Issues

## ISSUE-001：工况表与现有原始数据覆盖范围不同

- 状态：已记录，非迁移阻塞项
- 现象：`metadata/folder_list.xlsx` 包含 27 行工况，但现有原始数据只覆盖其中 10 个正式试验目录；白噪声、平衡及部分工况没有对应原始 CSV。
- 影响：不能假定工况表中的每一行均可直接重算。
- 当前处理：以原始文件完整的第 20 行 `20190109-2(JMAKobe100%)` 作为迁移基准。
- 后续条件：新增其他基准前，逐工况核对所需 JB 文件是否齐全。

## ISSUE-002：Python 工作流目前仅配置 Case 20

- 状态：设计限制
- 现象：`code/python/config.py` 固定配置第 20 工况。
- 影响：其他工况不能通过同一入口直接批处理。
- 后续条件：需要批量处理时，将工况参数从模块常量提升为显式命令行参数，并为每个工况建立输入完整性检查。

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
