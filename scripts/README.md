# Scripts

- `figure_export/`：历史工作簿交付图片入口，仅用于复现既有交付物。
- `figure_export/regenerate_current_figures.py`：从日期归档中的计算数据重绘当前
  2015/2018 工况图片，不把 CSV、NPZ 或元数据复制回活动结果目录。
- `deprecated/`：已失去必要依赖、不可直接运行的旧入口，仅供追溯。

2015、2018 十层试验的新成图入口位于各项目的 `code/python/run_pipeline.py --plot`，
只读取顶层 `results/<year>/<case>/csv/`，不再读取 Excel；图片直接输出到工况目录。
图片默认调用工作区 `common/python/publication_style.py` 中的 `paper` 样式；画布、
字体、字号、色板、线宽、坐标轴、刻度、网格、图例以及 600 dpi PNG/矢量 PDF
输出均由该公共代码统一管理。

新增脚本应通过脚本位置推导工作区根目录，避免写死用户目录或旧 `lab` 路径。
