# BSE3322 Mini-design Project — Topic B

Natural-ventilated Ceiling Jet Fire Plume Profile in Long Compartment / Smoke Extraction

本仓库用于完成 BSE3322 Topic B 作业：CFD 建模、实验验证、敏感性分析和排烟设计。

## 资料与目录

- `brief/`：原始作业 PDF，保留原文，不直接修改。
- `docs/`：要求清单、假设、进度和决策记录。
- `calculations/`：特征火源尺度、网格、排烟量及风机功率计算。
- `models/`：FDS 输入、PyroSim 模型及算例配置。
- `references/`：文献记录和数字化实验数据。
- `report/`：报告正文和图表说明。
- `output/`：本地仿真结果和生成文件，默认不纳入 Git。
- `scripts/`：可复用的模型生成、后处理与绘图脚本。

从 [项目要求](docs/project-requirements.md) 开始。当前尚未安装或运行仿真工具，也尚未生成工程模型。

## Git

远程仓库：https://github.com/LYUml/polyu_bse3322.git

主分支：`main`。仅显式要求发布时推送；课程材料和文献上传前须确认可公开分享。

## 下一步

1. 确认组号和提交要求，核对作业表格中的算例分配。
2. 阅读图 1 和两篇参考文献，确定几何、火源、测点、材料及边界条件。
3. 检查本机 FDS / PyroSim 工具与版本，建立可复现的基准算例。
4. 完成网格与模型敏感性、实验验证，再进行排烟设计。
