# Group 18 演示视频

展示时，先播放 Task 1 温度场介绍四门全开的基线，再播放 Task 2 三维烟气观察排烟布局。两段都是从房间长侧面正视。Task 2 三个正视版本使用同一次 OP-6 计算，总排烟量为 1.12 m³/s，烟炱产率为 0.05 kg/kg。它们覆盖 0–120 s，右下角为模拟时间。

| 演示用途 | 打开视频 | 画面内容 |
| --- | --- | --- |
| Task 1 实验对照 | [OP-1 温度场](OP1_106_coarse_native_temperature.mp4) | 106.2 kW 丙烷火，粗网格，四扇侧门打开 |
| Task 2 首选 | [OP-6 三维烟气](OP6_1p12_y005_front_soot_interior.mp4) | 灰黑色烟羽、R1 侧门和两道挡烟垂壁 |
| Task 2 与 Task 1 对照 | [OP-6 温度场](OP6_1p12_y005_front_temperature_interior.mp4) | 房间纵向中心面，沿用 Task 1 的 20–870 °C 温标 |
| Task 2 烟气分布复核 | [OP-6 消光系数](OP6_1p12_y005_front_extinction_interior.mp4) | 同一中心面，固定色标 0–0.1 m⁻¹ |

## Task 2 答辩片段

两段视频取自 OP-6、总排烟量 1.12 m³/s 的竖向加密网格算例。灰度底图为中央纵剖面的烟炱消光系数。彩色标记与下方曲线同步显示相应 FDS 设备的数据。极值取自各工况 0–120 s 的八个测点，画面在极值时刻额外停留 4 s。

| 视频 | 剪辑覆盖的模拟时间 | 答辩时可指认的读数 |
| --- | --- | --- |
| [远端热烟层最低位置](OP6_1p12_y005_thermal_layer_minimum.mp4) | 104–118 s，烟炱产率 0.05 kg/kg | 113.0 s 时，x = 6.1 m 的热界面降至 0.4358 m，比半高线高 55.8 mm。[测柱数据](../../05_Calculations/inlet48_6_0p05_0p24_1p12_z38_120_stations.csv) |
| [火源附近 CO 峰值](OP6_1p12_y010_peak_CO.mp4) | 0–8 s，烟炱产率 0.10 kg/kg | 3.0 s 时，x = 3.6 m、z = 0.38 m 的探头达到 32.83 ppm。[探头数据](../../05_Calculations/inlet48_6_0p1_0p24_1p12_z38_120_stations.csv) |

## 早期视角

| 视频 | 用途 |
| --- | --- |
| [PyroSim 三维烟气](earlier_views/OP6_1p12_y005_pyrosim_smoke_volume.mp4) | 回看此前导出的原生视角 |
| [PyroSim 消光系数切片](earlier_views/OP6_1p12_y005_pyrosim_extinction.mp4) | 与先前带 HVAC 管线的截图对应 |
| [烟气后处理预览](earlier_views/OP6_1p12_y005_smoke.mp4) | 早期可视化，采用独立后处理渲染 |
