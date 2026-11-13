# 接回前的鲁棒更新与后报检验

2026-11-14，检索近期 *robust sensor track association*、*measurement rejection / skipped update*、*coasting and reassociation*、*variational Bayesian outlier tracking*。补读 4 篇 2025–2026 年纯传感器原文。另筛到依赖原始距离–多普勒图的 IEEE TAES 2026 [雷达跟踪论文](https://doi.org/10.1109/TAES.2026.3703385)，当前仅核到摘要，未纳入机制实证。

| 来源及覆盖 | 原文直接证据与作者主张 | MTAD 适配及未知 |
|---|---|---|
| E-ON290，Jiang、Battistelli、Chisci、Forti、Zhou，IEEE TSP 2025，§§II–V、表 V／VII。 [作者全文](https://www.researchgate.net/publication/392152525_Outlier-Robust_Centralized_and_Distributed_Variational_Bayesian_Moving_Horizon_Estimation) · [DOI](https://doi.org/10.1109/TSP.2025.3572912) | 在固定窗用伯努利–高斯污染模型联合估计状态和噪声参数，比较 Student t 和理想污染标注。10 节点、100 次仿真，位置 ARMSE 随 BG 窗 1／2／4／10 步约为 137.27／13.19／4.87／4.57 米。作者报告充分窗长下接近理想滤波。 | 新量测的数量和是否已消费直接改变归因可信度。模型知道污染生成分布，评估可用污染标签。MTAD 没有逐条故障标注，也没有理由把移动窗的延迟收益计给严格批前关联。 |
| E-ON291，Su 等，IET Radar, Sonar & Navigation 2026，§2.1 式 4、§3.2 式 19、§3.3 算法 1、§4.1 表 1。 [原文](https://doi.org/10.1049/rsn2.70250) | PDA 有效量测为空时保持预测状态及协方差，后续有有效量测再恢复更新。噪声协方差的当前估计不回写当前步关联或增益。高杂波且噪声突变时位置 RMSE 由 AR-PDAF 12.129 降至 9.287 米，理想已知参数 6.680 米。 | 对照从相同先验只删一次更新，记录状态和协方差的影响。作者条件是单模拟目标及给定杂波/噪声情形，跳过与强创新正常吸收都可能合理。 |
| E-ON292，Xiong、Kong、Cui，IET Radar, Sonar & Navigation 2026，§§3、4.2–4.4、表 5。 [原文](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/rsn2.70177) | 实际雷达视频约 3 秒一扫，AIS 只辅助标注。前后扫隐式关联加当扫框定位。固定模块仅把 IoU 换为 IoC，ID 切换 20→8，MOTA 89.63→89.75。总体对照的检测器并不全相同。 | 先固定候选与证据权限，再分别测短时读出和持续身份。MTAD 无雷达图框外观，无法重现原法。 |
| E-ON293，Zou 等，Sensors 2026，§§3.5、4.6–4.7、表 3。 [原文](https://www.mdpi.com/1424-8220/26/16/5103) | 在两个实际 FMCW 场景人为遮掉短段量测。保留预测状态后两个场景各重接 1／1，立即删轨各 0／1。论文也将公开数据上的目标中心条件评价与整链检测区分。 | 同一后报可以检查两条预测路径。人工缺报和自然报文偏移不同，单雷达参考轨、两个片段的结果不认证跨源误拦。 |

针对原 28 场，可检验的新增价值是同一批次保留两条仅差一个更新的预测分支，以缓存外后报检验状态误差和配对排序。C51 既有选择规则在每轨取接回前最后一条缓存外报告，严格同轨后报的先验预期是零。分歧后的较早报告可用不同问题检验更新机制，或者用两候选对侧的后报检查两组匹配。二者均不能代称为原涉事报告的同轨独立后验。图和原决策可能已依赖对侧观测，也须与当前形状的缓存血缘核对。
