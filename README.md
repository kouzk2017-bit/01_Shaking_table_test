# Shaking Table Test Workspace

本目录用于管理 4 层与 10 层振动台试验数据、分析代码、前人资料，以及由此延伸的数值模型
（整体建筑 OpenSees 模型、节点局部 DIANA 模型）和最终成果。顶层子文件夹按"试验→数值模型→
结果→工具→前人资料"的顺序编号，方便查找。

## 当前结构

按"试验数据"与"数值模型"分开组织：

- `01_4-story/`：4 层试验正式工作目录，已完成配置化迁移和节点转角基准验证。
- `02_10-story_2015/`：2015 年 10 层试验正式 Python 工作目录，Raw Data 直接生成 CSV 并由 CSV 绘图。只含试验数据处理，不含数值模型。
- `03_10-story_2018/`：2018 年 10 层试验正式 Python 工作目录，支持现存加载工况批处理。
- 以上三个试验目录结构已固定（除内部 ISSUES.md 记录的数据缺失问题外），不再做结构性改动。
- `04_building_models/opensees_10story_2015/`：2015 十层试件的整体 OpenSees 数值模型（原嵌在
  `02_10-story_2015/opensees/` 内，2026-09-21 抽出独立存放）；仍从 `02_10-story_2015/data/raw/`
  读取台面实测输入。
- `05_joint_models/`：节点（梁柱节点）局部数值模型。
  - `diana_shell/`：DIANA 层壳节点模型的代码、配置与数据（原顶层 `diana/`）。
  - `diana_solid/`：DIANA 实体节点模型（原顶层 `solid_BCJs/`），原始产出在 `data/raw/`；
    `code/`、`config/` 为预留空目录。
  - `drawings/`：节点详图等 DWG 图纸（原顶层 `drawings/`）。
- `06_results/`：
  - `experiment/2015/`、`experiment/2018/`：试验当前图片，按年份和工况组织。
  - `diana/shell/`、`diana/solid/`：DIANA 层壳/实体节点模型的对比结果。
  - `opensees/10story_2015/`：整体 OpenSees 模型每次运行的独立结果目录。
  - `archive/`：整理前结果、历史基准和中间文件的日期化归档。
- `07_scripts/`：成果生成与维护脚本。
- `08_common/`：跨项目共用函数（绘图风格、MATLAB 基准比对等）。
- `09_legacy/`：从原 `lab` 整理出的前人代码、模型、文档和精选结果。

## 工作原则

1. 正式试验目录中的 `data/raw/` 视为只读原始数据；它们由迁移前的 `00_testdata` 建立而来。
2. `data/processed/` 和顶层 `06_results/` 属于处理结果，可由代码重新生成时不应作为唯一数据源。
3. 试验结果、DIANA 节点模型结果、OpenSees 整体模型结果分别放在 `06_results/experiment/`、
   `06_results/diana/`、`06_results/opensees/` 下；最终工作簿和成图放在各年份的 `deliverables/` 子目录。
4. 前人资料统一放在 `09_legacy/`，不保证迁移后可直接运行。
5. 正式试验目录按项目逐个迁移；移动前建立数值基准，移动后通过统一路径配置重跑并验证等价性。
   三个试验目录迁移完成后即视为冻结，后续新增的数值模型一律放在 `04_building_models/` 或
   `05_joint_models/` 下，不再嵌入试验目录内部。

## 项目迁移状态

- `01_4-story/README.md`：目录结构、运行入口和验证说明。
- `01_4-story/ISSUES.md`：缺失输入及无效默认工况等已知问题。
- `03_10-story_2018/README.md`：目录结构、Case 20 入口和验证说明。
- `03_10-story_2018/ISSUES.md`：工况覆盖范围、单工况 Python 配置及旧空目录占用问题。
- `02_10-story_2015/README.md`：目录结构、Case 22 入口和验证说明。
- `02_10-story_2015/ISSUES.md`：钢筋应变工作流限制、静态检查项及两个被占用旧副本。

三个正式试验项目均已完成迁移和代表性基准验证。

2026-07-30 已将 2015、2018 两套活动 MATLAB 代码封存至
`09_legacy/matlab_archive/`。历史 MATLAB 结果保留为 Python 数值基准；正式工作流不再依赖 MATLAB 或手工 Excel 中间处理。两个项目的 `data/raw/` 保持只读且未发生变化。

## 当前脚本入口

- `07_scripts/figure_export/export_10_story_figures.py`
- `07_scripts/figure_export/plot_excel_charts.py`

旧 PowerPoint 构建入口依赖已经清理的临时文件，已放入
`07_scripts/deprecated/`，仅供追溯。
