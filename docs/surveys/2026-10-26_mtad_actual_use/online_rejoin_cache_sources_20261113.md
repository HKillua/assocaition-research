# 纯传感器跟踪中的缓存时距、持续性与当批几何

2026-11-13。问题是同刻几何支持两组候选之一时，旧历史何时可以继续参与判断。检索2025–2026纯LiDAR、海面雷达和异步多假设，核量测来源、记忆时钟、动作和评价。SC为作者主张，DE为直接证据，AI为本项目推断，UN为未知。

|来源与阅读范围|DE 与 SC|AI 与 UN|
|---|---|---|
|E-ON235，Zeng 与 Ramezani，Measurement 2025，全文 §§4.3–4.5 式26–28、5.3表4/7|纯LiDAR由跨帧框重合传递置信，按新检测置信更新，几何、速度、点云特征与距离分开。训练集消融中去几何IDS 10→746，动态／线性／无置信IDS 10／205／35。|需要用固定当前几何对照记忆。跨帧规则依赖点云框、节奏及训练集调参，不能推出 MTAD 最佳年龄。 [全文](https://transportlab.sydney.edu.au/wp-content/uploads/2025/09/RZ-MR-2025.pdf) · [期刊](https://doi.org/10.1016/j.measurement.2025.117864)|
|E-ON236，Yi 等，IROS 2025 纯LiDAR动态分割，会议稿 §§III-E/IV|轨迹管理分别记录关联次数和距末次关联时间，短期静态／动态状态用 Beta 累积。候选形成与删除分别使用持续／未关联时间；动态候选以点云描述子和当前几何指派。|履历长度和最近支持时刻是不同量，持续可来自反复使用同一来源。论文评价任务和可用点云描述子与 MTAD 不同。 [会议稿](https://www.research.visual-navigation.com/static/documents/Felix/IROS25.pdf)|
|E-ON237，Schäfer 等，Advanced Intelligent Systems 2026，全文 §§5.7/5.9/6|路侧纯LiDAR将年龄、成功关联比例、形状和运动稳定性分开计入存在估计。不同可见区使用不同过期时间，实验只有参考车有高精度轨迹。|缺失实际扫描时钟和可见域时，MTAD 不能把长间隔当成多次漏检。年龄与成功比例无单独身份消融。 [作者全文](https://publications.rwth-aachen.de/record/1036708/files/1036708.pdf) · [示例代码](https://github.com/bassamlab/Algorithms-for-Perception)|
|E-ON238，Yoo 等，CVPR Findings 2026，作者稿 §§3.2–3.4/4.4表4|KITTI单目标任务，简单扩长记忆成功率70.5→69.2，加入时序和循环一致后71.8。|说明历史兼容性需要单独验证。任务给定首帧对象且使用点云，不能当持续多目标ID结果。 [会议](https://openaccess.thecvf.com/content/CVPR2026F/html/Yoo_Temporally_Consistent_Long-Term_Memory_for_3D_Single_Object_Tracking_CVPRF_2026_paper.html) · [作者全文](https://arxiv.org/html/2604.13789)|
|已有 Draves 等 MFI 2026，作者全文 §§III-C/D、IV/V|分组保留母假设的关联历史和ID，另用最新各源创新评分；评价模拟传感器场景，终局最优历史与顺序对照权限不同。|借鉴分开轨迹历史与新证据。只比较 MTAD 原决策时刻，避免事后最佳历史和真值参与状态。 [作者稿](https://arxiv.org/html/2610.20290)|
|已有 Jin 等 E-ON159，Remote Sensing 2026，全文 §§3.3/4|海面雷达的历史轨迹分布、实时距离和方向余弦分工。历史分布可能对突变迟钝，删减方向一致性消融体现切换与漏检的取舍。|历史时距只可限制适用性，持续时间也可能延长错误配对。原生 Doppler、300秒雷达帧和带速度的AIS对照不同于 MTAD。 [全文](https://www.mdpi.com/2072-4292/18/2/321)|

本轮把缓存计算时刻、末条支撑到达时刻、四端共同右端、两组配对的连续发布时长分开。当前实报和屏蔽几何都支持旧 KF 配对，才称当批几何方向稳定。以上给出可检验线索，未给出可直接迁移的身份概率。 [Mode C v56](online_causal_replay_mode_c_20261111.md#v56-缓存的可用性与身份判别)
