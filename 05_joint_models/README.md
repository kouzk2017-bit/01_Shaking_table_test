# Joint (BCJ) numerical models

梁柱节点局部数值模型，区别于试验目录（`01_4-story/`、`02_10-story_2015/`、`03_10-story_2018/`）和整体建筑
数值模型（`04_building_models/`）。

- `diana_shell/`：DIANA 层壳节点模型，代码见 `code/python/`，结果见 `../06_results/diana/shell/`。
- `diana_solid/`：DIANA 实体节点模型。
  - `model/`：模型本体和原生分析数据库（`.dpf`/`.dnb`/`.out`，`.dnb` 体积很大 ~15.8 GB），
    整个目录已被 `.gitignore` 排除。
  - `data/raw/`、`data/processed/`：跟 `diana_shell` 一样分导出的原始节点响应和标准化后的
    数据，按工况分子目录；`processed/` 目前是空目录，等处理脚本落地。
  - `code/`、`config/`：预留空目录，以后放处理脚本（对标 `diana_shell/code/python/`）。
  - 对比结果产出后放 `../06_results/diana/solid/`（与 `diana_shell` 同一约定）。
- `drawings/`：两个模型共用的节点详图（DWG），不纳入版本控制。
- `comparison/`：试验（动力时程）与节点数值模型（拟静力）的对比脚本，把两侧都转换成
  "节点变形角 vs 层间位移角" 的响应-响应曲线后叠加，绕开时程/加载步数无法对齐的问题；
  结果见 `../06_results/comparison/`。
