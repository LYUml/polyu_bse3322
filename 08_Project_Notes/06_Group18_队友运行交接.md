# Group 18 FDS 运行交接 · 2026-11-22

**先续跑三个已接近结束的 0.96 m³/s 工况**，再复核关键场景的竖向网格。原机已暂停，六个算例均由 FDS 正常响应停止请求并保存断点。下表的秒数是停止前的最后设备记录，恢复后以求解器实际读入的断点为准。

## Windows 快速开始

需要 Windows、Python 3.8 或以上、FDS 6.10.1（与原机相同；首选 PyroSim 2026 随附版本）。后处理使用 Node.js 18 或以上。以下命令在 PowerShell 中运行。一次只启动同一 CHID 的一个副本。不同工况可以在不同终端并行。

```powershell
git clone https://github.com/LYUml/polyu_bse3322.git
cd polyu_bse3322
$case = 'inlet44_1_0p02_0p24_0p96_120'
$fds = 'C:\Program Files\PyroSim 2026\fds\fds.exe'
```

**只有 GitHub 仓库时，从零跑。** 先执行检查，再启动。按本机实际安装路径调整 `$fds`。如 Python 启动器是 `py`，将下方的 `python` 换成 `py -3`。

```powershell
python 06_Tools/run_handover_case.py $case --fds $fds --check
python 06_Tools/run_handover_case.py $case --fds $fds
```

**拿到断点包时，从已保存进度跑。** 请原机负责人单独传送 `Group18_20261122_six_checkpoints.zip`（约 242 MiB）；GitHub 中只有输入、工具和精选结果。用新的克隆目录，将压缩包放入其根目录。完整解压会得到六个 `04_Results/<CHID>/` 子目录。不要解压到已经在运行或有同名结果的目录中。

```powershell
Get-FileHash .\Group18_20261122_six_checkpoints.zip -Algorithm SHA256
Expand-Archive .\Group18_20261122_six_checkpoints.zip -DestinationPath .
python 06_Tools/run_handover_case.py $case --fds $fds --resume --check
python 06_Tools/run_handover_case.py $case --fds $fds --resume
```

压缩包 SHA-256 为 `7ba3ad03d6915c7ed21789a3aa73f5003362e19a813e89caffad665c14f492c6`。包内保留原输入、设备历史、切片、求解日志与各组非空的单网格 restart 文件；交接包省略原机停算标记。启动脚本为续跑生成带 `RESTART=.TRUE.` 的输入，维持原 CHID。原机没有替队友实际重启求解器。若目标机版本或读档不兼容，保留报错和断点，在另一份干净克隆中使用从零跑命令。

## 工况清单

| 顺序 | CHID（直接赋给 `$case`） | 已记录模拟秒数 / 120 | 用途 |
|---|---|---:|---|
| 1 | inlet44_1_0p02_0p24_0p96_120 | 103.00 | OP-1 基准烟炱，降低风量 |
| 2 | inlet48_6_0p1_0p24_0p96_120 | 102.50 | OP-6 高烟炱，降低风量 |
| 3 | inlet48_6_0p05_0p24_0p96_120 | 98.01 | OP-6 中烟炱，降低风量 |
| 4 | inlet44_1_0p02_0p24_1p28_z38_120 | 20.00 | 已选方案最小余量场景，竖向 19→38 层，跑满 |
| 5 | inlet44_1_0p1_0p24_0p96_120 | 5.00 | OP-1 高烟炱，降低风量 |
| 6 | inlet48_1_0p02_0p24_1p28_z38_120 | 40.00 | 两端 0.48 m 布局的四门对照，跑满 |

若 0.96 m³/s 的已测门况均通过，再从零启动另两个预设组合 `inlet44_1_0p05_0p24_0p96_120`、`inlet48_6_0p02_0p24_0p96_120`。任一场景筛查失败即可排除此风量下的整套六场景方案，余下降风量工况按诊断价值决定。不要启动旧的 `run_design_queue.ps1`；它针对更早的矩阵。

## 验收与回传

启动脚本每 5 秒检查降风量筛查候选。任一有效层高记录低于 0.38 m 时，它保存同站能见度、CO、支管流量和相邻帧，写入本组 `.stop` 文件请求 FDS 正常结束。两个网格对照均运行到 120 s。启动脚本运行期间保持终端打开。

- **早停候选**：保留 `screen_failure.json` 与设备输出，记录首次越限位置、时刻及已覆盖时段。不要将截断数据用于全程累计时长。
- **正常完成**：检查末行有 `FDS completed successfully`，设备记录覆盖 0–120 s，再执行下列命令。脚本会检查时间连续性、工况和单位；退出码非零的结果不归档为通过。
- **交回结果**：回传逐站 CSV、摘要 JSON、求解器版本、异常说明和输入差异。大文件留在 `04_Results` 本地或单独传送。若多人协作，先说明各自承接的 CHID，避免重复计算。

```powershell
$dir = "04_Results/$case"
node 06_Tools/summarize_design.cjs $dir 0 1> "$dir/stations.csv" 2> "$dir/summary.json"
if ($LASTEXITCODE -ne 0) { throw "结果未通过完整性检查，请查看 $dir/summary.json" }
```

## 已有结果

- 1.28 m³/s 总排风、0.24 m 垂壁，OP-1 两端开口各高 0.44 m、OP-6 各高 0.48 m。原网格下六个场景均跑满并通过，八站最低 0.4425 m；降低到 0.96 m³/s 的可行性有待上述验证。[六场景汇总](../05_Calculations/door_preset_1p28_six_scenarios.csv)
- OP-6、106.2 kW 丙烷墙面对照已完成。90–120 s 顶棚平均温升偏差从绝热组 +330.3 K 变为代理板材组 −66.1 K。该项不需重跑。[墙面结果](../05_Calculations/op6_106_board_doorflow_90_120.json)
- [报告草稿](../07_Report/Group18_review_draft.md) · [当前诊断与设计记录](05_Group18_当前执行与诊断.md) · [原始作业](../01_Assignment_Brief/Project_Topic_1B_Smoke_Extraction.pdf)
