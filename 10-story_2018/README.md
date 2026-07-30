# 10-story 2018 Shaking Table Project

本项目采用与 `4-story` 试点一致的“原始数据、处理数据、代码、结果、元数据、文档、验证”分离结构。迁移只改变文件位置和路径配置，不改变原始测量内容或计算方法。

## 目录

- `data/raw/`：原始仪器 CSV，只读。
- `data/processed/text/`：MATLAB 提取的通道文本。
- `code/matlab/`：原 MATLAB 分析脚本和统一路径配置。
- `code/python/`：Case 20 Python 处理链和统一路径配置。
- `results/matlab/spreadsheets/`：MATLAB 分析工作簿。
- `results/python/`：Python 数值、表格、工作簿、成图和历史预览。
- `results/runtime/matlab/`：MATLAB 跨工况状态；可再生 Python 字节码缓存已清理。
- `metadata/`：工况表和迁移清单。
- `documents/test_information/`：试验管理资料、传感器资料和参考文档。
- `validation/baseline/`：迁移前后 Case 20 数值摘要及比较结果。

## 路径配置

MATLAB 脚本通过 `code/matlab/project_config.m` 获取项目路径；Python 处理链通过 `code/python/config.py` 获取项目路径。运行时不再依赖旧目录名 `00_testdata`、`Txt`、`ExcelData` 或 `python_results`。

## 基准工况

- 工况索引：`k = 20`
- 工况：`20190109-2(JMAKobe100%)`
- Python 入口：`code/python/run_case20.py`
- 验证范围：6 个核心 NPZ 中的全部数组，以及 15 个 CSV 表格。

运行方式：

```powershell
cd '<project>/10-story_2018/code/python'
python run_case20.py
```

已知限制和后续处理条件记录在 `ISSUES.md`。

## 可追溯性

`metadata/migration_manifest.xlsx` 记录每个原有文件的源路径、目标路径、大小和 SHA-256。全部原有文件在修改路径配置前进行逐文件校验。
