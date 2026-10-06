# Results

先看各模型自己的结果，再看模型跟试验的对比。结果层只放最终版（`../final_cases.json`），中间工况在 `archive/`；汇报用图在 `PPT_<日期>/`。

- `experiment/2015/<case>/`、`experiment/2018/<case>/`：2015、2018 两套十层振动台试验的当前图片，年份下一级直接是工况，图片直接放在工况目录中。每幅保存为 600 dpi PNG。分析程序从 `02_10-story_2015/` 和 `03_10-story_2018/` 中的只读原始数据读取输入。
- `diana/shell/`：`05_joint_models/diana_shell/` 层壳节点模型的结果包（每个 `*_comparison/` 是一个变体对 origin 的完整结果包，含 `curve-source-registry.csv`）。
- `diana/solid/`：`05_joint_models/diana_solid/` 实体节点模型自己的结果，每个工况一个文件夹（名字跟 `data/processed/` 一致），另有 `concrete_variants/` 比较实体的混凝土设置。只用实体自己的数据，不画壳和试验。
- `loading_protocols/`：按试验实测层间位移角历程生成的 DIANA 加载协议检查图（协议文件在 `05_joint_models/loading_protocols/`）。
- `comparison/`：模型 vs 试验，按模型分 `test_vs_shell/`、`test_vs_solid/`，下一级是试验工况和加载协议。层壳 vs 实体暂停（壳模型仍在调整），见 `comparison/README.md`。
- `opensees/`：`04_opensees_model/` 整体模型的结果，每个阶段一个固定文件夹：`model_info/`、`modal/`、`trial_case<N>_<T>s/`。重跑成功时覆盖；失败时另存为 `<名称>__failed/`。
- `archive/`：日期化归档。`2026-10-01_shell_vs_solid_preliminary/` 是 2026-09 的层壳 vs 实体对比（壳模型定稿前，仅留档）。
