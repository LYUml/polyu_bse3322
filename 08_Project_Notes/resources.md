# 消防模拟工具 文献与香港规范

检索日期：2026-11-13。用途：BSE3322 Group 18 Topic B。以下是文档/仓库调查，并非安装、运行或精度验证结果。

## 建议采用的工具链

优先利用本机 PyroSim/FDS，配合可审阅的 `.fds` 输入、Python 后处理和实验曲线数字化。先做正确的单一基准算例，再增加自动化。MCP 是调用接口，skill 是工作指引，两者都不能替代实验验证或数值求解器。

| 工具 | 本项目用途 | 评估与边界 |
| --- | --- | --- |
| [FDS + Smokeview](https://pages.nist.gov/fds-smv/) | LES 火烟模拟与可视化 | 主选计算底座；[官方手册入口](https://pages.nist.gov/fds-smv/manuals.html) 检索时列 FDS 6.11.1；本机附带手册是 6.10.1，应先固定实际版本 |
| [PyFDS](https://github.com/GraysonBellamy/pyfds) | Python 生成输入、参数化、进程管理、CSV 结果 | MIT；不是现成 AI agent；依赖独立安装的 FDS 执行。引入前用本项目所需 namelist 做兼容性试验 |
| [fdsreader](https://github.com/FireDynamics/fdsreader) | 切片、边界、设备等输出转 NumPy 数组 | 适合温度剖面与场数据后处理；仓库显示 GPL/LGPL 许可文件，复用时核对锁定提交的具体许可 |
| [WebPlotDigitizer](https://github.com/automeris-io/WebPlotDigitizer) | 从论文图像提取实验曲线 | 保留坐标标定、原图、图号与误差记录。开源仓库和商业 AI/cloud 功能的许可边界不同 |
| [BULC MCP](https://github.com/Meteor-Simulation/bulc-mcp) | 消防软件 AI 接口、知识规则、FDS deck 检查、网格建议 | 可优先借鉴建模检查与工作流程。MCP/知识包 MIT，桌面应用与求解器商业许可；部分知识/检查工具不需桌面 app，实际建模运行工具需 app。尚未测试 |
| [Prometheus 作者公告](https://github.com/firemodels/fds/discussions/16323) | FDS 语法、物理与故障问答 | 公告明确不用于编写输入文件；未确认可自托管的开源实现 |
| [FoamPilot 论文](https://arxiv.org/abs/2412.17146) | 借鉴源码检索、算例修改及运行分析流程 | 面向 FireFOAM 的 proof of concept；复杂任务仍需改善，未确认论文对应 agent 的公开源码。不要将同名库当作该 agent |
| [FireFOAM](https://github.com/fmglobal/fireFoam) | 另一种开放火灾 CFD 引擎 | 可研究，但本作业已有 PyroSim/FDS 教学基础，切换求解器会增加建立与验证成本 |

上述 PyFDS/fdsreader/BULC 均未在本工作区安装或实测。此次未确认到同时覆盖 PyroSim 操作、实验验证、香港规范审查的成熟开源专用 skill/MCP。

## 可用 skill 与后续定制方向

本会话已有 PDF、Presentations、Spreadsheets 技能，可用于读取 01_Assignment_Brief/论文、课件和课程安排；它们是通用资料处理能力。无需为了开始这个作业先安装一套外部 agent。

项目若要定制 skill，建议围绕以下可检查流程：输入来源与单位核对 → 几何/边界/火源检查 → case manifest → 小型执行验证 → 运行监控 → 守恒与实验对比 → 图表/报告溯源。香港条文另维护“文件版本、条款号、适用范围、设计证据”的索引。这里仅提出设计方向，未创建或安装专用 skill。

## 必须优先读的实验与数值文献

1. **Peng et al. (2021)**, Experimental study on temperature profile in long-narrow compartment fire with multiple lateral openings. TUST 117, 104018. [DOI](https://doi.org/10.1016/j.tust.2021.104018)，[CityU 作者机构记录](https://scholars.cityu.edu.hk/en/publications/experimental-study-on-temperature-profile-in-long-narrow-compartm/)。这是作业的实验验证来源；已核对书目和摘要，尚未获得全文或数字数据。要提取几何、壁面、火源、测点、开口组合和温度曲线。
2. **Yuen et al. (2015)**, LES and multi-step chemical reaction in compartment fires. Numerical Heat Transfer A 68(7), 711–736. [作者机构记录](https://ro.ecu.edu.au/ecuworkspost2013/1348/)，DOI 10.1080/10407782.2015.1012886。摘要比较 Smagorinsky/WALE 与化学反应方案；不能据摘要认定其中模型设置可直接映射到 FDS。尚未获得全文。
3. **Xu, Mohaddes & Wang (2024)**, LLM Agent for Fire Dynamics Simulations. [arXiv 2412.17146](https://arxiv.org/abs/2412.17146)。自动化工作流参考，不是本实验的验证数据来源。

作业 PDF 的图表数字化超链接实际指向 [PlotDigitizer tutorial](https://plotdigitizer.com/extrac-data-graph-image)。WebPlotDigitizer 是可另行评估的工具，不应与该原链接混为一谈。

## 香港规范与法律资料入口

这里是研究与课程设计的适用性索引，不是逐条完成的法定合规审查。缩尺隧道类实验、真实建筑、地下空间和隧道工程的适用条件不同；先保留作业实验的物理尺度，不把建筑条文数值机械缩放进试验模型。

| 来源 | 优先查什么 | 使用边界 |
| --- | --- | --- |
| [FSD Codes of Practice 现行目录](https://www.hkfsd.gov.hk/eng/fire_protection/notices/code.html) / [September 2022 PDF](https://www.hkfsd.gov.hk/eng/source/safety/File2022.pdf) | **5.23 Smoke extraction system**，动态/静态系统；补风、流路、排烟口、设备与控制。5.27 为通风/空调控制的关联条目 | 当前目录标注 2022 为 current edition；引用时同时检查后续 circular amendments |
| [FSD Circular 4/96](https://www.hkfsd.gov.hk/eng/source/circular/e04_1996.pdf) | 烟控系统图纸/提交资料 | FSD 官方后续培训仍指向此文件；大 PDF 此次网页工具无法解析全文，尚未逐条核对 |
| [FSD Submission of Smoke Control Systems 培训资料](https://www.hkfsd.gov.hk/eng/source/licensing/FSD_Web_20210416_PG_02.pdf) | 处方式/消防工程设计路线、提交和验收流程 | 辅助理解，不替代现行 Code 与 circular |
| [BD Fire Safety Code 2011 (2024 Edition)](https://www.bd.gov.hk/doc/en/resources/codes-and-references/code-and-design-manuals/fs_code2011.pdf) | 逃生、防火分隔、消防进场、Part G 消防工程方法 | 法规背景和设计讨论；不是独立的排烟设备选型手册 |
| [FSD Circular 4/2024](https://www.hkfsd.gov.hk/eng/source/circular/2024_04_eng_20240426_164202.pdf) | 2022 Code 的修订记录 | 已发现后续修订，不能只看封面年份便认定无修订；本 circular 不等于所有修订汇编 |
| [Cap. 95B Fire Service (Installations and Equipment) Regulations](https://www.elegislation.gov.hk/hk/cap95B) | 消防装置法例背景 | 官方 e-Legislation 网页此次停在加载检测页，未读取现行条文全文 |
| [Cap. 123J Building (Ventilating Systems) Regulations](https://www.elegislation.gov.hk/hk/cap123J) | 通风系统法律背景 | 同上，需进一步打开现行合并文本，不能据本索引声称满足具体条文 |

5.23(i) 的 B.1、B.8、B.10、B.12 可作为设计讨论起点：同时考虑排烟/补风、高位抽烟及低位补风避免提前混合。B.7 对 atria/tunnels 明列个别工程商定例外，不能无条件套用一般布点规则。正式引用请回到原文并核对适用类别及后续修订。

报告中应将三类标准分开：作业验收条件（烟层高度 0.38 m）、实验验证指标（天花温度剖面等）、香港实际工程的设计/提交要求。烟层高度达标并不能单独证明 CO 或能见度安全。
