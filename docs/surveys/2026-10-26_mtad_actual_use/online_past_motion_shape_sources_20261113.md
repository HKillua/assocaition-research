# 速航字段来源与已到位置的历史运动

2026-11-13。问题为同航的两组配对几何接近时，有无能在接回前提供区别的运动信息。检索原生 Doppler、海事航迹速航和异步整轨对照，按硬件观测、位置衍生和整轨权限筛选。DE 为直接证据，SC 为作者报告，AI 为本项目推断，UN 为未知。

|来源和阅读范围|DE 与 SC|AI 与 UN|
|---|---|---|
|既有 E-ON1，MTAD 原文 §2.1、§2.6(h–j)，Level1 八场审计|母AIS有速航。源轨迹按经纬扰动后重新生成速航。实测早行速度295,148／295,187在后一段几何速度1%内，航向295,177／295,187在1°内。|在后一端点到达前不能使用原速航；到达后可由位置重算。上游处理和真实到达未交付。 [原文](https://jeit.ac.cn/cn/article/pdf/preview/10.11999/JEIT221202.pdf) · [字段合同](../../data_contract.md#在线字段可用时间)|
|E-ON224，Kim 等，IEEE IV 2025，作者稿 §§III-D、IV-B 表 I|先位置关联，再用硬件 Doppler 支持第一步未匹配候选。固定一种检测器时 AMOTA .519→.521、IDS 177→170；另一配置 .539→.542、IDS 222→246。|硬件读数与几何坐标的来源不同，身份收益依赖条件。MTAD 没有对应 Doppler。 [作者稿](https://arxiv.org/html/2502.01357) · [会刊](https://doi.org/10.1109/IV64158.2025.11097628)|
|E-ON225，Wang、Li、Shi，Signal Processing 2025，出版预览 §§1、4|运动滤波先用位置速度缩候选，多帧回波分布再排序。作者报告琼州海峡雷达／AIS 实测及杂波抑制 F1 提升5.82%。|外部回波来源是真正额外的证据，MTAD 不具备；可借鉴将候选与新增信息分开。完整细节与独立消融未核。 [出版预览](https://www.sciencedirect.com/science/article/abs/pii/S0165168425001483)|
|E-ON226，Chae 等，ICCV 2025，全文 §§2.2、4|LiDAR／RADAR 单帧检测分别编码反射功率和径向 Doppler；本文传感器范围及分辨率不能完整解算绝对速度。多帧跟踪留作后续。|单帧探测的提升不能作为持续 ID 证据。测量可用性也要和模型输入分开。 [会刊全文](https://openaccess.thecvf.com/content/ICCV2025/papers/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.pdf)|
|既有 Wan 等，IJTST 2025 卷期，全文 §§2.2–2.3、3.5 及公开代码入口|分开比较位置、速度和圆周航向，按 DTW 汇总。10 场由原母AIS再抽样加噪，允许整轨；场44速度差小且多属性臂退化，论文与代码的空配合同有区别。|对照应固定已到时间和共同历史，区分一般净位移与段间变化。整轨代码不直接迁移。 [全文](https://doi.org/10.1016/j.ijtst.2024.03.001) · [作者代码](https://github.com/SkiWWWW/Track-to-Track-Association-Algorithm-of-DTWCM)|
|既有 S-ON150，He 等，Sensors 2025，全文 §3.2.1–2、§4|现场多源船舶数据中 AIS、雷达和视觉按雷达时刻进入级联指派。式12–13比较速度模和向量夹角，式13印刷与文字不符。|未给单独速航对 ID 的同口径消融。保留为外部数据候选，严格在线输入时刻需单独查。 [全文](https://www.mdpi.com/1424-8220/25/7/2179) · [作者数据入口](https://github.com/yixiiii/Multi-Source-Fusion-for-Vessels)|

C-ON38 已查四端共同过去20秒的单段位移，C-ON39 已查四端续报及共享偏差，过去两个60秒段仅用于独立历史锚或环候选资格。本轮转到固定四端组的直接排序，比较相同历史的净位移与两段运动变化。历史位置已经进入原滤波，新增的是时序表达。 [Mode C v52](online_causal_replay_mode_c_20261111.md#v52-原始速航权限与历史运动)

## 外部数据能补哪项证据

|数据或论文|可核字段与可测问题|仍缺的条件|
|---|---|---|
|Autoferry 作者公开版，及主仓 C128 实测|雷达和 LiDAR 是独立物理通道，检测提供量测时刻和坐标，标签提供两条目标船 GNSS。C128 的9场已有8场可见近距双船、双源和双GNSS，可作持续 ID、漏检及延迟的开发级外部机制试验。|发布检测没有原生 Doppler 或单独收报时钟。C128 的静态近距检验也没有建立连续跟踪身份。该9场已有开发用途，独立确认另需数据。 [作者字段和场景](https://autoferry.github.io/sensor_fusion_dataset/) · [既有资格审计](https://github.com/HKillua/association-code/blob/399da72/offline_observation/docs/reports/2026-11-13-autoferry-dual-gnss-eligibility-review.md)|
|Mariner 作者公开海试，Hem 等，IEEE Access 2024 §VI-B|雷达按扫描组织，AIS 按到达组织并带速航，目标 GPS 另列。可核输入 AIS 实测速航与位置历史的差异。|发布结构各只有一个 UTC，持续跨源配对标签未显式交付，论文闭环示例重点是单机动目标。不同图的数据包括仿真与实测，须先核对应文件。 [作者数据结构](https://github.com/autosit/autonomy-field-test-data/blob/6e1a0bf23f831f778aa9c793d49d9adf6da95814/README.md) · [原文](https://doi.org/10.1109/ACCESS.2024.3389824)|
|WHUT-MSFVessel 作者说明，He 等，Sensors 2025|原编码 AIS、带时间雷达帧、分别标注的 radar/visible 轨迹。|公开说明未列雷达ID到AIS MMSI的映射，也未区分源事件与接收时间。需核实际开放样本才能判断跨源 ID。 [作者字段清单](https://github.com/yixiiii/Multi-Source-Fusion-for-Vessels#details)|
|DLR HAXR 作者数据页，2026|13站 X 波段实测回波幅值、原单流 AIS、旋转窗口。允许将 AIS 只留作伪参考，研究两站回波与扫描证据。|原始回波还需检测到轨迹的明确处理，数据公开页称 AIS 为伪参考。原生接收日志、跨站检测真配对均未交付。 [DLR 官方页](https://www.dlr.de/en/kn/about-us/departments/nautical-systems/real-world-marine-radar-datasets-for-target-tracking)|
|Du 等，ISPRS JPRS 2026，出版预览；Zhao 等，IET ITS 2026，全文 §4及数据声明|前者用短时运动＋空间后再图正则，声明增量更新；后者有珠江口实际岸基雷达与 AIS 的同步关联，评价图匹配。|前者完整时窗、速度消融、真实收报未知；后者数据按请求提供，同步关联指标不是连续发布。两者当前均无可直接复跑的在线数据协议。 [Du](https://doi.org/10.1016/j.isprsjprs.2026.07.005) · [Zhao](https://doi.org/10.1049/itr2.70166)|

以上是已核的外部方法与数据字段。在线实证范围以主仓研究状态为准，当前只使用 MTAD。
