# 2015 十层振动台试件 OpenSees 模型

按 2015 年 E-Defense 十层 RC 墙-框架试件资料建立的三维 OpenSeesPy 模型，建模方法沿用 `02_TJU_test` 的 OpenSees 模型。单位 **N–mm–t–s**。

当前状态见 [TRIAL_STATUS](docs/TRIAL_STATUS.md)：模型可以完成 20 s 的 Case 13，但比实测刚 4–5 倍，**还不能和试验定量对比**。建模检查清单见 [MODEL_REVIEW](docs/MODEL_REVIEW.md)，参数来源见 [PARAMETER_SOURCES](docs/PARAMETER_SOURCES.md)。

## 工作流程

```
02_10-story_2015/data/raw/ ─┐  (台面实测加速度，只读)
config/specimen_2015.json ──┼─> model/ ──> ① info  : 材料/截面/几何检查图（只建模）
config/analysis.json ───────┘              ② modal : 重力 + 模态（对照实测周期）
                                           ③ trial : 重力 + 模态 + 时程
                                           ④ verify_run.py : 核对时程结果
```

在本目录的 PowerShell 中运行（执行策略受限时加 `-ExecutionPolicy Bypass`）：

```powershell
powershell -ExecutionPolicy Bypass -File run.ps1 -Stage info
powershell -ExecutionPolicy Bypass -File run.ps1 -Stage modal
powershell -ExecutionPolicy Bypass -File run.ps1 -Stage trial -Case 13 -Duration 20
..\..\02_TJU_test\.venv\Scripts\python.exe -B verify_run.py ..\06_results\opensees\trial_case13_20s
```

每次改模型的推荐顺序：修改 `config/` 或 `model/`，然后按 ① → ② → ③ 运行。
- ① 用来检查材料和截面，约 1 分钟；
- ② 用来对照实测周期（frame 方向 0.85 s，wall 方向 0.58 s），约 1 分钟；
- ③ 只在前两步确认后再跑，20 s 约需 1 小时。

脚本默认使用 `02_TJU_test/.venv` 的 Python。独立运行时用 Python 3.12，安装 `requirements.txt`，再传入 `-Python <python.exe>`。

## 结果位置

所有结果都在 `06_results/opensees/` 下，每个阶段一个固定名称的文件夹，重跑时覆盖：

| 文件夹 | 内容 |
|---|---|
| `model_info/` | 图片 01–26、`audit/` 参数 JSON、`README.md` 图片索引 |
| `modal/` | 重力反力、模态周期与振型、模型汇总、参数和源码快照 |
| `trial_case13_20s/` | 楼层响应、峰值、基底反力、求解恢复记录、响应图、参数和源码快照 |

- 运行过程中写入 `<名称>__running/`。
- 成功后替换同名旧文件夹。
- 失败时保存为 `<名称>__failed/`，同时保留上一次成功的结果。
- 楼层响应表中 `story=1…10` 对应楼面 `2F…RF`。

## 代码

| 路径 | 作用 |
|---|---|
| `config/specimen_2015.json` | 几何、分层材料、柱梁配筋、墙体、楼板翼缘、框架单元选项及参数来源 |
| `config/analysis.json` | 重力步数、收敛判据、阻尼、积分器、恢复策略 |
| `model/build.py`、`model/sections.py` | 建模；纤维截面和分层壳截面 |
| `analysis/ground_motion.py` | 读取台面 SW/NE 两角实测加速度，滤波后取平均 |
| `analysis/solver.py` | 重力、模态、时程 |
| `entrypoints/trial.py`、`entrypoints/output.py` | 运行入口；固定名称的结果文件夹 |
| `postprocessing/model_info_figures.py`、`postprocessing/figures.py` | 模型信息图；模型和响应图 |
| `verify_run.py` | 只读核对已完成的时程结果 |

## 模型要点

- **几何**：十层，总高 25,750 mm；长边 3×4,000 mm，短边 3,100+1,800+3,100 mm。
- **坐标**：模型 X = 图纸/传感器 Y（长边，纯框架方向）；模型 Y = 图纸/传感器 X（短边，带墙方向）；Z 向上。
- **梁柱**：forceBeamColumn 纤维单元。混凝土为 Concrete02（保护层和约束核心），钢筋为 Steel02，框架钢筋用 MinMax 在 6% 应变处断裂；扣除被钢筋置换的混凝土；PDelta。剪切柔度按弹性、未开裂的腹板计算。
- **节点**：柱端刚域取相交梁最大梁高的一半，梁端取柱宽的一半；梁子单元整体位于柱宽内时改为刚性段（10 倍毛截面刚度）。墙层 G8 在 C3 边缘柱宽内以刚性段嵌入墙壳。**没有节点剪切变形和黏结滑移。**
- **梁截面**：取报告中的端部和跨中配筋；计入 AIJ 有效宽度的楼板翼缘和 S1 板筋；纤维坐标以毛截面形心为参考轴。
- **墙**：四片短边墙，1–6 层厚 230 mm，7 层厚 150 mm，8–10 层无墙。采用 ASDShellQ4 分层壳（PlaneStressUserMaterial）；C3 边缘柱和 G8 梁带并入墙壳。
- **楼板**：楼层设刚性平面约束；楼板用 ShellMITC4 + ElasticMembranePlateSection。TJU 模型用的五分量 ElasticPlateSection 与 ShellMITC4 不兼容，所以改用这个截面。
- **质量**：2F–RF 移动重量 8,196 kN（按 g = 9.8 m/s² 换算为 836.3 t），按楼板面积分配，只有水平质量。
- **阻尼**：5% Rayleigh，锚定 T1 和 0.2T1，与已提交刚度成比例。阻尼比是假定值。
- **求解**：HHT（α = 0.9）+ KrylovNewton，收敛判据 NormDispIncr 1e-4 mm。不收敛时依次改用其他算法、放宽判据到 1e-3 mm、细分步长。
- **输入**：Case 13（2015-12-09，JMA Kobe 10%，固定基础阶段）。取台面 SW 和 NE 两角水平加速度的平均，不再乘缩放系数，也不输入竖向。可运行的固定基础工况为 13/15/17/20/22。

## 主要限制

1. 从未损伤状态开始，没有继承 11 月滑移系列（10/25/50/100%）造成的损伤。这是和实测周期相差约 2 倍的主要候选原因。
2. 混凝土峰后行为、约束系数、钢筋硬化和断裂、阻尼都沿用 TJU 的假定，没有标定。D16 钢筋的 fy 和 Es 是假定值。
3. 板厚取 130 mm（报告），图纸为 120 mm，仍未确定。
4. 没有模拟基础滑移、6 层钢连接缝的柔度、竖向和转动输入。
