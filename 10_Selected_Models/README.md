# Group 18 精选模型

本目录集中保存报告采用的设计工况、已完成的丙烷验证输入和主要排烟对照。文件按原名从 [03_Models](../03_Models/) 复制。

| 文件夹 | 内容 |
| --- | --- |
| [01_Task2_Propylene_1p12](01_Task2_Propylene_1p12/) | 报告选用的 1.12 m³/s 丙烯排烟方案。OP-1 采用 0.44 m 端部补风开口，OP-6 采用 0.48 m。两种门况各有 0.02、0.05、0.10 kg/kg 三档烟炱产率。六个 FDS 输入的垂向网格均为 0.02 m，计算时长设为 120 s。另附 OP-6、0.05 kg/kg 限制工况的 PyroSim 原生文件。 |
| [02_Task1_Propane_Validation](02_Task1_Propane_Validation/) | 项目清单所列的 20 个已完成丙烷输入，覆盖 OP-1、OP-6 与 47.2、106.2 kW，并包括网格、边界和模型参数对照。 |
| [03_Task2_Propylene_Comparisons](03_Task2_Propylene_Comparisons/) | 1.28 和 0.96 m³/s 各六个原网格工况，以及四个垂向加密对照。0.96 m³/s 的 OP-6、0.02 kg/kg 加密算例在记录中出现热层高度越限。 |

## 在 PyroSim 中查看

直接打开 [限制工况的 PSM](01_Task2_Propylene_1p12/inlet48_6_0p05_0p24_1p12_z38_120.psm)。其余工况可以在 PyroSim 中导入对应的 FDS 输入。

在[限制工况 FDS 输入](01_Task2_Propylene_1p12/inlet48_6_0p05_0p24_1p12_z38_120.fds)中，部分围护面由计算网格的固体边界表示，所以 PyroSim 三维视图可只显示其中一部分实体。带侧门的长墙用 OBST 和 HOLE 建模。另一侧长墙、地板、舱内天花及端墙未被 VENT 覆盖的区域采用默认的 BOARD_LIMIT 绝热边界。端墙的补风开口、外侧通风边界、天花排风口和地板上的火源由 VENT 定义。绝热是该排烟模型采用的热边界假设。

工况选择和结果见[项目清单](../08_Project_Notes/project-requirements.md)、[风量对照](../05_Calculations/door_preset_flow_pair.csv)和[报告审阅稿](../07_Report/Group18_review_draft.md)。
