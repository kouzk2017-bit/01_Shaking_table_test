# 4-story Shaking Table Project

本项目已作为正式目录迁移试点，采用“原始数据、处理数据、代码、结果、元数据、
文档、验证”分离的结构。迁移只改变文件位置和路径配置，不改变原始测量内容。

## 目录

- `data/raw/`：原始仪器 CSV，只读。
- `data/processed/text/`：从原始 CSV 提取的通道文本。
- `code/matlab/`：MATLAB 分析脚本和统一路径配置。
- `results/spreadsheets/`：分析工作簿。
- `results/figures/`：脚本生成的图片。
- `results/runtime/data_loop/`：残余位移等跨工况运行状态。
- `metadata/`：工况表、传感器表和迁移清单。
- `documents/`：测量资料和参考文献。
- `validation/baseline/`：迁移前后基准数值与对比结果。

## 路径配置

所有 MATLAB 脚本通过 `code/matlab/project_config.m` 获取项目路径，不再依赖
当前工作目录，也不再写死 `00_testdata`、`Txt` 或 `ExcelData`。

## 已验证基准

- 脚本：`Joint_Rad.m`
- 工况索引：`k = 14`
- 工况：`20101217-4(JRTakatori60%)`
- 输入：JB4 原始 CSV
- 输出：`results/spreadsheets/Joint_20101217-4(JRTakatori60%).xlsx`
- 验证内容：完整 5,123 × 5 节点转角矩阵、时间向量和摘要峰值。

从 MATLAB 运行：

```matlab
cd('<project>/4-story/code/matlab')
Joint_Rad
```

## 当前脚本状态

- `Joint_Rad.m`：已完成迁移前后数值等价验证。
- `Acceleration_ShearForce.m`：路径已迁移；当前保留的原始文件不包含脚本要求的
  JB13–JB15 数据，因此未作为运行基准。
- `Displacement.m`：路径已迁移；脚本当前设置 `k = 22`，超过工况表的 15 行，
  需要先选择有效工况后才能运行。

上述问题及后续处理条件统一记录在 `ISSUES.md`。

## 可追溯性

`metadata/migration_manifest.xlsx` 记录迁移前的源路径、迁移后的目标路径、文件
大小和 SHA-256。清单中的 392 个原有文件均在修改代码路径前完成逐文件校验。
