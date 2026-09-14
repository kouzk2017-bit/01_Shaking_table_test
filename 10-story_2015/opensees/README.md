# 2015 十层振动台试件 OpenSees 模型

沿用 `02_TJU_test/02_Pre_Experiment_Validation/01_OpenSees_Model` 的三维 RC 建模方法，按 2015 年试验资料独立建立。使用 OpenSeesPy，单位 **N–mm–t–s**。原 TJU 模型和试验原始数据没有改动。

当前用途是**建立模型、重力/模态检查及小强度实测输入试运行**。尚未完成试验响应拟合，也没有把试运行成功视为验证通过。

检查结果与未收敛记录见 [数值试运行状态](docs/TRIAL_STATUS.md)。20 秒时程尚未通过，不能将其当作已验证算例。

针对未收敛的墙片对照、整楼静力筛查和原工况重放见 [未收敛定位记录](docs/FAILURE_LOCALIZATION.md)。

## 运行

在本目录执行：

```powershell
.\run.ps1 -Stage model
.\run.ps1 -Stage modal
.\run.ps1 -Stage trial -Case 13 -Duration 1
.\run.ps1 -Stage trial -Case 13 -Duration 20
```

`modal` 包含重力分析；`trial` 包含建模、重力、模态、时程和成图。脚本优先使用同工作区 TJU 的现成 Python 环境，不复制或修改该环境。独立运行时使用 Python 3.12、安装 `requirements.txt`，再传入 `-Python <python.exe>`。

时程默认采用 KrylovNewton；必要时尝试 NewtonLineSearch、Newton 并细分步长，保持相同收敛判据。ModifiedNewton 矩阵复用选项仍可用于诊断，但初步计时没有显示足够收益，因此不作为默认设置。

也可直接 `python -B -m entrypoints.trial --stage trial --case 13 --duration 20`。`--config` 和 `--analysis-config` 可指定替代 JSON，默认参数见 `config/`。代码导入本身不建模、不启动计算。

## 模型及坐标

- 十层，总高 25,750 mm；长边 3×4,000 mm，短边 3,100+1,800+3,100 mm。
- **模型 X=图纸/传感器 Y（长边纯框架方向），模型 Y=图纸/传感器 X（短边带墙方向）**；模型 Z 向上。输入和输出都明确采用这个映射。
- 外侧 C1/C2 和上部 C3：Concrete02 保护层/约束核心、Steel02+MinMax 钢筋、扣除被钢筋置换的混凝土、弹性扭转、PDelta、dispBeamColumn。该梁柱单元不使用 Aggregator 的 Vy/Vz 项，没有独立剪切变形。
- 梁采用报告中的端部/跨中配筋。以五点 Lobatto 的位置和权重，通过 UserDefined 积分分配不同截面；节点细分时保留所在全跨位置。保护层和具体排筋坐标仍为显式假定。
- 四片短边墙：1–6 层厚 230 mm，7 层厚 150 mm，8–10 层无墙。采用 PlaneStressUserMaterial、PlateFromPlaneStress、PlateRebar、LayeredShell 和 ASDShellQ4。墙内 C3 边缘柱和 G8 顶部梁带整体建壳，不叠加同位置线单元。
- 楼层设置刚性平面约束，楼板采用 ShellMITC4 + **ElasticMembranePlateSection**。这是针对截面兼容性的必要修正；详见下面说明。
- 移动楼层重量 2F–RF 共 8,196 kN，对应 836.326531 t。采用与现有试验处理程序一致的 g=9.8 m/s²；固定基础的 1F 重量不计入移动质量。水平质量按楼板面积分配，竖向质量和竖向地震输入未启用。

## 试运行工况

默认 **Case 13：2015-12-09，JMA Kobe 10%，固定基础阶段**。直接读取 JB14 西南角台面 AX/AY 实测加速度，1 ms 原始采样；按现有处理流程做全记录 FFT 滤波和抗混叠后取 10 ms。已是 10% 试验的实测输入，**不再乘 0.1，不应用 TJU 的 1/6 缩尺关系**。

输入保留起始预历史，分析 t=0 加零点，原记录整体后移 0.01 s。20 s 覆盖约 13.6 s 的主要水平脉冲。输出绝对加速度=相对加速度+映射后的台面输入；位移、层间位移角为相对固定基础的响应。

2015 年 11 月是基础滑移阶段；12 月改为固定基础。因此当前固定基础模型拒绝把 Case 2/4/7/10 的台面记录作为对应固定基础试验直接输入。可运行的固定基础编号为 13/15/17/20/22，但后续工况的前序损伤均尚未继承。当前默认仅为 Case 13 小强度试运行。

## 已知假定及后续校准项

1. 采用初始无损伤材料状态，未继承此前滑移 10/25/50/100% 试验的损伤，也未显式模拟基础滑移、接触和第六层钢连接缝柔度。
2. 材料屈服强度/弹性模量按实测报告汇总；钢筋同直径跨楼层取合并值。D16 缺少已确认试样，保留旧模型屈服强度及名义 Es 的假定。混凝土峰后、约束系数、钢筋硬化/断裂和 5% 阻尼沿用 TJU 假定，尚未校准。
3. 报告文字给楼板厚 130 mm，施工图 S-33 标 120 mm。本版本采用 130 mm，并保留该资料差异。楼板和墙边缘配筋采用本模型说明的等效方式；墙内边缘钢筋为分布钢筋，梁带配筋位于上下 100 mm 区域。
4. 小悬挑、钢楼梯、吊装附件不单独贡献刚度；其重量包含在报告楼层质量中。楼层质量中心和转动惯量由当前平面面积分布计算，尚未按逐件称重分解。
5. 梁柱采用 Euler–Bernoulli 假定，未计独立剪切变形；未建钢筋黏结滑移、接头剪切弹簧、压屈或校准的破坏准则。壳内钢筋采用连续 Steel02，未开启断裂。

这些参数和范围均可供后续试验验证修订，不能将当前模型用于声明大震破坏预测精度。

## 楼板兼容性修正

照搬 TJU 的 `ElasticPlateSection + ShellMITC4` 后，首次重力计算出现奇异刚度，局部楼板节点产生非物理的竖向位移。OpenSees 的 ElasticPlateSection 是五分量截面，而 ShellMITC4 采用八分量壳截面。本模型改用官方示例采用的 ElasticMembranePlateSection；保留刚性楼盖后，楼板面内应变由刚体运动约束为零，仍由楼盖约束控制面内运动。

出处：[OpenSees ElasticPlateSection 源码](https://opensees.berkeley.edu/OpenSees/api/doxygen2/html/ElasticPlateSection_8cpp-source.html)、[ShellMITC4 官方示例](https://opensees.berkeley.edu/OpenSees/manuals/ExamplesManual/HTML/876.htm)。**此次只修正新模型，未修改 TJU 原模型。**

## 文件和输出

- `config/specimen_2015.json`：试件几何、分层材料、柱梁配筋、墙体和参数来源。
- `config/analysis.json`：重力步数、收敛判据、阻尼、积分器和最小子步。
- `model/build.py`、`model/sections.py`：建模与截面。
- `analysis/ground_motion.py`、`analysis/solver.py`：原始波形读取和分析。
- `docs/PARAMETER_SOURCES.md`：资料页码、参数对应和重要差异。

每次运行先在 `../../results/2015/opensees/<UTC时间_分析类型>/` 建立唯一目录，保存参数快照、源码快照及 SHA256、输入源 SHA256、求解日志和状态。失败也保留日志，不覆盖旧运行。

主要结果包括 `model_summary.json`、节点/单元/质量 CSV、截面审计 JSON、重力反力、重力后模态、`floor_response.csv`、`response_peaks.csv`、模型图及响应图。楼层响应表的 `story=1…10` 对应物理楼面 `2F…RF`，不是物理 1F…10F。

基础反力输出包含惯性/阻尼项，正号为支座对结构的作用。计算成功须同时满足：输入读取有效、重力平衡误差≤1e−5、所有特征值为正且有限、每个响应值有限、实际时程达到请求终点。与试验的误差对比属于下一步工作。
