# 二维 IMK 集中塑性模型（框架方向，模型 X）

与三维纤维模型并列的简化模型，只模拟框架方向（模型 X = 图纸 Y）。几何、材料、配筋读取 `config/specimen_2015.json`；箍筋、IMK 选项和分析参数在 `config/imk2d.json`。

## 运行

```powershell
cd 04_opensees_model
..\..\02_TJU_test\.venv\Scripts\python.exe -B -m imk2d.run --stage params     # 只算铰参数表（约 35 s）
..\..\02_TJU_test\.venv\Scripts\python.exe -B -m imk2d.run --stage modal      # 重力 + 模态
..\..\02_TJU_test\.venv\Scripts\python.exe -B -m imk2d.run --stage pushover   # 一阶振型分布 pushover，至屋顶 3%
..\..\02_TJU_test\.venv\Scripts\python.exe -B -m imk2d.run --stage trial --case 13 --duration 20
```

结果在 `06_results/opensees/imk2d_<stage>/`（时程为 `imk2d_trial_case<N>_<T>s/`），命名和失败处理同三维模型。

## 模型

| 项目 | 做法 |
|---|---|
| 框架 | 外框架（y = 0/8000，C1-C2-C2-C1，G1-G3）和内框架（y = 3100/4900，G4-G6），各代表 2 榀（刚度、强度、荷载 ×2）；楼层 X 向 equalDOF |
| 内框架 1-7 层 | 每条轴线取半片 Y 向墙（C3 边缘 + 半个墙腹板）按弱轴弯曲作为"墙肢柱"；8-10 层为 C3 柱 |
| 构件 | 弹性单元 + 两端零长度 `IMKPeakOriented` 转动弹簧，n = 10 刚度分配（Ibarra & Krawinkler 2005） |
| 节点域 | 节点中心到构件面的刚性连杆；**无节点剪切、黏结滑移** |
| My | 截面纤维分析：Hognestad 混凝土、理想弹塑性钢筋；受拉钢筋屈服或混凝土应变达到 1.8 fc/Ec；柱取重力轴力；梁计入 AIJ 有效翼缘和 S1 板筋，正负向分开 |
| θp、θpc、Mc/My、λ、EI | Haselton et al. (2016) 柱公式；梁取 ν = 0；ρsh 来自报告表 1/表 2 箍筋 |
| 初始刚度 | EIstf40（40% My 割线），T1 = 0.829 s，实测 0.85 s；EIy 时 T1 = 1.080 s |
| 循环退化 | Λ = λ·θy（新版 IMK 中 Et = Λ·My，已用数值试验确认） |
| 重力 | 楼层重量按楼板面积和轴线受荷宽度，均布于梁净跨，节点域部分作节点荷载 |
| 质量 | 各层质量集中在外框架 x = 0 节点（经 equalDOF 分给全楼层） |
| 阻尼 | 5% Rayleigh（T1、0.2T1）；质量项在楼层节点，刚度项只加在弹性构件上并乘 (n+1)/n；弹簧和刚性连杆不加阻尼 |
| 输入 | 台面实测加速度的 X 分量（同三维模型的读取、滤波、轴向映射），不输入 Y 和竖向 |

## 假定和限制

1. 箍筋标注 `[a,b]` 中 a 按"平行图纸 Y（框架方向）的肢数"理解，依据是 C3 和 C2 附加箍的画法；表中没有明说。
2. Haselton 公式是按柱试验标定的；用到梁（ν = 0）和墙肢弱轴上没有单独验证。
3. 残余强度比 0.2、极限转角 0.2 rad 是假定值。
4. 没有 P-M 相互作用（My 按重力轴力计算），没有双向耦合。
5. 从未损伤状态开始；11 月滑移系列造成的损伤没有继承。
6. 横向 G7-G9 梁的扭转约束、楼板在有效宽度以外的框架作用都没有计入。
