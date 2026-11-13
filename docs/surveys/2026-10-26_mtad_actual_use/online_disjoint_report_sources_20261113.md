# 双报证据与历史复用

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-DISJOINT-REPORT-20261113`，2026-11-13。DE 为原文直接证据，SC 为作者主张，AI 为本项目推断，UN 为未核。

**E-ON208，Xu、Cui、Xiong，CIAG，IET Radar, Sonar & Navigation 2025。** 核 §1、§4 式26、§7–8。列举用两对航迹减系统偏差的前例，以航迹差值张量结合各轨建立关联表征。仿真以 AIS 生成雷达/ESM 输入，原文讨论多次增强同一方向可强化错配。SC 为其结构和反馈改善仿真；UN 为实船原生异步输入和本项目的报告复用。AI 是四条航迹的相对残差可抵消常值偏移，仍需用同批删除实报验证贡献。 [原文](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/rsn2.70044)

**E-ON209，Xue、Feng，Signal Processing 2026。** 仅出版方预览和 §3–5 摘录。共用过程噪声与部分重叠时段的投影会使局部估计相关。方法依赖先验与反馈以恢复信息项，导出 LDL 去相关，扩展到 GM-PHD 合并，验证为仿真。AI 是必须核后报预测是否包含前报，报文键不重仍可能共用过程和局部滤波状态。UN 为 MTAD 中的实际互协方差，不能据预览复现作者方法。 [出版方](https://doi.org/10.1016/j.sigpro.2025.110119)

**E-ON210，Sharma 等，IET Radar, Sonar & Navigation 2026。** §6.4 在不同视野覆盖下200次蒙特卡洛比较 HMD-GA、CI、ICI，指出仅由一个节点实际测到的估计在共享融合记忆后可能高度相关。准确度与一致性受覆盖影响。AI 是报告来源不同不保证新观测独立。UN 为本项目回放中的共享误差量。 [原文](https://doi.org/10.1049/rsn2.12672)

**E-ON211，旧来源定向复核。** Fontana 等 TSP 2025 的 §II.C、IV.C、V 将两时刻联合测量和单端部分测量分别建模，100次蒙特卡洛，较长窗口和杂波场有收益，短窗位置误差趋近；仿真给了短航迹测量内的对应及噪声。Draves 等 IEEE MFI 2026 的 §III.D/H 按每源最近更新记创新并按轨迹键去重，仿真最终存活假设成绩受剪枝覆盖影响。AI 是保留来源和同延迟对照，无依据把两个归一残差直接当独立概率相乘。 [TSP 原文](https://arxiv.org/html/2504.08421v2) · [MFI 原文](https://arxiv.org/html/2610.20290v1)

`next_skill=deep-read Mode C`。
