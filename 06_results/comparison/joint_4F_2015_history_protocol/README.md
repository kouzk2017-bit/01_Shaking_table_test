# 4F joint: standard vs test-history loading protocol (DIANA shell, origin)

同一个层壳节点模型（origin），两种加载协议：

- 标准协议（`origin`，原始结果）：±0.005/0.01/0.02/0.03/0.04 rad 各一圈。
- 试验历程协议（`origin_history`，raw 目录 `origin_2015_history`）：按 2015 Kobe 100% 4F
  实测层间位移角的转折点加载，见 `05_joint_models/loading_protocols/`。

两者步数不同，所以只按“响应–层间位移角”比较，不按加载步比较。

- `01_story_shear_vs_story_drift.png`：层剪力滞回。
- `02_joint_deformation_vs_story_drift.png`：节点变形角，含试验 4F。
- `03`–`05`：节点箍筋、梁纵筋、柱纵筋应变（ε/εy）随层间位移角。
- `06_peak_contribution.png`、`peak_contribution.csv`：试验 A–D 峰值处的节点变形贡献比。
  试验历程协议取与试验峰值同一时刻的转折点；标准协议取首次到达同一层间位移角的步。

与试验的时程对比（只用试验历程协议）：每个分析步按所在加载段换算到试验时间
（该段内实测层间位移角首次到达该步目标值的时刻），映射表在
`05_joint_models/diana_shell/data/processed/origin_history/step_time_map.csv`。

- `07_joint_deformation_time_history.png`：节点变形角时程。
- `08`、`09`、`12`：钢筋应变时程（DIANA 右 = 试验西；应变片对应见 `02_10-story_2015/REBAR_GAUGES.md`）。
  DIANA 网格 100 mm，每个试验应变片同时与构件面处和距面 100 mm 处的节点比较
  （2015 年应变片离面距离未知，2018 年同类布置为梁约 50 mm、柱约 80 mm）：
  - `08`：试验 **4G2A-STR-E01**（G2 东端下筋）↔ DIANA 右梁下筋 1628（柱面）、1629（距柱面 100 mm）。
  - `09`：试验 **4F2AC-STR-02**（4F 柱脚东侧，即试验图 chart_007 的柱筋）↔ DIANA 上柱左侧筋
    1839（梁面）、1838（梁面以上 100 mm）。
  - `12`：试验 3F2AC-STR-18（3F 柱头西侧）↔ DIANA 下柱右侧筋 1985，作参考。
  试验应变直接从原始数据读取，按本工况前 1000 点做基线修正；模型从零开始。
  （此前用的 Col44 = 4G1A-STR-E01 位于**角柱**节点，已弃用。）
- `10`、`11`：层剪力各自除以自身峰值后的滞回与时程。试验为 4F 整层剪力，模型为单个节点，
  只比较形状，不比较大小。

01–06 由 `05_joint_models/comparison/code/python/plot_history_vs_standard_protocol.py` 生成，
07–11 由 `plot_history_protocol_vs_test.py` 生成。
