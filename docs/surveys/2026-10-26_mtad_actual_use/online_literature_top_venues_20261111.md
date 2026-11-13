# MTAD 在线观测第三轮顶会顶刊原文分析

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-TOP-VENUES-20261111`，2026-11-11，partial。范围是海事传感器实测、异步与配准、在线结果可用性、关联拒配与评价。各条记录本轮实际读取的版本与位置，SC 为作者主张，DE 为直接证据，AI 为面向 MTAD 的推断，UN 为缺证据。所有数值依各作者原协议。下游为 [deep-read Mode C v5](online_causal_replay_mode_c_20261111.md#v5-顶会顶刊证据与问题筛选)。

## 拒配与评价

### S-ON35 Lowe，最近／次近匹配，IJCV 2004

阅读作者原文 §§7.1–7.3，图 11。问题是局部图像描述符的最近邻是否可信。DE 用最近与次近欧氏距离比识别歧义。有同物多张训练图时，次近按已知的不同物体选。40,000 描述符，随机缩放旋转、30° 深度转动和 2% 图像噪声，比例大于 .8 的剔除移走 90% 假匹配及少于 5% 真匹配。SC 次近可代理特征空间的局部竞争。AI MTAD 的低维位置、未知同船片段归并、目标可能完全不在候选中的条件均不同。特别是同目标的两个片段可能压小间距，唯一错误候选也可能显得很确定。UN 同一出生和首选下，比较竞争与绝对距离的接收风险，尚需目标域证据。作者源码和数据未运行。 [作者原文](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf)

### S-ON36 Geifman 与 El-Yaniv，选择性分类，NeurIPS 2017

阅读会议原文 §§2–5，算法 1、图 2、表 1–3。DE 固定已训练的分类器，通过独立标注校准集、置信排序、二项风险界来选拒绝阈值。CIFAR-10 的目标风险 1%、置信失败率参数 .001 时，保留约 78.56% 的测试样本，测试错误率 .92%、上界 .99%。同节朴素按训练误差定阈在 1000 次随机划分中超过一半违反测试目标风险。图 2 的阈值取舍随置信打分和数据而异。SC 作者主张在相应抽样假设下可控制接收集合的风险。AI 在 MTAD 上可先固定首选与接收数检验排序价值，重复船、场内相关、部署分布未知使论文保证不可移植。UN 真实目标域风险预算、独立校准分布与部署阈值。 [会议原文](https://papers.nips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf)

### S-ON37 Luiten 等，HOTA，IJCV 2021

阅读正式版 §§5–8、10–11，图 5、18，式 33–35。DE 先逐帧配对，分别计算检出与跨帧关联的准确性。OHOTA 对每个当前正确检测只用截至当时的预测前缀，也允许用已修订的历史预测。图 5 有全局关联同分、碎片长度不同的构造例，FA-HOTA 增加同一连续段的贡献。§11 有 230 人、2075 次有效比较，刻意挑指标排序相反且差距明显的例子。排除平局后，HOTA 与人一致为 61.6%（对 MOTA）及 72.0%（对 IDF1）。SC 作者认为可兼顾关联与检出。AI 评分所用前缀与原版输出时间必须各自记录。UN MTAD 米制门、独立参考及原版／改版的评分口径。前轮仅提 §8，本轮增加定义和实证限制。 [正式原文](https://link.springer.com/article/10.1007/s11263-020-01375-2)

### S-ON38 Li 等，TETA，ECCV 2022

阅读会议版 §3.1–3.2、§5.1，图 4/8/9、表 1。DE 不完整标注下，以真标注为锚把预测纳入局部 IoU 簇，簇内的未匹配预测可算假阳性，簇外保留为不可判。TAO 一段视频的复制轨迹压力例中，TAO track mAP 0→62.9，Federated HOTA 4.2→68.7，TETA 47.6→13.8。图 8 分析 TAO 到 BDD 有完整标签的重叠类别，仍需对象可比性。SC 作者主张局部簇缓解把所有未知预测判错和全部忽略这两种偏差。AI MTAD 参考未覆盖的目标秒应留账，不能把簇外目标当作已证实虚警。UN 无参考和误并的关系、空间聚集时锚点能否提供足够判别。 [会议原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136820486.pdf)

### S-ON39 García-Fernández 等，GOSPA 与 T-GOSPA 准度量，IEEE TAES 2026

阅读正式版 §§III–IV、VII，式 2–4/38、引理 5/10、图 1/5–6。DE 在定位门固定时，以 `ρ` 分配漏目标与假目标代价，轨迹扩展另计跨时刻换配。固定基准距离时，改变 `ρ` 不改最优匹配集合与定位／换配分量，仍可改变总评分排序。图 1 构造例随权重可逆转。模拟比较 TPMBM、PMBM、GLMB，`ρ=.3/.5/.7` 均为同一排序，但目标消失后重罚假目标放大误报尖峰。SC 作者提出按应用的错漏代价取权重。AI 在 MTAD 的错并和拒配代价未知时可先逐项报告，权重后定会混淆结论。UN 真实应用代价、米制门及参考人口，作者场景代码仅定位未运行。 [机构正式 PDF](https://research.chalmers.se/publication/551896/file/551896_Fulltext.pdf) · [正式出版](https://ieeexplore.ieee.org/document/11489514/)

## 传感器配准与观测可辨性

### S-ON40 Cormack 等，雷达与红外联合配准及融合，IEEE TAES 2020

阅读机构接受稿 §§II–IV，式 2/3/5/6/9/13、算法 1、图 5–12。DE 以雷达测距和方位为锚，顺序处理已知异步时间的雷达和仅方位 IRST。每个相对旋角假设运行 PHD/Panjer，待配准 IRST 到达才更新角度权重。50 次重复的同轨迹仿真中，Poisson 杂波在检出率 .99 时估配准两法 RMSE 21.72/20.04 m，在 .85 时 32.56/30.72 m。负二项杂波下普通 PHD 要更高检出率，Panjer 在 .7 已给出较一致配准。未校准融合可比雷达单源更差。海试约 50 s、约 2 km 单目标，雷达扫描 2.5 s，每雷达间隔选约三次 IRST，估偏 1.5–2°，更新更密但两处重获距离时出现位置跳变。SC 作者主张非同步方位源可补轨迹更新并估配准。AI 额外到达可以改善输出频度，同时只约束部分状态。UN 实测独立角度和位置真值、持续 ID、物理抵达日志。 [机构接受稿](https://researchportal.hw.ac.uk/files/25260122/08771381.pdf)

### S-ON41 Zhang 等，多量测向量的未知置换恢复，IEEE TIT 2022

阅读 NSF 正式 PDF §§I–IV、VI，式 2、定理 1/5/6/7、图 3–5。DE 设计矩阵已知，多列共用同一未知行置换，噪声独立。定理分别约束总能量和信号稳定秩。高稳定秩能降低恢复所需信噪比的量级，重复同一低秩信号主要累积能量。未知信号的定理 7 另有限定置换距恒等的范围等条件。图 5 未知信号仿真里，量测列 m=15 所需 SNR 约 1–10，m=50 降到 1 以下，数值受具体构造限制。SC 作者将益处联系到多样性。AI 已见新报文要提供非冗余信息且共享对应才能借鉴，位置派生速航不能增加独立证据。UN 真实船运动激励、出生退出使候选集变化后的对应结构。 [正式 PDF](https://par.nsf.gov/servlets/purl/10384334)

### S-ON42 Taghavi 等，从局部航迹估计传感器偏差，IEEE TAES 2016

阅读作者稿 §§III–VI，式 29–45、图 5、§VI-A/G、表 I。DE 已关联连续局部状态和协方差用于重构等效测量，融合其它雷达构成相对参考，递推最小二乘估计偏差。五雷达、16 目标仿真，同钟，设 20 m/1 mrad 偏差，L=10 表示稀疏传输。修正后误差介于单源和已知偏差融合。L=1 可导致奇异，需去相关估计。运动模型失配以过程噪声膨胀处理，选取无统一规则。SC 作者主张可在中心用局部航迹重构有效配准信息。AI 仅有处理后的经纬、没有状态协方差和正确对应的 MTAD 缺关键输入。UN 未知归属、真时偏和真实链路下的效果。 [作者稿](https://arxiv.org/pdf/1603.03449) · [正式 DOI](https://doi.org/10.1109/TAES.2015.140574)

### S-ON43 Akrout 等，双线性未知标签感知，IEEE TSP 2025

阅读作者稿 §§III–V、图 4–7。DE `Y=UAX+W`，已知设计 `A`，所有列共享一方阵置换 `U`。Bi-VAMP 使用行列一对一约束和近似状态演化。图 4 在 20 dB、N=160/M=100/R=10 的条件下，最强参照仅在置换范围不超过 N/2 时恢复。任意大置换 N≥10 的作者对比没有其它可用基线。图 7 的某些配置增加 M/N 后仍在较高 SNR 才出现恢复相变，图 6 迭代上限 2500。SC 作者报告联合估计能扩展部分配置的可恢复范围。AI 全局求解能力和目标域是否具备可辨信息要分别测。UN 开放人口、拒配、迟到和每秒预算。 [作者稿](https://arxiv.org/pdf/2406.08290) · [正式 DOI](https://doi.org/10.1109/TSP.2025.3575919)

## 海事实采与跟踪

### S-ON44 Brekke 等，海事扩展目标 VIMMJIPDA，IEEE JOE 2021

阅读作者稿 §V、图 4–8。DE 比较近邻与多量测联合概率关联，Joyride 238 扫描、Autosea 1471 扫描，每扫描 2.5 秒。原实录有连续六次漏检后断轨。图 4 的身份跳接是受控复现，作者在原实录删三组量测并放宽终止阈值。另一个起轨例中较宽的门让旧轨抑制新目标，首报后 7 帧（17.5 秒）才起轨。SC 作者认为量测组、目标形状和存在状态的软关联能降低其中一部分互扰。AI 同门内距离小既可能是真边，也可能是占用着旧轨的假边，需要同时记录延迟和错并。UN MTAD 报告粒度、目标散射形状信息及实测证据是否同样充分。 [作者原文](https://edmundfo.folk.ntnu.no/papers/vimmjipda-2nd-submission.pdf)

### S-ON45 Xu 等，AIS／雷达状态融合，IEEE TITS 2024

阅读机构作者稿 §IV-A、§V-C 表 VI。DE 长江 VTS 的实采实验预选一船并提取该船 AIS。10 秒间隔的速度方差 AIS／雷达／融合为 7.73／2.55／0.38，航向为 26.48／28.39／23.48。摘要雷达航向方差写 28.35，取表 VI 的 28.39。SC 作者用方差与变化曲线说明轨迹平稳。AI 有真组的状态平滑收益和未知对应的定位准确是不同证据，低方差也可能掩盖转弯。UN 独立状态真值、选船规则之外的泛化、传输和持续身份。 [机构作者稿](https://scholar.tecnico.ulisboa.pt/api/records/UPfep4oCBgJJboVeyUdz32ibb4TecztyDjez/file/d574c5ac479cb624a7c22b686425e46ed8796e1541db5d6e2273b57b0b61fa08.pdf)

## 在线链路与跨次身份

### S-ON46 Wu 等，CooperScene，ECCV 2026

阅读 arXiv v1 §3.2、§4 表 2/6、图 5–6、附录 B.2，正式版 pp.91–111。DE 三车一路侧单元同步传感采集，网络 iPerf 统计和特征负载的分块传输分别测。所查公开脚本根据载荷、配置带宽及固定开销折算历史帧年龄，默认按 10 Hz 帧间隔取整，未使用逐次观测到达。表 2 的带宽约束基准下，ERMVP 加 RSU 后 AP50 .57→.56，表列传输时间 3.46→5.19 s，无限带宽却 .80→.81。表 6 是用真框裁点的短载荷 oracle 对照，真 C-V2X 丢包 38.19%、延迟 31.46 ms、.72 Mbps，AP50 本地 .15／链路 .19／无限 .21。SC 作者要求用现实网络约束评价可协同的感知。AI 来自更多源的证据增量会受包容量、抵达时刻和处理共同限制。UN 逐条海事测量真实到达、同步协议差异、身份评价和非 oracle 稀疏报告。 [正式会议章节](https://link.springer.com/chapter/10.1007/978-3-032-37393-9_7) · [作者原文](https://arxiv.org/html/2606.31219v1) · [固定提交的数据回放](https://github.com/UCR-CISL/CooperScene/blob/fb7853c633ccc3d69ee798fc5105cd308173fddb/models/cooperative/datasets/coop_dataset.py#L104-L153)

### S-ON47 Zhong 等，CoopTrack，ICCV 2025

阅读正式会议版 §3.2/3.4、表 3–4。DE 基准中按同一时刻配对的车路图像和位姿输入，每帧恒速传播已有对象 query，结合运动与语义估图匹配分数，未配实例有独立路径。10 Hz、ResNet101 的 AMOTA .435，对比 UniV2X-Track .418，ID 切换 302 对 535。无融合控制切换仅 50，AMOTA 却 .217、检测 mAP .183。图关联的消融在同一前置配置上 .332→.346。通信体积 2.88×10⁵ B/s，对手 1.51×10⁵ B/s。SC 作者报告端到端顺序跟踪的精度和通讯效率。AI 原始 ID 切换计数会受有多少目标输出影响。UN 墙钟抵达、真实通信尾延迟、视觉 query 的海事同等输入。 [会议原文](https://openaccess.thecvf.com/content/ICCV2025/papers/Zhong_CoopTrack_Exploring_End-to-End_Learning_for_Efficient_Cooperative_Sequential_Perception_ICCV_2025_paper.pdf)

### S-ON48 Li 等，OA-SORT，CVPR 2026

阅读作者稿 v2 §§4.2–4.4、式 8–11、表 1/4，会议正式条目已核。DE 由框底深度排序和交叠估遮挡，在高分关联中加依赖轨迹的代价项，低分更新时用预测与观测混合，仍有上次观测重接。DanceTrack-val 三模块 IDF1 60.7→63.7，跟踪 9.57→24.56 ms；ReID 条件下 65.1→65.3，增加 15.32 ms。DanceTrack test 的 OA-OC AssA 40.2→39.6，而 HOTA、IDF1 改善。SC 作者认为遮挡线索能改善关联和滤波。AI 式 8 在固定匹配轨迹集合的全双射里代价偏置总和为常数，作用须来自筛选、部分匹配或后续阶段。UN 海事没有影像框遮挡信息时的效应、完全中断和真实到达。 [会议正式条目](https://openaccess.thecvf.com/content/CVPR2026/html/Li_Occlusion-Aware_SORT_Observing_Occlusion_for_Robust_Multi-Object_Tracking_CVPR_2026_paper.html) · [作者原文](https://arxiv.org/html/2603.06034v2)

### S-ON49 Xiang 等，V2X-ReaLO，2025 预印本补充

阅读作者 v1 §§III–VI、表 II–VII。DE 独立 ROS 节点与 Wi-Fi 在线演示，通信延迟用两设备 RTT/2 的平均测量，准确率是用所测阈值在同机回放计算，未关联逐条实时抖动。压缩特征 25 MB/511.2 ms→391.1 kB/14.3 ms；设备复制 19.19 ms 大于序列化 .26 ms 和压缩 .13 ms。V2V 中 AttFuse 线上 mAP@.5 27.4 对 V2X-ViT 26.6，离线 33.5 对 39.8。SC 作者强调最新可用信息的特征库。AI 实际可用输入可能改排名，通信与计算的单独影响未由此分离。UN 正式同行评审身份与海事链路。此项另列为补充证据。 [预印本](https://arxiv.org/html/2503.10034)

### S-ON50 Ristic、Clark 与 Gordon，无标签偏差校准，IEEE JSTSP 2013

阅读正式版 §III 式 4/8/9/20、算法 1，§IV-A/B、图 1–3、表 I、§V。DE 外层静态偏差重要性采样，内层为每个偏差假设运行粒子 PHD，利用无目标 ID 的检测集似然，要求检测、Poisson 杂波、出生／存续和运动先验。两固定传感器已知位置、视场重叠，量测距离与方位。交替 15 批共 45 s、5 条有生灭的模拟轨迹，偏差后验覆盖所设真值，逐批 MAP 变化。SC 作者把严格可观性列为未解决，报告 MCMC 接收率偏低。AI 即使缺身份，已知几何和跨批目标分布仍可提供配准信息。算法 1 使用积累检测，不能推定每秒可更新。UN 真实错时、持续身份、先验失配和 MTAD 相对平移的可辨性。 机构 PDF 本次由搜索缓存读取，直连访问失败。 [正式 DOI](https://doi.org/10.1109/JSTSP.2013.2256877) · [机构 PDF](https://www.udrc.eng.ed.ac.uk/sites/udrc.eng.ed.ac.uk/files/publications/Calibration.pdf)

### S-ON51 Gao 等，MOTIP，CVPR 2025

阅读作者 v2 §§3.3、4.2/4.4 表 6、§5，会议补充 D.2/3 表 8 图 9/10。DE 用历史外观和 ID 做因果匹配训练，模拟丢轨和特征交换。固定交换率 0，遮挡模拟率 0/.5/1 的 IDF1 为 61.1/62.7/59.8；遮挡 .5 时，交换率 .2/.5/.8 为 64.1/64.8/61.8。补充图中一条轨迹中断 4 帧后，用较早的历史特征恢复，但只是示例。A5000 FP32/FP16 为 12.7/22.8 FPS，历史上限随基准设 29/59/19。SC 作者认为可学习模型从不同历史位置取身份信息。AI 训练扰动与缺失严重度的作用非单调，真实报告可能没有外观替代。UN 海事多源无信号、真实迟到、长空档和有限 ID 字典的影响。 [会议原文](https://openaccess.thecvf.com/content/CVPR2025/html/Gao_Multiple_Object_Tracking_as_ID_Prediction_CVPR_2025_paper.html) · [作者正文](https://arxiv.org/html/2403.16848v2) · [会议补充](https://openaccess.thecvf.com/content/CVPR2025/supplemental/Gao_Multiple_Object_Tracking_CVPR_2025_supplemental.pdf)

### S-ON52 Hem 等，船报与外部量测 PMBM，IEEE Access 2024

阅读正式版 §§III–V、VI-A/B、VII-B，图 4–6。DE 报文 ID 进入 PMBM 状态与关联似然。式 10 在有报文时才用检出项，缺报时该项为零。2023-10 特隆赫姆峡湾，Mariner 实时雷达＋AIS 跟踪单机动艇，结果进入场景 MPC。相同记录上事后比较单模型纯雷达 IPDA 与 AIS-IMM-PMBM，速度和航向标准差 0.36→0.25 kn、34.45→15.63°，传感器、运动模型和滤波均有变化。另有多目标实采雷达场景的 AIS 是事后合成，LiDAR 试验也有 GPS 生成的 AIS。SC 作者报告目标提供信息在点、扩展目标跟踪上的作用。AI 单目标闭环能说明现实运行输入，无法将标准差变化归因于身份辅助。配套开放数据给单 UTC 的 AIS 条目、雷达扫描和按雷达时间标记的输出。UN 缺同时记录物理时刻、抵达与发布三者的字段证据，密集多船闭环也未覆盖。此项用于补现场证据。 [正式 PDF](https://papers.etn-sas.eu/assets/uploads/files/781d1-pmbm_filtering_with_fusion_of_target-provided_and_exteroceptive_measurements_applications_to_maritime_point_and_extended_object_tracking.pdf) · [正式 DOI](https://doi.org/10.1109/ACCESS.2024.3389824) · [同一海试的开放数据](https://github.com/autosit/autonomy-field-test-data)

### S-ON53 Helgesen 等，异构多源船舶跟踪，Ocean Engineering 2022

阅读作者上传的正式版 §§5–7，表 6–7、图 24–25。DE milliAmpere 平台的雷达、LiDAR、可见光、红外进入多传感器 JIPDA，两环境有 GPS 参考。开阔区雷达→雷达＋LiDAR 的 GOSPA 20.05→18.58，两目标位置 RMSE 29.28/8.92→15.97/8.26 m，表列断轨长度却 8.4→10.0 s。城市水道雷达／LiDAR／二源融合的表列断轨长度 95.7/76.2/188.7 s，四源融合 200.2 s，误轨 131 条，LiDAR 单源 11 条。GOSPA 使用 20 m cutoff 且不计标签。SC 作者指出城市水道的 LiDAR 可见范围假设过于乐观，相机高频更新可能将轨迹拉向靠泊船。AI 真实海事存在位置变好、连续性下降，以及加源使多个结果变差的反例。UN 逐秒发布时间、实际传输、加源与检测模型失配的单独效应。S-ON52 的部分扩展目标实验使用该数据的场景 13，两个论文不能对这部分计作独立复验。 [正式原刊](https://www.sciencedirect.com/science/article/pii/S0029801822005753) · [作者上传全文](https://www.researchgate.net/publication/359787436_Heterogeneous_multi-sensor_tracking_for_an_autonomous_surface_vehicle_in_a_littoral_environment) · [开放数据](https://autoferry.github.io/sensor_fusion_dataset/)

### S-ON54 Üney 等，从多目标观测协同估计相对位置，IEEE TSP 2016

阅读机构审后稿 §§II、IV–V、VII，式 1–5/18–19、命题 4.1、推论 4.2、算法 1、图 1–4。DE 共同离散时间下，一源当前无标签检测对另一源历史 Poisson 多目标预测给似然，两向累积边势后定期以环路 BP 估相对平移。似然近似误差受预测不确定性约束，完全可预测是零误差的充分情形。九传感器／四目标，200 步及 200 次模拟，检出率 .98、每步 Poisson 平均两虚警，选一个坐标原点，10 步窗、每窗八次 BP，前 40 步预热。末窗各试验网络最大误差的平均 5.95 m、跨试验最大 12.09 m。SC 作者提出以共享目标同时配准与跟踪。AI 可信的历史预测和多源真实时间轴是机制条件。UN 未知时偏、低检出、重复队形、持续身份。 [机构审后稿](https://www.research.ed.ac.uk/files/22038653/uney_cooploc_authorsfinal.pdf) · [正式 DOI](https://doi.org/10.1109/TSP.2015.2493981)

### S-ON55 Kang 等，Batch-MOT，IEEE TCAD／EMSOFT 2024

阅读正式版 §§I–III、VI–VIII，图 1/2/6/8、算法 3–4。DE 单 GPU 不抢占模型，每路摄像有固定周期、到达可预知，截止为下一周期。调度器维护就绪队列，通过可调度性检查后才等候成批。V100、YOLOX 十二张高分辨率图串行归一耗时 1.00，批处理 .46，MOTA 同为 41%。低分辨率串行 .74，MOTA 17.7%。§VII 随检测模型与设备变更，饱和点和批处理收益变化。Jetson TX2 真实行车片段的硬件时间按测量估计最坏执行时间，和跟踪精度为不同实验。SC 作者指出整体加速与个别任务的优先级反转可并存。AI 海事报文不规则且固定 1 Hz 查询未定义硬截止，不能直接承接其保证。UN 实际延迟抖动、跨源融合路径和每秒发布时刻。 [正式原文](https://rtcl-yonsei.github.io/website/papers/IC202409KLH.pdf) · [正式 DOI](https://doi.org/10.1109/TCAD.2024.3443002)

### S-ON56 Tokle 等，商船雷达与光学跟踪，Ocean Engineering 2025

阅读机构存档正式版 §§2.2、3.1、5.1–5.3，图 7–11/14–15、表 1/3。DE 两套 S 波段雷达、12 路相机、Seapath 位置姿态时间用于坐标统一。V-JIPDA/GM-P 显式估各源可见性，近似边缘关联，按预备、暂定、确认、衰减管理目标。PROXIMA 2018-06-22 卑尔根约 30 min 实录，初始 10 min 手工挑五轨与 AIS 配对，有一侧中断即裁剪。配对 55/448/12/380/67 s 的水平 RMSE 30/14/57/28/10 m。单个同刻快照打开可见性建模后，新增只在雷达可见的船，现场无该时点 AIS。SC 作者说明覆盖差异会影响起轨。AI 先前的双源同在约束可能漏掉仅一源所见的对象，定性单例不能给错并／漏检分母。UN 独立位置真值、人工选轨偏差、完整人口身份和真实输出延迟。 [机构正式全文](https://nva.sikt.no/registration/0198cc96f850-fe6c0695-dbf0-4ee4-b2f1-d92014431e47)

## 检索与正文状态

2026-11-11 在期刊官网、CVF/ECVA、arXiv、作者和大学档案中用论文引用与全文检索互查。检索族覆盖 `maritime radar AIS real sea trial multi-object tracking`、`joint registration fusion unlabelled measurements unknown permutation`、`cooperative sequential perception measured communication delay`、`nearest second nearest ratio selective coverage`、`multi-target tracking partial annotation asymmetric false missed costs`。旧书目、同数据重复和新读到的方法／对照分别记录。此前的 IEEE JACF、Wang 联合偏差估计、Tian TGRS 及 He 岸基级联仍仅有摘要或书目。未以它们的具体实现或数值作为直接证据。部分正式版本未开放，使用所标接受稿／作者稿阅读定位。论文性能和代码复现状态分别记账。
