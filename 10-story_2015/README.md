# 10-story 2015 Shaking Table Project

本项目采用“只读原始数据、Python 计算、CSV 交换、CSV 绘图、历史结果验证”工作流。

## 目录

- `data/raw/`：原始仪器 CSV，只读。
- `code/python/`：正式 Raw Data → CSV → CSV 绘图入口。
- `../results/2015/<case>/`：当前工况图片，图片直接放在工况目录中。
- `../results/archive/2026-07-30_before_cleanup/2015/`：历史结果、MATLAB 工作簿和运行残留。
- `metadata/`：工况表、传感器表和迁移清单。
- `validation/baseline/`：历史迁移验证资料。

## 正式入口

```powershell
cd '<project>/10-story_2015/code/python'
python run_pipeline.py --list-cases
python run_pipeline.py --case 20
python run_pipeline.py --all-loading
python plot_from_csv.py --case 20
python run_pipeline.py --case 20 --then-plot
python validate_against_matlab.py --case 20
```

通常先运行 `run_pipeline.py` 生成计算 CSV。以后仅调整坐标轴、字体、颜色或
图片格式时，只修改共享的 `../common/config/plot_config.json` 并运行 `plot_from_csv.py`，不会重新读取
或计算 Raw Data。`csv/selected_peaks.csv` 保存 A--D 的时刻、响应值和占比。

流程覆盖楼层/台面/基础加速度、层剪力、层间与绝对位移、累计残余位移、
层间位移角、节点转角、基础滑移位移及八工况钢筋应变继承。

原 MATLAB 代码已移至 `legacy/matlab_archive/10-story_2015/`，不再是正式入口。
历史 MATLAB 结果已封存在 `../results/archive/2026-07-30_before_cleanup/2015/`，用于验证 Python 数值等价性。
