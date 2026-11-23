# BSE3322 Topic B · Group 18

本项目用 FDS 对照 Peng 等人的顶棚射流实验，并比较不同排烟布局能否在 120 s 内维持至少 0.38 m 的烟层净高。

## 报告、视频与作业要求

| 要找的内容 | 入口 |
| --- | --- |
| 当前报告 | [英文 PDF](07_Report/Group18_Report.pdf) · [中文审阅 PDF](07_Report/Group18_Report_zh.pdf) · [LaTeX 源文件](07_Report/LaTeX/) |
| 课堂演示视频 | [视频目录与播放顺序](07_Report/videos/README.md) · [Task 1 温度场](07_Report/videos/OP1_106_coarse_native_temperature.mp4) · [Task 2 三维烟气](07_Report/videos/OP6_1p12_y005_front_soot_interior.mp4) |
| 作业要求 | [Topic B 原始作业 PDF](01_Assignment_Brief/Project_Topic_1B_Smoke_Extraction.pdf) · [工作清单](08_Project_Notes/project-requirements.md) |
| 实验依据与计算记录 | [参考资料导航](02_References/00_资料导航.md) · [本地下载目录](02_References/00_本地下载目录.md) · [工况验收记录](08_Project_Notes/03_Group18_验收记录.md) |

## 技术路径

- **Task 1** 用丙烷火模拟 OP-1 和 OP-6 两种门态、47.2 和 106.2 kW 两档功率，在 51 个位置与实验温升对照。[验证诊断图](07_Report/figures/diagnostics/)
- **Task 2** 改用丙烯火，比较挡烟与排烟布局。改进布局中，1.12 m³/s 通过六组细网格 FDS 工况复核，最低采样净高为 0.4358 m。[英文报告](07_Report/Group18_Report.pdf)
- **搜索与预筛** 用归档 FDS 数据评估 BO、GA、PINN 和回归模型的排序。设计选择以 FDS 复核为依据。[代理模型与回放记录](09_PINN_Layer/README.md)

## 工作区目录

| 目录 | 内容 |
| --- | --- |
| [00_Submit](00_Submit/) | 确认提交时使用的交付目录 |
| [01_Assignment_Brief](01_Assignment_Brief/) | 原始作业说明及课程安排 |
| [02_References](02_References/) | 文献、课程资料索引、规范及 FDS 文档 |
| [03_Models](03_Models/) | 项目使用的 FDS 工况输入文件 |
| [04_Results](04_Results/) | 本机保存的求解输出、切片及日志，大型结果由 Git 忽略 |
| [05_Calculations](05_Calculations/) | 实验对照、门流诊断、净高和设计比较的提取数据 |
| [06_Tools](06_Tools/) | 建模、结果提取、验证及绘图脚本 |
| [07_Report](07_Report/) | 中英文报告、源文件、[图表](07_Report/figures/)、[截图](07_Report/previews/)和[视频](07_Report/videos/) |
| [08_Project_Notes](08_Project_Notes/) | 要求、假设、设计决策和运行交接记录 |
| [09_PINN_Layer](09_PINN_Layer/) | 代理模型、留出评估和搜索顺序回放 |
| [98_wjc](98_wjc/) | 组员交来的模型、工作簿及 Word 文档，按原工况保存。本地另含原始运行输出 |
| [99_Archive](99_Archive/) | 历史材料归档位置 |
