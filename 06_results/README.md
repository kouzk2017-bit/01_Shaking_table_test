# Results

按来源分四类：试验结果（`experiment/`）、DIANA 节点模型结果（`diana/`）、OpenSees 整体模型结果（`opensees/`）、
跨模型/跨试验对比（`comparison/`）。

- `experiment/2015/<case>/`、`experiment/2018/<case>/`：2015、2018 两套十层振动台试验的当前图片，年份下一级直接是工况，图片直接放在工况目录中。每幅保存为 600 dpi PNG；不含 CSV、工作簿或运行中间文件。分析程序仍从 `02_10-story_2015/` 和 `03_10-story_2018/` 中的只读原始数据读取输入。
- `diana/shell/`：`05_joint_models/diana_shell/` 层壳节点模型的对比结果包（每个 `*_comparison/` 目录是一个变体的完整结果包，含 `curve-source-registry.csv`）。
- `diana/solid/`：预留给 `05_joint_models/diana_solid/` 实体节点模型自身的工况对比，尚无产出。
- `opensees/10story_2015/`：`04_building_models/opensees_10story_2015/` 整体模型每次运行的独立结果目录（按 UTC 时间戳命名），含参数快照、源码快照、求解日志和状态；不覆盖旧运行。
- `comparison/`：`05_joint_models/comparison/` 脚本产出的跨模型/跨试验对比图（试验 vs 节点模型、层壳 vs 实体节点模型）。
- `archive/`：整理前的全部历史结果、CSV、工作簿、旧图和运行文件的日期化归档。
