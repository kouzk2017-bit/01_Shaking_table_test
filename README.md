# Shaking Table Test Workspace

本目录用于管理 4 层与 10 层振动台试验数据、分析代码、前人资料和最终成果。

## 当前结构

- `10-story_2015/`：2015 年 10 层试验正式工作目录，已完成配置化迁移和节点转角基准验证。
- `10-story_2018/`：2018 年 10 层试验正式工作目录，已完成配置化迁移和 Case 20 等价验证。
- `4-story/`：4 层试验正式工作目录，已完成配置化迁移和节点转角基准验证。
- `legacy/`：从原 `lab` 整理出的前人代码、模型、文档和精选结果。
- `deliverables/`：工作簿、成图和演示文稿等最终成果。
- `scripts/`：成果生成与维护脚本。
- `drawings/`：DWG 等图纸。
- `common/`：计划用于存放跨项目共用函数；当前仅建立框架。

## 工作原则

1. 正式试验目录中的 `data/raw/` 视为只读原始数据；它们由迁移前的 `00_testdata` 建立而来。
2. `data/processed/` 和 `results/` 属于处理结果，可由代码重新生成时不应作为唯一数据源。
3. 最终工作簿和成图统一放在 `deliverables/`。
4. 前人资料统一放在 `legacy/`，不保证迁移后可直接运行。
5. 正式试验目录按项目逐个迁移；移动前建立数值基准，移动后通过统一路径配置重跑并验证等价性。

## 项目迁移状态

- `4-story/README.md`：目录结构、运行入口和验证说明。
- `4-story/ISSUES.md`：缺失输入及无效默认工况等已知问题。
- `10-story_2018/README.md`：目录结构、Case 20 入口和验证说明。
- `10-story_2018/ISSUES.md`：工况覆盖范围、单工况 Python 配置及旧空目录占用问题。
- `10-story_2015/README.md`：目录结构、Case 22 入口和验证说明。
- `10-story_2015/ISSUES.md`：钢筋应变工作流限制、静态检查项及两个被占用旧副本。

三个正式试验项目均已完成迁移和代表性基准验证。

2026-07-29 已完成迁移残留收口：2015 旧 MATLAB 路径版本移入
`legacy/migration_residue/`，2018 旧空目录和可再生 Python 字节码缓存已清理。
三个项目的 `data/raw/` 未发生变化。

## 当前脚本入口

- `scripts/figure_export/export_10_story_figures.py`
- `scripts/figure_export/plot_excel_charts.py`

旧 PowerPoint 构建入口依赖已经清理的临时文件，已放入
`scripts/deprecated/`，仅供追溯。
