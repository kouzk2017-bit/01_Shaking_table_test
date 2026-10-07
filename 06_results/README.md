# Results

只放最终版（`../final_cases.json`）；中间工况在 `archive/`；汇报用图在 `PPT_<日期>/`。
**每条曲线出自哪个节点、哪个位置、哪个应变片：`data_sources/`。**

```
06_results/
├── data_sources/            数据来源表格图：01 钢筋应变、02 其他量、03 壳参数工况（改 CSV 后跑 plot_data_source_tables.py）
├── experiment/<年>/<工况>/   试验自身的图（2015、2018）
├── loading_protocols/        试验历程协议的检查图
├── diana/solid/<工况>/       实体模型自己的结果（只用实体数据）
├── comparison/               所有对比都在这里
│   ├── test_vs_shell/<试验>_<协议>/<工况>/     壳 vs 试验（origin、origin_history、origin_history_slab）
│   ├── test_vs_solid/<试验>_<协议>/<工况>/     实体 vs 试验
│   ├── shell_variants/<变体>_vs_<基准>/        壳工况之间（j12/j16 参数分析、v2018、楼板）
│   └── failure_mechanism/                      试验 vs 壳 vs 实体的破坏机理
├── opensees/                 整体模型（04_opensees_model）
├── PPT_<日期>/               汇报用图（07_scripts/presentation/collect_joint_figures.py 复制）
└── archive/                  日期化归档
```

规则：一个对比一个文件夹，文件夹名写清"谁 vs 谁"；壳 vs 实体暂停（壳模型定稿后放 `comparison/shell_vs_solid/`）。
- 实验图片 600 dpi PNG，从 `02_10-story_2015/`、`03_10-story_2018/` 的只读原始数据生成。
- `opensees/`：每个阶段一个固定文件夹（`model_info/`、`modal/`、`trial_case<N>_<T>s/`），失败的另存 `<名称>__failed/`。
