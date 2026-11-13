# 批前对侧新报、缓存来源和位移证据

2026-11-13。C-ON49 的 131 次真边变远中只有 10 次的旧历史比较实际用过分歧后对侧报文。研究问题是在旧缓存剔除后，原决策时钟上的相对位移是否增加候选排除信息。DE 为原文直接证据，SC 为作者主张，AI 为适配判断，UN 为未知。

| 来源、实读范围 | DE／SC | AI／UN |
|---|---|---|
| E-ON256，Draves 等，MFI 2026 作者稿 §§II-B、III-D/H、IV–VI | DE：传感器本地航迹携带持续 ID 与量测，异步融合节点按航迹 ID 集合去除重复分区。保留尚无新量测更新的假设。星座仿真显示过度剪枝、弱几何仍会使局部航迹难以归入发布假设。 | AI：把去重单位下沉为原生轨键加时刻，分别量化剔除后失去支撑和已有排序改变。UN：航迹 ID 集合去重未证明逐报误差独立。 [作者全文](https://arxiv.org/html/2610.20290v1) |
| E-ON257，Guan 等，IET Radar, Sonar & Navigation 2025，§§2.2、3.2.2.1、4.4–4.5，式11–13 | DE：运动速度和方向由同一组相邻坐标差确定，与位移等价；使用截至当前的少量原点训练伪点聚类。交汇及平行条件下关联变难，证据来自合成空中航迹。 | AI：位移和由它导出的航速、航向只算一个来源。保留异步括点和剩余实报数。UN：其训练式方法的结果在 MTAD 严格批前位移下未证。 [期刊全文](https://doi.org/10.1049/rsn2.70099) |
| E-ON258，*A Multi-Feature Adaptive Association Method for High-Frequency Radar Target Tracking*，Remote Sensing 2026，§§2.3、3.3.1、3.3.3 | DE：方向余弦配合位置及多普勒作关联门，沿海实测的消融中加入方向能减少身份切换和断裂，但漏检可增加，转向船尤其受匀速假设影响。 | AI：分别检验发现错接与保护正确接回。原文当前多普勒、航迹滤波方向和长序列阈值均不照搬。 [期刊全文](https://www.mdpi.com/2072-4292/18/2/321) |
| E-ON259，Wan 等，IJTST 2025，§§2.1–2.3、3.1、4.1，已有 MTAD 使用登记后的定向复核 | DE：DTWCM 对位置、速度、航向计算序列相似并做全组指派。两段完整共同覆盖需超过 120 秒，实验由十个母 AIS 场景二次分源抽样并加噪。SC：异步和交叉密集情况下多特征 DTW 提升分组。 | AI：参照候选共同时间支撑与同图竞争，固定两端避免换窗口掩盖缓存剔除。UN：完整段 DTW 与 MTAD 当批处理的收益不可直接相比。 [作者全文](https://www.sciengine.com/cfs/files/pdfs/view/2046-0430/9A6B4DB4617340DEAD54549EFFA7E657.pdf) |
| E-ON260，Chang 等，JAIF 2025 年卷，2026-01 定稿，§§I、IV，表 I。Xia 等，ISIF FUSION 2026，§§II-A/B、IV-A、V | DE：PRIMEX 用唯一来源身份编码交集与并集。在条件独立的分解中，公共因子需要从融合乘积中除去。动态共同过程噪声下，即使来源可追溯也需要近似。有限通信轮次下近似融合有时输给协方差交集。 | AI：去掉明确复用的原生坐标后重算同一区间，同时保留缺支撑。UN：估计融合实验没有验证纯位移的身份判别。 [JAIF 原文](https://isif.org/files/isif/2026-05/encoding_inofrmation_lineage-scalable_distributed_fusion.pdf) · [FUSION 作者稿](https://arxiv.org/html/2604.21618) |
| E-ON261，Su 等，IEEE T-ITS 2025，§§III–V、表 I | DE：用道路上、下游片段的通行时间差及横向运动做断点匹配。highD 来源的缺口消融中，完整配置可维持至 200 米的较高关联准确率，去通行时间差后在大于 50 米处明显下滑。原文给出离线和按分钟批处理条件，highD／NGSIM 为视频生成轨迹，另有 TJRD。 | AI：对异步位移评价固定同一时钟并拆除时间和坐标贡献。UN：分钟批处理结果无法说明原接回批是否能拒错且保真。 [IEEE 期刊](https://doi.org/10.1109/TITS.2025.3586924) · [作者全文](https://www.researchgate.net/publication/393800314_Generator-as-a-Matcher_Joint_Optimization_of_Tracklet_Matching_and_Gap_Filling_for_Sparser_mmWave_Radar_Placements_on_Smart_Freeways) |

比较相对位移时，固定平移从各端位置差中抵消，旋转、时变偏差、共用上游数据和插值误差仍可能影响。一个原生点对位移的净贡献由右端插值权减左端插值权确定。按轨键与时刻去除旧缓存，再保持相同两端，才能区分新报带来的可计算性与分差方向。 [C-ON49 逐窗证据](../../reports/2026-11-13-online-rejoin-witness.md)
