# Joint deformation angle: DIANA shell vs. solid, origin condition

层壳节点模型（`diana_shell`，工况 `origin`）与实体节点模型（`diana_solid`，工况
`origin_2015`）的节点变形角对比，横轴用加载步（两侧用的是同一套位移控制加载协议，
共 850 步，1-10 轴力加载、11-850 位移控制循环，步数完全一致，按步直接可比）。

节点面板尺寸 a=300mm、b=366.67mm 两侧一致（同一物理节点，网格和节点编号不同：壳单元
用 623/620/639/636，实体单元用 3149/3152/3165/3168，见
`05_joint_models/diana_solid/data/raw/README.md`）。

`01_joint_deformation_angle_by_step.png`：两条曲线中小幅值段（前约600步）吻合很好，
最大一圈循环（约第600-850步）明显分开——壳单元变形角达到约±0.025 rad，实体单元只到
约±0.012-0.017 rad，说明两种单元formulation在大变形阶段的表现有实质差异。

由 `05_joint_models/comparison/code/python/plot_shell_vs_solid_joint_deformation.py`
生成，可重复运行。试验时程数据未纳入这次对比。
