# 首报距离门的留场验证来源

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-HELD-GATE-20261111`，2026-11-11，定向原文阅读。问题来自 E-ON43 的三场结果。检索覆盖场景偏移、选择性拒配、雷达配准及跨源船舶位置门，纳入直接影响本轮比较设计的六篇原文。SC 为作者主张，DE 为原文直接证据，AI 为本项目推断，UN 为未知。

|编号、原文与阅读位置|SC 与 DE|AI 与 UN|
|---|---|---|
|S-ON77 Koh 等，WILDS，ICML 2021，§4.1、§5 表1、§7。 [原文](https://proceedings.mlr.press/v139/koh21a/koh21a.pdf)|SC 真实应用的域间变化应按数据生成单位留出。DE 固定训练时，同域到留域 iWildCam 相机位置 macro F1 47.0→31.0，Camelyon17 医院准确率 93.2→70.3。单个留出医院给出的环境证据有限。|AI MTAD 按场景一次抽样、报告逐场结果及支持量，避免大场遮盖小场。UN Level1 留场仍共享生成链，不能据此推断真实部署域或身份独立。|
|S-ON78 Gulrajani 与 Lopez-Paz，DomainBed，ICLR 2021，§3.1、§5.2 表4。 [原文](https://arxiv.org/pdf/2007.01434)|SC 选参协议是方法的一部分。DE 同一 ERM 在七数据集平均准确率中，源域验证选参 67.0%，留一源域 63.8%，目标域 oracle 68.9%。控制选择协议后各算法和 ERM 的平均差距很小。|AI 在读留场标签前冻结场景、两门、校正及回退。两门共享每场已到的无标签校正。UN 无法从此工作推断 MTAD 门限值或跨场共享偏移参数。|
|S-ON79 Angelopoulos 等，Conformal Risk Control，ICLR 2024，§§2.1、2.3、4.1 和附录 D 图6。 [原文](https://proceedings.iclr.cc/paper_files/paper/2024/file/f3549ef9b5ff520a7e41ff3cc306ab2b-Paper-Conference.pdf)|SC 在有界单调损失和可交换样本下可控制期望风险。DE 非单调反例可接近损失上界，模拟协变量偏移使常规方法失去风险控制，重加权方案要求关于偏移的额外信息。|AI 嵌套门收紧时，错接数必然不增，需同时核减错幅度、原正确流失和接收内错接率。UN 同场出生相关，没有足够条件提供 conformal 或分布无关保证。|
|S-ON80 Karniely 与 Siegelmann，TAES 2000，§II-B、II-E。 [原文](https://binds.cs.umass.edu/papers/2000_Karniely_IEEETransAeroElecSys.pdf)|SC 在多雷达注册中，偏差会降低同目标进入关联门的机会，跨源配对受影响尤其明显。DE 在同历元、已知误差协方差与近高斯条件下，中心卡方门的名义覆盖只描述同目标边。作者讨论区域和条件变化带来的注册误差差异。|AI 校正后的距离收紧仍可能把真近邻推到门外。用同池的校正前后控制、校正支持和真候选进入阶段定位代价。UN MTAD 首报异步，误差协方差未知，无法把名义覆盖用于 1 km。|
|S-ON81 Zhang 等，Journal of Navigation 2017，§4.1.1 式25–26、§5.3 表5/7。 [原文](https://www.researchgate.net/publication/309330510_Multi-Feature_Maximum_Likelihood_Association_with_Space-borne_SAR_HFSWR_and_AIS)|SC 海事关联粗门应受传感器误差与特征约束。DE SAR–AIS 使用依分辨率和实验统计确定的 2 km 平面门，HFSWR–AIS 用量程、方位与径向速度各自成门。海试已接收 SAR–AIS 的位置差均值 0.53 km，受 2 km 门截断。局部实测中最近邻和纯位置 ML 都受到疑似虚警牵引，多特征对照使用船长和径向速度。|AI 以完整首报人口和真机会追踪门外正确损失，保留门内近邻歧义。UN 原文没有独立留场的数值门表现，依赖的传感器特征也不具 MTAD 首报权限。|
|S-ON82 Zhang 等，Acta Oceanologica Sinica 2018，§5.2、表2。 [原文](https://www.researchgate.net/publication/326712371_Vessel_fusion_tracking_with_a_dual-frequency_high-frequency_surface_wave_radar_and_calibrated_by_an_automatic_identification_system)|SC 合作 AIS 校正的双频雷达联合跟踪改善十艘船的跟踪。DE 表2 两单频和校正后双频量程均值误差为 0.54/0.65/0.49 km、漏失 2/3/0，误差只用未漏轨，正文的漏失叙述与表计数存在差异。|AI 支持把配准和门限效应分开测。UN 实验同时改了校正和融合，用合作 AIS 校准并评价，无法隔离校正增益或外推无 AIS 的 MTAD 首报。|

可迁移内容为按场景留出、冻结规则、同时报告覆盖和风险、以校正前后定位损失。E-ON43 为 1 km 的唯一直接数值依据，六篇原文均无 MTAD 条件下的定量支持。S-ON81/82 同团队的两次不同海试不能当独立研究团队复现。留场现象和竞争解释进入 Mode C v13。 [在线 Mode C](online_causal_replay_mode_c_20261111.md#v13-首报门限的留场问题)

## 补充的海事反例

S-ON83 Kazimierski，IET Radar, Sonar & Navigation 2017，§§3.1、5.1–5.2、6.1–6.3 表1/3/4。SC 按目标到雷达的距离调整位置门可保留更多常态真配。DE 波罗的海雷达与 AIS 同时采集后离线处理，671 个已配对真样本中 200 m 固定门接收 537，104–1540 m 线性门接收 650。在另一组 200 个真实正例加 200 个单字段加偏差和噪声的人工负例中，同两门的总体正确率为 72.5%／62%。由表3的总接收数与正确率回推真接收 165／194、假接收 75／146。三票历史在原 671 个真例仅令线性门 650→654。AI 只评价已知同目标会遮蔽放宽门的误接代价，应保留自然缺真和竞争候选的人口。UN 未测真实负例、异步首报、跨场或 MTAD 米制门的泛化。此补充反例未改变冻结计划。 [原文](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-rsn.2016.0409)
