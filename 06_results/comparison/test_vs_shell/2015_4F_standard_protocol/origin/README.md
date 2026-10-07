# 4F joint: 2015 shaking table vs. DIANA origin

试验（动力时程，20151211-2(JMAKobe100%)，4F 节点）与 DIANA 层壳模型 origin 工况
（拟静力，位移控制加载步）的节点变形角-层间位移角对比。两者都转换成"响应量对响应量"
曲线（节点变形角 vs 层间位移角，Y 方向/纯框架方向），不依赖时间或加载步数，因此可以
直接叠加。层间位移角取 `story_drift_y`（模型 X = 传感器 Y，长边纯框架方向，无墙，
适合跟节点局部模型对比）。

- `01_joint_deformation_vs_story_drift.png`：完整轨迹叠加，试验曲线标出 A/B/C/D 四个
  显著负向层间位移角峰值点（与试验侧现有工况图表的峰值选取规则一致）。
- `02_joint_deformation_vs_story_drift_envelope.png`：只保留每个曲线的转折点（层间
  位移角的全部局部极值），作为简化的包络/骨架线对比，避免动力时程本身噪声较大导致
  完整轨迹图不易读。
- `03_normalized_shear_vs_story_drift.png`：层剪力各自除以自身峰值（试验 4F 整层 3691 kN，
  模型一个节点 392 kN，只比形状）。

由 `05_joint_models/comparison/code/python/plot_experiment_vs_model_joint_drift.py`
生成：`--model shell`（默认，条件 origin）。

阅读对比时请注意几个没有做修正的物理差异：动力加载应变率高于拟静力，试验强度/刚度
可能因此偏高；拟静力模型没有惯性力和阻尼；两者的加载幅值序列和圈数不同（地震动不规则，
DIANA 是规则递增的位移控制协议）。
