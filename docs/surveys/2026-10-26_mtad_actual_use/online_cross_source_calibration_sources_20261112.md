# 纯传感器跨源误差的均值、离散与参照

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-CROSS-SOURCE-20261112`。2026-11-12 定向核读。SC 为作者主张，DE 为可核对事实，AI 为迁移推断，UN 为未知。

## E-ON190／191 实船独立参考

Bauer 等，JMSE 2026，§4–8、表9–10。岸基 LiDAR 的几何由 RTK 标定，AIS 船体按尺寸、航向与天线位置重建，用人工轮廓配准做评价。71 次过船，69 次常规航行的横／纵向有符号中位为 +0.62／−1.81 m，绝对 P95 为 4.68／12.41 m。本实验的接收侧时差量级低于 0.5 m。SC 是纵向误差还受动态定位、参考点和静态船体字段影响。Fukuda 等（Journal of Navigation，2025 在线，2024 刊期，项目旧证据 E335）§3、表4则用船上 RTK 发现最大约117 m，按收发时差纠正后，三航段小于10 m的比例是99.0%、87.2%、100%。AI 是先核有符号残差和中心化离散，并保留时间来源；这两类独立参考在 MTAD 的航迹输入未取得。UN 是源内位置是否共享同一物理船体参考点。 [Bauer 全文](https://www.mdpi.com/2077-1312/14/20/1879) · [Fukuda 全文](https://www.cambridge.org/core/journals/journal-of-navigation/article/study-on-ais-positional-error-analysis-and-transmission-frequency-requirements-of-attitude-data-for-future-vessel-monitoring/E8EE865AAFB8896C0FF1E44F50B3E584)

## E-ON192／193 误差一致性与可观测性

Marom、Bar-Shalom、Milgrom，JAIF 2025，表II–III、§IV 图2–6。5000次含已知过程噪声的双基地测量仿真，RMSE 与 ANEES 分开。加入多普勒后部分一阶算法估计更准或门更小却失去一致性，二阶变换或完整测量协方差适配才改善部分一致性。DE 有模拟状态真值；AI 是不能用门宽或命中率反推跨源方差合适。Brunson、Wang，Sensors 2025，§3–4。以 GNSS 和 IMU 逐传感器观测建立系统误差状态、归一化协方差与可观测性预分析；平面轨迹示例30状态仅22可观测。SC 是运动激励与传感器布局应先核。AI 是两个源的相对残差只能约束两者合成误差及相关项，无法分出每个源的绝对偏差及方差。 [JAIF 全文](https://isif.org/files/isif/2025-06/Consistent-Bistatic-Radar.pdf) · [Sensors 全文](https://www.mdpi.com/1424-8220/25/10/3239)

## E-ON194／195 匹配与标定的耦合

Fan 等，Sensors 2026，§2.2、3.1–3.3。使用已同步且已配对的 MTDSP 雷达–AIS 量测，以船只分割并将相邻时刻归在同一划分。范围 MAE 514.76→7.77 m，方位 1.37→0.14°。SC 是几何条件均值能解释大部分系统误差，UN 为跨系统和实际在线效度；其输入含本项目没有的雷达测距测角与物理参考，其结果也不提供可迁移的协方差标定。Hao 等，IEEE Sensors Journal 2025，仅出版方摘要。JPDA、稀疏假设检验及KL软匹配交替优化偏差和关联，仿真。可核主张是关联与偏差估计互相影响，原文设置和消融未知。AI 是先用早期资格确定锚，再取之后新报的残差，避免同一报文自选自证。 [Fan 全文](https://www.mdpi.com/1424-8220/26/12/3782) · [Hao 摘要](https://ieeexplore.ieee.org/document/10858647/)

对 MTAD 的接入条件为严格早于决策的外部片段及新报、原候选和资格可复核、仅估相对位置差。共同位移可提供不同于绝对位置的资格核验，物理独立参考仍缺。`next_skill=deep-read Mode C`。
