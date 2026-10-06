# Comparisons

主线：每个节点模型先跟试验对比，按模型分目录，下一级 `<试验年份>_<楼层>_<加载协议>`。

- `test_vs_shell/2015_4F_standard_protocol/`：2015 Kobe 100% 4F vs 层壳 origin（标准协议，按“响应-层间位移角”叠加）。
- `test_vs_shell/2015_4F_history_protocol/`：同上，层壳用试验历程协议，可按试验时间叠加；含标准 vs 历程协议对比。
- `test_vs_solid/<协议>/<实体工况>/`：实体每个工况一个子文件夹（名字同 `diana/solid/`）。历程协议下有时程对比（04–08）和全部工况的汇总图，见 `test_vs_solid/2015_4F_history_protocol/README.md`。
  - `2015_4F_standard_protocol/origin_2015/`：标准协议基准。
  - `2015_4F_history_protocol/origin_2015_parabolic_history/`：parabolic，+0.016 rad 未收敛后骤降。
  - `2015_4F_history_protocol/origin_2015_parabolic_residual_history/`：parabolic + 残余强度 9.6 MPa，全部收敛。
  - `2015_4F_history_protocol/origin_2015_parabolic_gc61_residual_history/`：再加 Gc 61 N/mm，正向大位移角跟试验吻合，负向 −0.022 rad 偏弱。
  - `2015_4F_history_protocol/origin_2015_parabolic_gc61_residual20_history/`：再把残余强度提到 20 MPa，正负向和节点占比都跟试验吻合（当前最好，1119 步全部完成）。

层壳 vs 实体：暂停，壳模型定稿后再生成，输出到 `shell_vs_solid/`（脚本 `plot_shell_vs_solid_*.py`）。
2026-09 的初步对比留档在 `../archive/2026-10-01_shell_vs_solid_preliminary/`。

- `failure_mechanism/`：试验 vs 壳 vs 实体的破坏机理诊断（节点 4，收尾版 2026-10-06）。
