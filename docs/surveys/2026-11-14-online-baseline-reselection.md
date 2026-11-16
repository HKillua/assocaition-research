# MTAD 在线多传感器基线重新筛选

2026-11-14，来源初筛与旧候选复核。当前研究阶段见[研究状态](../research_status.md)，回退依据见[审计](https://github.com/HKillua/assocaition-research/blob/d9eaeaa3e5e4de9d80aee56dfc242068843dc5af/docs/reports/2026-11-14-online-baseline-restart-audit.md)。

## 比较任务与依据

目标是从 MTAD 双源已到经纬、量测时钟及源内片段等同性出发，从首报持续发布关联、身份和融合状态。每套方法应说明单源和少量候选时如何初始化、何时空配、如何断轨重接及何时发布。原方法若必须使用缺失输入或终局信息，先定位所涉核心行为，并记录适配后还能回答的问题。当前阶段只核论文、已有记录和作者源码，不运行 MTAD。 [字段与评价约定](../data_contract.md)

按 2025–2026 卷期或正式会议纳入，另记首次公开年份。2026 正式在线但卷期在 2027 的论文单列。优先看本任务匹配和原任务有对照的效果，核作者代码、许可或公式与算法的复建条件。在可比任务内参考近两年引用和已核后继，继续追踪前向引用与作者实现。源协议、代码核验及 MTAD 适配各自保留证据。 [飞书第一章](https://my.feishu.cn/wiki/OHs3w9meHiQ3OXk4XC7ctFPXnxd#Wq7gdDT11otUQsx36z6co1qhnjb) · [项目流程](../research_workflow.md#从基线到研究问题和解法)

## 检索记录

用户提到的 `asnsearch` 本轮按本机已有的 AnySearch 服务执行。调用 `POST /v1/search`，每条最多 8 条，2026-11-14 三条均成功。返回条数含重复版本和检索噪声。再按标题与 DOI 查原文、正式会程、作者仓和后继，扩查 2025–2026 纯传感器航迹级、多传感器海事、同 MTAD 和视觉在线。 [AnySearch 接口](https://github.com/anysearch-ai/anysearch-skill/blob/main/scripts/shared/doc_spec.md)

| AnySearch 查询 | 返回 | 命中及后续核查 |
|---|---:|---|
| `2025 2026 asynchronous track-to-track fusion multi sensor local tracks online persistent global track ID IEEE Sensors Journal Information Fusion TAES` | 7 | Draves 两个同稿链接合并，Lindenmaier 转原论文；另有 Temporal-MPRF 与 CCTA 2025 雷达／红外。SDF 动态共识和 HTG-TA 为 2024。 |
| `2025 2026 multisensor multi-object tracking online track-level fusion radar AIS local tracks published reproducible source code github` | 8 | 核 RCFMOT、PTFM、TUMFTM FusionTracking；含工具和书目。FusionTracking 回查算法首发年份，未计入 2025–2026 主池。 |
| `2025 2026 online multi sensor tracking radar lidar track to track fusion asynchronous association ECCV CVPR ICCV open source` | 8 | 补查视觉／雷达类实现。对照 Fusion-Poly、GMT、GRAE-3DMOT 和 CoopTrack 的具体输入与测试执行路径。 |

以下数字均为 2026-11-14 以 DOI 取 OpenAlex `cited_by_count` 的快照，链接定位到该库的 work。Draves、Fusion-Poly、GMT 标注为预印本记录，未与正式版本相加。0 表示该条记录当时显示 0。引用存在收录和时间差异，以下观察只覆盖已检索到的同类来源。DE 为原文、数据表或源码可直接读出的证据，SC 为作者主张，AI 为 MTAD 适配推断，UN 为未核。 [OpenAlex 引用口径](https://help.openalex.org/data/works/citations/)

## 航迹级整系统候选的原文复核

| 来源与阅读范围 | DE／SC 原协议、效果与复建证据 | AI／UN 当前判定及精读任务 |
|---|---|---|
| **Lindenmaier，IEEE Sensors Journal 2025**。算法 1、式 29–51、实测结果；[7 引](https://openalex.org/W4408399516)。 | 雷达和智能相机直接供局部轨，反馈融合轨做关联，维护全局轨。实测 F1、MOTA 相对 JIPDA 各领先不足 0.5 个百分点，JIPDA 召回更高。Bóka 等 2026 是可核的同路线后继，进一步用视场、速度及出生模型估计存在概率，[0 引](https://openalex.org/W7161172037)。 [刊版](https://doi.org/10.1109/JSEN.2025.3548899) · [作者公开全文](https://www.researchgate.net/publication/389845267_A_Robust_and_Runtime-Efficient_Track-to-Track_Fusion_for_Automotive_Perception_Systems) · [直接后继](https://eprints.sztaki.hu/11134/) | 作者代码未核到，正文给出重建路径。先逐项核关联、起轨、删轨所需的局部协方差和存在概率，区分可从已到位置估计的量和必须额外假设的量。缺真实视场的 MTAD 暂不能使用后继的出生和空扫机制。 |
| **CDP-WGL，Signal Processing 2025**。作者稿 2024，§§3–4、算法 1–3；[16 引](https://openalex.org/W4403728210)。 | 密度峰先分簇并融合当前状态，加权图分配历史标签。以真实出租车路径生成观测，两个例子的轨迹 OSPA² 相对 TC-OSPA² 小幅下降，融合耗时约其四分之一。完整算法可读，未核到作者代码。 [作者稿](https://arxiv.org/html/2401.00605v2) · [卷期](https://doi.org/10.1016/j.sigpro.2024.109703) | 两源各一条的密度并列裁决、单轨、同源互斥及历史误合并撤销缺明确定义。需把分簇、状态融合、历史标签分开核。若补规则改变核心行为，记录为有条件适配或机制参照。 |
| **Draves 等，IEEE MFI 2026**。作者全文 §§II–V、正式会程；[预印本 0 引](https://openalex.org/W7221980208)。 | 按到达局部轨分区、扩展、打分、剪枝并继承同根 ID。两源建立根是为了方位观测的立体几何，假设同一源每个目标至多一条持续局部轨。原仿真以终局最佳假设对逐帧 GNN，最终采用不到八成的局部轨。正文算法可读，作者代码未核到。 [作者全文](https://arxiv.org/html/2610.20290v1) · [正式会程](https://www.mfi2026.org/program.html) | 在 MTAD 双源断段输入中，单源首报、同源换片和跨根延续会改变原生命周期。复建前须确定双源时保留哪些多假设机制，分别记当前发布、延迟确认和终局修订。终局分数不足以支持同延迟优越性。 |
| **CFAG-GLM，IEEE Sensors Journal 2026**。出版方题录／摘要；[0 引](https://openalex.org/W7221994759)。 | SC 轨级融合加遮挡后 rebirth，全局标签跨扫描延续；摘要的 69.2%／65.7% 指两场遮挡造成的 OSPA² 劣化降幅。 [出版记录](https://doi.org/10.1109/JSEN.2026.3730854) | UN 全文、源码、使用视场的位置和跨源异步发布。先找可用的原文与作者实现。摘要只支持列为补查对象。 |
| **Wang 等 LMB 航迹匹配，Digital Signal Processing 2026**。出版方摘要、导言和章节预览；[1 引](https://openalex.org/W7126108597)。 | SC 先按跨节点 LMB 航迹历史算标签相似性，再全局匹配与算术平均后验融合，原验证为八节点仿真。 [出版方预览](https://www.sciencedirect.com/science/article/abs/pii/S1051200426000734) | 新增补查对象。UN 位置报文能否替代 LMB 局部后验、算法细节、作者代码、是否按异步到达发布。 |
| **ModTrack，ECCV 2026**。作者全文 §4、作者后端及评估代码；[0 引](https://openalex.org/W7138950295)。 | 有空间跟踪模式，使用协方差传播；固定源码在全序列结束后合并 ID。原文非真值辅助雷达 LSTQ 42.1，论文中的雷达对照 66.8，76.9 来自真值辅助输入。 [原文](https://arxiv.org/html/2603.15812v3#S4.SS7) · [固定源码](https://github.com/JackRobs25/ModTrack/blob/17afb547fa5f8341743595598fe269768aa28637/modtrack/core/evaluate_modtrack.py#L2115-L2130) | 先区分空间后端当前时刻行为和终局 ID。MTAD 无原生误差协方差及真实检测机会，作者仓软件许可未核定。当前证据不足以选为完整系统。 |

## 学习关联与输入边界

| 来源 | 原文与源码证据及 MTAD 边界 |
|---|---|
| **GMvA，IEEE T-ITS 2026**，[21 引](https://openalex.org/W7125940799) | AIS／CCTV 图学习与全局匹配。作者稿表 II–III 的高密度匹配分数为 86.73%，欧氏对照 57.32%，随机删除十条目标记录后为 45.45%。固定代码先筛至少 3 个有效点再插值、跳过单侧窗；论文写剔除低分边，该评价入口直接指派。当前有作者代码、软件许可未核定。核窗末可见性、单点和单侧、空配后，可讨论固定等待的学习关联，持续 ID 与全场首报另需发布规则。 [原文](https://ira.lib.polyu.edu.hk/handle/10397/119909) · [固定源码](https://github.com/LouisYxLu/GMvA/tree/a7207aa645f9a78e255248d299ccfb814e4bb54b) · [表 II–III](https://arxiv.org/html/2504.09197v1#S5.SS2) · [评价入口](https://github.com/LouisYxLu/GMvA/blob/a7207aa645f9a78e255248d299ccfb814e4bb54b/evaluate.py#L24-L47) |
| **MH-T2TA，FITEE 2025**，[5 引](https://openalex.org/W7114911582) | 公布冲突簇和智能评分算法；补充材料 §2.8 中 20／40／60 秒窗的 AF1 为 .8327／.8526／.8888。优先核单点斜率和窗内因果可见性。原分数回答固定窗口关联，逐事件持续 ID 和首报尚缺。 [原文](https://www.fitee.zjujournals.com/en/article/doi/10.1631/FITEE.2400340/) · [补充材料](https://cdn.academax.com/videos/suppl-3a2ce598732f437bbd7d8a9956f55c41-FITEE.2400340suppl001.pdf) |
| **Temporal-MPRF，IET Radar, Sonar & Navigation 2026**，[0 引](https://openalex.org/W7213438482)；**IAGM-TAN，Neurocomputing 2026**，[0 引](https://openalex.org/W7164403432)；**MIS-GNN，Measurement Science and Technology 2026**，[0 引](https://openalex.org/W7167932579) | Temporal-MPRF 为重新命中，另两篇为本轮新增。当前为题录、摘要或出版方章节预览。IAGM-TAN 的双向序列与 Sinkhorn 空配、MIS-GNN 的跨轨软对齐可查其 MTAD 输入范围；三篇的可用实现、窗口时间界及持续发布尚待核。 [Temporal-MPRF](https://doi.org/10.1049/rsn2.70230) · [IAGM-TAN](https://doi.org/10.1016/j.neucom.2026.134264) · [MIS-GNN](https://doi.org/10.1088/1361-6501/ae8929) |
| **TMTAFF，Applied Sciences 2026**，[0 引](https://openalex.org/W7169801238)；**T2T，Pattern Recognition 2026 正式在线、2027 卷期**，[1 引](https://openalex.org/W7203757249) | TMTAFF 是新核到的同 MTAD 来源。§§3.1.1–3.1.2 按 3000 场随机划分，用整场最终配对和融合评价；§5 把实时推理列为后续工作。T2T 公开作者实现，原协议以完整轨迹对为单位。可借鉴缺测及空配设定，分数和数据划分保留各自原协议。 [TMTAFF 原文](https://www.mdpi.com/2076-3417/16/14/7251) · [T2T 原文](https://doi.org/10.1016/j.patcog.2026.114650) |
| **GCI-PMB，IEEE TSP 2026**，[2 引](https://openalex.org/W7123344891)；**Mao 等，IEEE T-ITS 2025**，[5 引](https://openalex.org/W4408859638)；**Castelino 等，Sensors 2026**，[1 引](https://openalex.org/W7140079405) | GCI 有作者代码，在共同融合时钟上交换包含存在概率和状态密度的完整局部后验，原指标为目标集状态。Mao 以实测雷达与磁传感器研究异步迟到，特定道路和传感器几何进入模型。Castelino §§3.2、5 展示原生异步输入对持久全局轨的更新，状态融合对照围绕单受测目标。用来核误差、时钟或发布接口，完整 MTAD 持续 ID 证据待补。 [GCI 全文](https://arxiv.org/html/2506.18397v2) · [固定源码](https://github.com/Agarciafernandez/MTT/blob/cc5c6df0e9343dc1345d91ed6ab95f01db4d1821/Distributed%20MTT/DPMB_GCI_filtering.m) · [Mao 作者稿](https://www.guoqiangmao.com/ewExternalFiles/Mao25Asynchronous-TITS.pdf) · [Castelino 原文](https://doi.org/10.3390/s26062003) |
| **DetectorContext，FUSION 2026**；**Fusion-Poly，IROS 2026**，[预印本 1 引](https://openalex.org/W7134843045) | 前者以真实海事雷达／激光点迹原生时刻更新，表 II 的合计 HOTA 为 81.4，均匀可见性 GM-PHD 为 42.0，雷达独用为 74.3。作者公开了尚未合并的 Stone Soup 实现，原试验依赖视场、检测与杂波模型。后者在 nuScenes 测试集报告 76.5% AMOTA，原同步／异步两种更新使用不同频率的 2D／3D 检测；投影标定、检测置信和框几何均缺于 MTAD。两者可用于异步生命周期的机制阅读。 [DetectorContext 全文](https://arxiv.org/html/2603.15137) · [会程](https://fusion2026.isif.org/fusion2026/thursday.html) · [DetectorContext 作者实现](https://github.com/dstl/Stone-Soup/pull/1291) · [Fusion-Poly 全文](https://arxiv.org/html/2603.08199v1) · [固定源码](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/dataloader/nusc_loader.py#L142-L179) |
| **GMT，CVPR 2026**，[预印本 7 引](https://openalex.org/W4400341618)；**GRAE-3DMOT，CVPR 2025**；**CoopTrack，ICCV 2025** | GMT 固定代码测试时收整段帧再走图像骨干。GRAE 的预测依赖 3D 框尺寸、朝向、分数和单路检测流。CoopTrack 跨代理交互使用学习查询、框和相对位姿。作者代码可查，其表现分别保留在原视觉或协作感知任务。 [GMT 全文](https://arxiv.org/html/2407.01007v2) · [GMT 固定代码](https://github.com/FoxCanned/GMT/blob/2693799fe71d93da47e2887001c88d105a509fc9/gtr/modeling/meta_arch/gtr_rcnn.py#L88-L116) · [GRAE 全文](https://openaccess.thecvf.com/content/CVPR2025/papers/Kim_GRAE-3DMOT_Geometry_Relation-Aware_Encoder_for_Online_3D_Multi-Object_Tracking_CVPR_2025_paper.pdf) · [CoopTrack 代码](https://github.com/zhongjiaru/CoopTrack) |

另核 **LEO，IEEE MFI 2026**。作者全文 §§IV–V 和正式会程可核。雷达、LiDAR、相机的局部跟踪输出按最近观测前向投影入图；依赖形状端点、方差、二维速度和自车状态。原表评价轮廓、召回和速度，暂无公开实现与持续全局 ID 证据。**Su 等，IEEE TVT 2025** 的出版摘要表明跨代理关联针对漏检和 ID 切换，期刊全文、源码及在线信息边界待核。 [LEO 全文](https://arxiv.org/html/2604.02206v1) · [MFI 会程](https://www.mfi2026.org/program.html) · [Su 出版记录](https://doi.org/10.1109/TVT.2025.3577676)

## 前向引用及可核后继

按 OpenAlex `filter=cites:<work-id>` 读取 CDP-WGL、Lindenmaier、GMvA 的 16／7／21 条引用条目，再到原文核已读条目。Lindenmaier 路线的 Bóka 论文明确延伸两阶段存在概率。CDP-WGL 的引文中，Wang 等 2025 在正文参考文献第 24 项引用，采用视场分区和 CPHD 后验融合；CFAG-GLM 和 Yu 等 LMB 可学习匹配仍需全文来判断是否复建或直接修改过 CDP-WGL。GMvA 的引文中，Ma 等 HDLGNN 参考文献第 29 项引 2025 预印本，公开摘要给出图关联模型，未确认可复用代码或继承原系统。引文列表还含图像增强、标定和综述等不同任务，引用总数不能替代改造记录。 [Wang 原文](https://www.mdpi.com/1424-8220/25/13/4241) · [Yu 出版摘要](https://ieeexplore.ieee.org/abstract/document/11273043) · [Ma 参考文献](https://link.springer.com/article/10.1007/s42401-026-00490-1)

## 进入下一阶段所需证据

本轮没有冻结主基线名单。Lindenmaier／Bóka 的状态和生命周期输入、CFAG-GLM 的完整算法、CDP-WGL 的低人口规则、Draves 的双源发布、GMvA 与 MH-T2TA 的固定等待行为，各自还有会改变比较含义的缺口。对同类候选先追直接后继与原文对照，再完成逐篇来源分析。可获得源码时记录实际入口和软件许可，可独立复建时列出公式、缺省值与作者可核结果。对必要适配明确核心算法、输入重建及发布差异。完成后把可比的候选与未排除解释并入 Mode C，形成事前 Idea，再从首报做 MTAD 开发验证。保留单源、稀疏、空配和全部覆盖分母，比较同信息与同延迟下的持续 ID、错漏配、错链、首报、确认等待和处理成本。
