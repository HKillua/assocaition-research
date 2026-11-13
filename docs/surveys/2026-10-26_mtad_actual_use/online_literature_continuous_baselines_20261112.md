# 持续在线关联的基线原文审查

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-CONTINUOUS-BASELINES-20261112`，2026-11-12，partial。检索轴为 MTAD 航迹级同行、海事系统 ID 与多源融合、运动和全局指派、联合假设与迟到更新。优先选方法、输入、作者协议和失败对照可查的正式论文。原文数据成绩均按原任务记录。SC 为作者主张，DE 为直接证据，AI 为项目推断，UN 为未确定。已有来源沿原编号补读。

## 同任务与现场系统

|来源与阅读位置|SC 与 DE|AI 与 UN|
|---|---|---|
|S-ON3a Cao 等，TSA-cTFER，Remote Sensing 2024，§§3.5、4、5.2–5.7，算法1–3、表1–2、图7/14。 [原文](https://doi.org/10.3390/rs16183380)|SC 对比学习可从局部历史提取片段相似度，两阶段确认处理难配。DE 同源 ITSA 和异源 MSTSA 分别组正负对。经纬度与时间进入网络，最多 128 点，双分支训练，指派、易难确认及后续复审。按 20 s 喂入轨迹信息，原分割 4000/500/500，150 epoch，3/6 确认。MSTSA 单任务表2的场均正确关联 94.83±0.38%、误配 2.61±0.34%、正确边平均确认 234.65±1.10 s，联合训练为 94.25±0.09%、3.06±0.11%、246.95±0.78 s。ITSA 联合训练 94.59%、3.49%、131.00 s。图14展示一对一错误连锁。|AI 优先同任务强学习基线，现字段可支持。原评估用 MSTSA >120 s 共时、ITSA 两段各 >120 s 和中断 <20 min 的事后评价条件，不能拿来筛在线输入或全首报。UN 未核到原划分逐场 ID、公开权重/可执行作者代码、真实到达及所有阈值细节。论文等待只在正确关联边上取均值，不能读为处理墙时或全体确认延迟。|
|S-ON3b Xiong、Xu 与 Cui，HTG-TA，IEEE TAES 2024，§§III–VI、表IX/X/XII/XIII。 [期刊](https://doi.org/10.1109/TAES.2024.3414957) · [原文与表图（出版页）](https://doi.org/10.1109/TAES.2024.3414957)|SC 异构点—片段图用场景上下文处理不等速报告。DE 数据由 MTAD 生成。窗口内 t/x/y min-max、首尾趋势、跨源全二部边，学习评分、0.5 贪心。原设定同源不同轨属于不同目标。固定 90 目标的 F1 为 .8587，真实单个雷达/ADS-B 场识别 9 个已知真配的 8 个，完整错配分母未知。五固定场既用于选择设置也用于结果比较。|AI 可做不等长因果尾窗学习对照，推理只读已到窗口。UN 无跨窗口系统 ID、原版发布规则、作者代码和可复现名单。不能从整窗时间推得在线时效；当同源片段重叠时须保留并计入输出限制。|
|S-ON5 Nikolić 等，Remote Sensing 2019，§§3–6、图2–3/6。 [原文](https://www.mdpi.com/2072-4292/11/7/852)|SC 雷达批抵达触发可形成持续系统航迹。DE 既有成员延续、活跃轨关联、暂失预测轨重获、余项建新轨，每个系统轨每源最多一条当前成员。现场 33 s 雷达周期，案例一源改两次本地 ID 时另一源维持系统 ID。|AI 最贴近本地片段进入中心融合器的生命周期对照。UN 源级 JPDA–UKF、本地状态、雷达几何权重和 AIS 参考不可照搬。全年合并条数无法证实假合并或漏配率。|
|S-ON22 Gaglione 等，IEEE TSP 2022，方法因子图与海事实验。 [原文存档](https://dspace.mit.edu/entities/publication/f7972a21-b0ec-42af-a452-e3acadf82a2b) · [前轮全文笔记](online_literature_web_followup_20261111.md)|DE 联合更新存在、状态、量测归属与 AIS 目标标识。作者实测条件存在 AIS 信息和雷达扫描，图模型允许无关联。|AI 是联合跟踪和拒配的同行证据，依赖外部身份和探测机制，当前 MTAD 只提供匿名来源键、时间与位置。|
|S-ON91 Bar-Shalom 与 Chen，JAIF 2006，§§II–III、V，式39–43。 [原文](https://isif.org/files/isif/2024-01/2075D01.pdf)|SC 同源／异源假设的似然可转化为多维指派代价。DE 推导使用局部状态和误差协方差，考虑相同目标过程噪声造成跨源误差相关，匹配支持虚元。等方差且相关 .5 时，误假定独立会把归一化二次统计量变为正确值的一半，扩大同源接受也扩大误接。|AI 同一公共时刻比较与显式空配可用。UN MTAD 缺局部估计协方差和交叉项，基线只能用因果位置滤波估计及其近似误差模型，不能声称复现精确似然。|

## 在线运动与全局推断

|来源与阅读位置|SC 与 DE|AI 与 UN|
|---|---|---|
|S-ON92 Yi 等，UCMCTrack，AAAI 2024，图2、式6–8、表4、伪代码。 [原文](https://arxiv.org/html/2312.08952) · [作者代码](https://github.com/kumcvat/UCMCTrac)|SC 地平面运动和协方差传播提高鲁棒性。DE 用 CV-KF、协方差加权残差及 log 行列式，结合 Hungarian。相同 ByteTrack 底座，MOT17 验证 HOTA 68.43，单换 MMD 为 68.09，加入协方差传播 70.44，再加过程补偿 71.96。DanceTrack 也有单换成本变差。|AI 先控制同一候选和空配，用绝对距离与不确定性似然、静态与传播分步比较。UN 框底、相机标定和检测置信无等价输入，项目基线只能明确称因果运动与 GNN 适配。|
|S-ON93 Yin 等，CenterPoint，CVPR 2021，§4、附录 A、表12。 [原文](https://arxiv.org/html/2006.11275)|SC 可靠点速度可令简单关联具竞争力。DE 用当前检测器回归速度反推上一帧位置，再贪心一对一；同检测输入的表12相对 Kalman–Mahalanobis 约 +3.7 AMOTA，跟踪处理 1 对 73 ms，状态模型和成本同时变化。|AI 保留运动近邻控制以核全局指派是否提供独立增量。UN 新生 MTAD 片段没有可靠当前速度，能用的是已到旧片段前推。|
|S-ON94 Liu 等，GNN-PMB，IEEE TIV 2023，§§V–VI、表I–II。 [原文](https://arxiv.org/html/2206.10255)|SC 统一生命周期和存在分支可提升在线 3D MOT。DE 同 CenterPoint 检测下 GNN、PMBM、GNN-PMB 的 AMOTA 为 .603/.645/.707。线性指派从已存在、新生与杂波等局部假设取一个全局假设。检测分、初始协方差、出生密度的变化都影响结果。|AI 可借显式新生和空配及同观测统一对照。UN 检测分代理 P_D、均匀杂波、出生先验和点目标观测是原模型条件，当前无直接对应。|
|S-ON95 Williams 与 Lau，IEEE TAES 2014，§III/IV/V、图3/5/7。 [原文](https://arxiv.org/pdf/1209.6299)|SC 双部互斥图的 BP 收敛并高效近似边缘概率。DE 图3输入单目标相对似然权重含空配。高置信但未消歧时收敛会变慢，最难模拟实践最多 87 次迭代，理论上界约 3000。§IV 精确推断的成本和近似误差分别比较。|AI 同权重的 GNN 与 BP 可区分最优单解和边缘歧义，适合小图精确对照、逐源事件。UN 收敛不保证边缘精确，边缘大也不能替代互斥解码，近似权重不能变成物理概率。|
|S-ON3c Reid，IEEE TAC 1979，§§II–IV，及 S-ON59 Xia 等，JAIF 2019，§7.3 表I/图4。 [Reid 原文](https://graphics.stanford.edu/courses/cs428-03-spring/Papers/readings/CollaborativeProcessing/Reid_MHT_ieee_trans_ac_1979.pdf) · [Xia 原文](https://isif.org/files/isif/2024-01/07-022019-0009R2_LR.pdf)|SC 多扫描关联用新证据重排旧假设。DE Reid 按已知目标／新目标／假点递归分支。轨迹 PMBM 以 N-scan 剪枝及多帧指派控制复杂度，并分别比较多扫描和状态平滑。|AI 可对照同一分数、候选池和发布约束下保留一个或多个分配假设。UN 原方法的扫描模型和发现／杂波率不可直接继承，未来证据只在抵达后用于当时修订。|
|S-ON29 García-Fernández 与 Yi，IEEE TSP 2021，§§IV–VI、表II。 [原文](https://arxiv.org/html/2106.04898)|SC 真迟到点可先反推至量测时刻更新再边缘化。DE 100 次仿真的 19 目标设置，丢迟到的 TPMBM 到 5 历元 OOS-TPMBM，RMS 轨迹误差 3.44→3.10、计算 11.3→12.3 s。|AI 真迟到需分别有量测和到达时戳。UN 当前是理想到达异频回放，不能把不等 Δt 当迟到。|
|S-ON96 Ding 等，3DMOTFormer，ICCV 2023，§§3–4，表4。 [原文](https://openaccess.thecvf.com/content/ICCV2023/papers/Ding_3DMOTFormer_Graph_Transformer_for_Online_3D_Multi-Object_Tracking_ICCV_2023_paper.pdf)|SC 在在线更新的检测—轨迹图上学习评分可提高跟踪。DE 每帧预测边关联概率，原解码按检测分贪心；训练展开长度 2→3 时 AMOTA .6741→.7105。|AI 可作为后续学习图的近邻，现有同数据集 TSA-cTFER 优先。UN 缺 3D 框、类别及检测置信，不能移用作者权重。|

|S-ON97 García-Fernández 与 Särkkä，IEEE TSP 2025，§§II/IV/V-A，表II。 [原文](https://arxiv.org/html/2411.19814) · [作者 MATLAB](https://github.com/Agarciafernandez/MTT/blob/cc5c6df0e9343dc1345d91ed6ab95f01db4d1821/CD%20MTT%20filters/PMBMtarget_cd_filter.m#L91-L139)|SC 连续模型可一步传播到不规则扫描时刻。DE 单源位置仿真 100 个不规则测量时刻，类似 GOSPA 下 CD-PMBM 5.1 s、离散 PMBM 136.6 s、CD-PMB 1.1 s。非等间隔出生分布影响部分条件下的误差。代码更新明确需要 H/R、检出率、杂波强度和假设上限。|AI 是待输入模型成立时的持续系统概率对照。UN 无真实扫描机会，不能把一秒发布或源未报当空扫；原版模型/速度不能直接当作 MTAD。|
|S-ON98 Kim 等，PolarMOT，ECCV 2022，§§4.2–4.4、式7、表2/5。 [原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136820038.pdf)|SC 局部相对几何时空边可跨域。DE 已到检测与历史构图，使用时间归一位移和相对角。同检测的 nuScenes 验证在线 AMOTA 67.27，CenterPoint 65.91，作者允许未来的离线版 71.14；速度筛 ×0.5/1/2 的结果 58.61/67.27/65.42。|AI 比依赖外观的视觉 tracker 更贴近位置片段，可作学习几何扩展。UN 新片段首报无方向，需核同刻、方向缺失及训练；数字不外推至 MTAD。|

|S-ON99 Kropfreiter 与 Hlawatsch，Information Fusion 2026 在线／2027 卷期，§§2–4、7、图4–5、表1–2；与其 ICASSP 2024 前作对照。 [期刊存档](https://repositum.tuwien.at/handle/20.500.12708/230581) · [17 页原文及复核（公开出处）](https://repositum.tuwien.at/handle/20.500.12708/230581) · [会议稿](https://repositum.tuwien.at/handle/20.500.12708/199604)|SC 对本地对象或标签的不确定对应作软关联，再融合后验。DE 扩展同时推导 JPDA/JIPDA/LMB，实测是六个模拟场景的 JIPDA、LMB，2–9 源与 10–50 目标。软关联的平均 MOSPA 低于各自硬对照，部分场景耗时反升。需要同一时刻的本地状态后验、存在概率和误差模型。|AI 支持把硬选择和关联不确定性放进同观测对照。UN MOSPA 不量持续身份；原 JIPDA/LMB 零分支为非存在，不能等同对侧暂缺报告或显式空配。先检验小图边缘与空配语义，当前没有论文所需本地后验。|

另核 ByteTrack（ECCV 2022 §3/算法1）、OC-SORT（CVPR 2023 §4/表5）及 TrackTrack（CVPR 2025 正式摘要与作者代码入口）。ByteTrack/TrackTrack 原检测分、框重叠及后一项的视觉外观模型缺同等输入。OC-SORT 的观测中心方向需要两侧已到历史，重新关联后重更新不能用于判当次首报。近期 IAGM-TAN（Neurocomputing 2026）只取得出版社摘要及方法摘录，确认 MTAD 和含空配的 Sinkhorn，信息截止、持续 ID、权重和划分待核，暂不列为在线主对照。 [ByteTrack](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136820001.pdf) · [OC-SORT](https://arxiv.org/html/2203.14360) · [TrackTrack](https://openaccess.thecvf.com/content/CVPR2025/html/Shim_Focusing_on_Tracks_for_Online_Multi-Object_Tracking_CVPR_2025_paper.html) · [IAGM-TAN](https://doi.org/10.1016/j.neucom.2026.134264)

2026-11-12定向源码订正：S-ON97本篇CD-PMBM应定位`PMBMtarget_cd_filter_linear_SDE.m`，上表旧`PMBMtarget_cd_filter.m`链接不足以对应本篇线性SDE入口；S-ON146的TM量测生成器内部两端已经来自同一目标。具体输入/窗口语义与不能直接移用的条件见[E-ON128](online_fusion_dataset_code_audit_20261112.md#e-on1282025-tsp-两种概率骨架输入条件不同)。S-ON99仍是概率标签融合，不能与CD-PMBM串号。

另核公开 MMM-TTA/MIMMA 工程的 MMTDS-mtad 表，BYTE/OC-SORT/UCMC/MIMMA 的 HOTA 分别为 39.78/30.43/29.09/40.73，BYTE 的 AssA 40.04、MIMMA 39.33。只核到派生工程，原 TXT 生成、独立划分、发布时刻及正式发表未确认，仅作“有人比较过”的证据。 [工程原件](https://github.com/Yide-Qiu/MMTD#readme)
