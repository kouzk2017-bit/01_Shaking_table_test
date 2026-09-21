# Joint (BCJ) numerical models

梁柱节点局部数值模型，区别于试验目录（`01_4-story/`、`02_10-story_2015/`、`03_10-story_2018/`）和整体建筑
数值模型（`04_building_models/`）。

- `diana_shell/`：DIANA 层壳节点模型，代码见 `code/python/`，结果见 `../06_results/diana/shell/`。
- `diana_solid/`：DIANA 实体节点模型，原始产出见 `data/raw/`（`.dpf`/`.dnb`/`.out`，`.dnb` 体积很大，
  已被 `.gitignore` 的 `**/data/` 规则排除），`code/`、`config/` 为预留空目录；对比结果产出后放
  `../06_results/diana/solid/`（与 `diana_shell` 同一约定）。
- `drawings/`：两个模型共用的节点详图（DWG），不纳入版本控制。
