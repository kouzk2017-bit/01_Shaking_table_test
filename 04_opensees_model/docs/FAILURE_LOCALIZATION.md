# 未收敛定位记录

## 本次结论（2026-09-08）

原失败工况已精确复现：0–12.69 s 的 12,700 行楼层响应全部数值列与原运行逐点相同，17 个归档源码文件哈希一致。首次失败发生在 **12.69→12.70 s** 的 0.01 s 增量，ModifiedNewton 迭代 100 次，位移增量范数 3.3854e-5，超过 1e-6 容限，返回 -3。

本次诊断在首次算法失败处停止。旧运行随后用 NewtonLineSearch 成功到达 12.70 s，再在下一增量中耗尽算法和步长回退；两者不是同一个终止点。

**已锁定失败时段，尚未锁定导致失败的单个墙单元。** 最后收敛状态与失败回退后的节点位移、壳截面应变逐项完全相同，不能据此还原失败迭代中的局部试算状态。已记录的收敛状态没有显示墙片应变突然爆增。

| 应变指标（绝对分量最大值） | 单元与位置 | 数值 |
|---|---|---:|
| 面内应变 | 478，第三层 W3 边缘区；X=8 m，Y=2.875–3.100 m，Z=7.900–8.000 m | 1.18688e-4 |
| 由中面应变与曲率推算的外表面应变界限 | 586，第四层 W2 边缘区 | 1.75098e-4 |

这些是应变集中位置，**不是已证实的破坏位置或不收敛源**。目前优先核查 ASDShellQ4 的 EAS 与初始刚度 Rayleigh 调用之间的数值交互：下述独立墙片对照已重复复现异常，但尚未证明它是整楼终止的唯一原因，也未完成修复后的完整时程验证。

结果目录 `06_results/opensees/10story_2015/20260908T023932_963929Z_locator` 内已保存 `replay_consistency.json`、`rollback_comparison.json`、`localization_summary.json`、`wall_localization.png` 和 `wall_strain_history.png`。墙片图显示回退后应变分布，不是失败单元判定图。

## 已复现的数值交互异常

在当前 OpenSees 3.8.0 环境中，八单元非线性墙片仅将初始刚度 Rayleigh 系数从 0 改为 1e-30，就出现了明显不同的位移响应和首个未收敛时刻。1e-30 的物理阻尼贡献可忽略，主要差别是是否触发初始刚度计算路径。

结果目录：`06_results/opensees/10story_2015/20260908T024335_747981Z_coupon`。可查看 `beta_comparison.json`、`beta_zero_vs_tiny.png` 和逐步 CSV。

| 壳选项 | 积分器 | 共同已收敛时段最大位移差（mm） | β=0 最后收敛时刻（s） | β=1e-30 最后收敛时刻（s） |
|---|---|---:|---:|---:|
| EAS 开 | HHT | 0.862807 | 1.875 | 1.785 |
| EAS 开 | Newmark | 0.026746 | 1.570 | 1.755 |
| EAS 关 | HHT | 0 | 2.480 | 2.480 |
| EAS 关 | Newmark | 0 | 2.480 | 2.480 |

这不是单纯由“阻尼大小不同”解释的响应差别。无 EAS 的对照逐点完全相同，将异常范围缩小到 **ASDShellQ4 的 EAS 与初始刚度 Rayleigh 路径之间的交互**。所有墙片强输入算例最终仍未收敛，因而这一测试没有证明消除该交互就能解决整楼全部收敛问题。

使用独立新进程再次运行（`20260908T025120_676235Z_coupon`），八个算例的时间、位移、迭代次数数组全部逐点相同，确认该现象可重复。

整楼 0–0.1 s 的补充对照（`20260908T035818_843659Z_locator` 为 β=0，`20260908T035819_167460Z_locator` 为 β=1e-30）均完成。楼层最大位移差 X=1.50e-8 mm、Y=1.79e-7 mm，仍小于 1e-6 的全局位移增量判据；这段短时对照不能单独证明整楼失败由该交互引起。其状态文件明确区分原求解器返回的名义 Rayleigh 系数和诊断实际使用系数，未把该对照标记成原工况重放。

## 对应源码路径

官方 [ASDShellQ4.cpp](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/element/shell/ASDShellQ4.cpp) 中：

- `getInitialStiff()` 调用 `calculateAll(OPT_LHS | OPT_LHS_IS_INITIAL)`。
- `calculateAll()` 对 EAS 无条件进入 `AGQIbeginGaussLoop()`，重置内部矩阵及残差，再用所选刚度组装。
- 后续 `AGQIupdate()` 使用这些内部矩阵和残差更新增强应变自由度。

据此推断，初始刚度调用影响了本应供非线性迭代使用的 EAS 工作状态。源码解释与本机零/微小系数对照相符；本记录没有通过修改、重新编译 DLL 完成最终源码修复验证。

## 整楼原工况重放

先行整楼静力筛查 `20260908T024952_238538Z_static_screen`：分别施加随楼层质量和层号增加的 X/Y 单向水平力，用屋顶位移控制从重力状态增加到 5 mm（每步 0.1 mm），两向均完成 50 步，末步各用 2 次迭代。5 mm 大于旧时程的屋顶峰值约 3.28/2.56 mm，但静力载荷分布和加载历史不同，不能据此排除所有材料非线性问题。该结果仅说明在相近整体变形量下，模型没有必然出现同样的求解失败。

双向同时加载筛查 `20260908T031129_516912Z_static_screen` 采用 Fy/Fx=1.3（诊断假定，并非实测加载路径），完成屋顶 X 增量 5 mm、Y 约 4.30 mm，末步 6 次迭代。第四层 W4 边缘区单元 658 的面内应变分量最大约 1.75e-4，仍收敛；不能将这个静力最大应变位置直接认定为动力失败位置。

运行目录：`06_results/opensees/10story_2015/20260908T023932_963929Z_locator`。

使用 2026-09-07 失败运行的原始源码快照、参数和完整输入历史，未把后续配筋修正混入重现过程。成功步诊断只读取截面应变、截面内力及节点状态；停止后的残差查询例外，见下文限制。已核对 t=0.8 s 各楼层双向位移与原运行差值为 0。

t=6.0 s 再次核对各楼层双向位移，差值仍为 0，结果保存于 `replay_consistency.json`。

## 残差诊断的适用范围

文件名 `failed_soe_residual.npy` 保留原名，但其内容是 **自动回退后重新组装的 B，不是失败迭代的最终残差**。官方 [OpenSeesCommands.cpp](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/interpreter/OpenSeesCommands.cpp) 的 `OPS_printB()` 会先调用积分器 `formUnbalance()`，因此该查询不是被动读取。状态元数据和汇总已更正解释；原始数组与运行时脚本未改写。

官方 [DirectIntegrationAnalysis.cpp](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/analysis/analysis/DirectIntegrationAnalysis.cpp) 在求解失败后调用域和积分器回退。实测此次回退后位移、截面应变与最后成功步完全相同，截面内力结果仍有差别，因此失败后的内力不能当作新的已提交平衡状态。

刚性楼盖从节点的方程编号不能直接按 X/Y/Z/Rx/Ry/Rz 解释：[TransformationDOF_Group.cpp](https://raw.githubusercontent.com/OpenSees/OpenSees/master/SRC/analysis/dof_grp/TransformationDOF_Group.cpp) 将自由从节点 DOF 放前、保留主节点 DOF 放后。本次已修正映射并验证 7,656 个方程恰好覆盖一次。

在上述限定下，重新组装 B 的最大平动力分量在第九层楼盖主节点 X 方程，约 1.654 kN；最大力矩分量在第七层楼盖主节点 Rz 方程，约 0.598 kN·m。它们不能定位到某一片墙，也不能替代失败迭代残差。全局向量同时含 N 与 N·mm，不能把混合范数称为某个实际力。

## 后续修复验证所需证据

诊断脚本已增加在 `printB` 前被动保存 `printX`，供下一次运行保留最后求解增量；本次运行未记录该数据。继续追溯具体失败迭代，需要在失败时段开启迭代向量记录，再对 EAS/初始刚度调用路径进行受控修复或替代对照，最后验证完整 20 s。已有 NPZ 节点状态无法恢复材料加载历史，不能作为 12.69 s 的完整重启状态。
