# 10-story 2015 Shaking Table Project

本项目采用“原始数据、处理数据、代码、结果、元数据、文档、验证”分离结构。迁移只改变文件位置和路径配置，不改变原始测量内容或计算方法。

## 目录

- `data/raw/`：原始仪器 CSV，只读。
- `data/processed/text/`：MATLAB 提取的通道文本。
- `code/matlab/`：MATLAB 分析和成图脚本，以及统一路径配置。
- `results/spreadsheets/`：分析工作簿和钢筋应变状态文件。
- `results/figures/`：历史图片及脚本生成的图片。
- `results/runtime/data_loop/`：跨工况残余位移状态。
- `metadata/`：工况表、传感器表和迁移清单。
- `documents/specimen_information/`：试件信息、图纸及相关文档。
- `documents/measurement/`：测量位置备忘资料。
- `validation/baseline/`：迁移前后基准数值及比较结果。

## 路径配置

所有 MATLAB 脚本通过 `code/matlab/project_config.m` 获取项目路径，不再依赖当前工作目录或旧目录名 `00_testdata`、`Txt`、`Images` 和 `ExcelData`。

## 基准工况

- 脚本：`Joint_Rad.m`
- 工况索引：`k = 22`
- 工况：`20151211-4(JMAKobe60%)`
- 输入：JB11 原始 CSV
- 验证范围：完整 5,630 × 5 节点转角矩阵和时间向量。

运行方式：

```matlab
cd('<project>/10-story_2015/code/matlab')
Joint_Rad
```

已知限制和后续处理条件记录在 `ISSUES.md`。

## 可追溯性

`metadata/migration_manifest.xlsx` 记录每个原有文件的源路径、目标路径、大小和 SHA-256。全部原有文件在修改路径配置前进行逐文件校验。
