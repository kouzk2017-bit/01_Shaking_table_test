# Comparisons

一个对比一个文件夹。所用节点/应变片见 `../data_sources/`（表格图）。

| 文件夹 | 对比 | 加载 | 生成脚本（`05_joint_models/`） |
|---|---|---|---|
| `test_vs_shell/2015_4F_standard_protocol/origin/` | 试验 vs 壳 origin（响应–位移角） | 标准 | `comparison/code/python/plot_experiment_vs_model_joint_drift.py --model shell` |
| `test_vs_shell/2015_4F_history_protocol/origin_history/` | 试验 vs 壳 origin_history（含标准 vs 历程、时程、梁端） | 历程 | `plot_history_vs_standard_protocol.py`（01–06）、`plot_history_protocol_vs_test.py`（07–12）、`plot_history_beam_bar_profile.py`（13–15） |
| `test_vs_shell/2015_4F_history_protocol/origin_history_slab/` | 试验 vs 壳有楼板 / 无楼板（三条线） | 历程 | `plot_history_slab_vs_test.py` |
| `test_vs_solid/2015_4F_standard_protocol/origin_2015/` | 试验 vs 实体基准 | 标准 | `update_case.py --model solid --case origin_2015` |
| `test_vs_solid/2015_4F_history_protocol/<工况>/` + 汇总图 | 试验 vs 实体最终版 | 历程 | `update_case.py --model solid --case <工况>` |
| `shell_variants/<变体>_vs_origin/` | 壳参数分析 j12_h/j12_m/j16_l/j16_m/j16_h、楼板 origin_slab | 标准 | `diana_shell/code/python/regenerate_all_figures.py` |
| `shell_variants/v2018_vs_j16_h/` | 2018 试件 vs J16-H | 标准 | 同上 |
| `failure_mechanism/` | 试验 vs 壳 vs 实体，首次屈服与各转折点状态 | 历程 | `comparison/code/python/failure_mechanism_summary.py` |

壳 vs 实体：暂停，壳模型定稿后输出到 `shell_vs_solid/`（`plot_shell_vs_solid_*.py`）；2026-09 的初步对比在 `../archive/2026-10-01_shell_vs_solid_preliminary/`。
