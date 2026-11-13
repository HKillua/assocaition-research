# 2025–2026 在线运动、关联和持续状态来源分析

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-RECENT-2025-2026-20261112`，2026-11-12，partial。按运动组件对照、非等间隔预测、多源弱观测及身份歧义分别检索并核原文。S-ON100–111 为本轮新纳入的 12 篇。11 篇核得正式会刊记录，Fusion-Poly 有作者接收声明及 IROS 会议索引转录，IEEE 出版记录待核。已入库的 S-ON21 仅回读。纯预印本、只有摘要的条目和已读的同一篇均不计入。范围为机制、原表、反例和可复现资产的定向核对，未做全面计量综述。

SC 表示作者主张，DE 表示原文和静态代码直接证据，AI 表示对 MTAD 的推断，UN 表示未确认条件。输入依作者协议，论文成绩彼此不可直接合并。当前分析未执行任何作者代码。下游候选问题包括对侧历史能否修正门内排序、同源邻轨何时提供独立证据、弱更新是否积累持续错链，以及未见真对侧能否区分缺报与可拒配。 [Mode C v20](online_causal_replay_mode_c_20261111.md#v20-近期学习基线和可获得的运动信息)

## S-ON100 Song 等，HyperSSM，CVPR 2026
- **SC** 单目标运动预测忽略共同运动与遮挡期线索，相关目标的运动可协同稳定预测。**DE** §3.2–3.3、式 3–5、图 2–3。对五帧盒位置和尺寸差分做 EMA，将运动表示近邻按阈值连成超边，先从顶点聚合到超边再散回顶点，把超卷积嵌入 SSM 状态转移，最后预测下一帧。§4.1 运动训练用轨迹片段，不读图像，输入仍有盒宽高；整体 tracker 在 §3.4 接 YOLOX 检测与多置信层关联。训练分数据集 260 或 360 epochs、batch 128，不能把作者推理框架作为无影像原生实现。 [正式论文](https://openaccess.thecvf.com/content/CVPR2026/papers/Song_Hypergraph-State_Collaborative_Reasoning_for_Multi-Object_Tracking_CVPR_2026_paper.pdf) · [作者全文](https://arxiv.org/html/2604.12665)
- **DE** §4.3 表 5 固定检测和关联，只换运动模块。MOT17 半训练／半验证的 KF、OC-KF、独立 SSM、HyperSSM HOTA 为 64.5／64.6／63.4／65.5，DanceTrack train→val 为 47.0／52.5／53.7／59.7。独立 SSM 在 MOT17 反而比 KF 低 1.1。表 6 改超边阈值 .5／.8／.98，MOT17 验证 HOTA 47.7／65.5／64.7。表 7 同 YOLOX-X 报 20.3→17.5 FPS，但在全 MOT17 训练集上训练及推理，不能当独立测试，也不能把检测开销当运动模块延迟。**AI** 同航道共动可能给运动补充支持，也可能使错误身份更相似。邻居增量应在固定候选、校正及关联下对照独立时序模型和无邻居层；按相近运动对象数、转弯、短史及场景组件评估。**UN** 不规则海事到达、无尺寸输入、航路变换、真实端到端延迟与不确定性校准。 [原文 §4.3](https://arxiv.org/html/2604.12665#S4.SS3)
- **资产与权限** 作者 HyperMOT 公开树有训练、评估、配置、模型、跟踪器及测试源码，未发现仓内权重。论文未在所核算法段规定不足五个实际报告的处理，现仓代码提供直接证据。评估入口所用 BYTETracker 初始把第一框和零差分放进长度由 interval 配置的 deque，预测时追加自产状态，匹配后把对应条目替换成新观察。生成器取最近 interval 条，不足时在序列尾部重复最后一条，超图推理掩码将全部传入目标标为有效。训练集的补零掩码针对同批目标数量，不能与推理时的短时间史等同。**AI** 这些自产状态可以因果使用，使用时需区别实测，并另报首点／缺报。未安装或执行代码。 [跟踪器初始及滚动更新](https://github.com/SkyeSong38/HyperMOT/blob/4819e3fb64c8f075fe76d4f15901393e44bb76a7/tracker/BYTETracker.py#L59-L149) · [生成器](https://github.com/SkyeSong38/HyperMOT/blob/4819e3fb64c8f075fe76d4f15901393e44bb76a7/models/autoencoder.py#L30-L67) · [训练集掩码](https://github.com/SkyeSong38/HyperMOT/blob/4819e3fb64c8f075fe76d4f15901393e44bb76a7/dataset/hyper_dataset.py#L45-L80)

## S-ON101 Kim 等，Dual-Path Temporal Decoder，NeurIPS 2025
- **SC** 让一条分支适配当前外观，另一条保留身份线索，可缓解低可信检测造成的身份漂移。**DE** §3.2–3.3、式 3–6，外观分支动态更新 query；身份分支在 decoder 层间固定轨 query 并重用上一帧采样偏移，框中心仍迭代细化，采样的是当前图像特征。两路状态融合，低置信时抑制历史轨 query 更新。不是把历史坐标直接冻结。 [正式论文](https://proceedings.neurips.cc/paper_files/paper/2025/file/07054a34f24ac3ef64c5f2fdf571b8c0-Paper-Conference.pdf)
- **DE** §4.4 表 4，DanceTrack-val 无 IDL／变偏移／固定历史偏移的 HOTA 为 66.7／67.5／69.1，AssA 为 56.3／59.0／61.6。表 5 从不抑制到 β=.4，HOTA 67.9→69.1，AssA 59.2→61.6，DetA 78.1→77.8，说明身份增益可伴检测指标下降。MOT17 test 表 3 的 HOTA 61.5 低于 MOTRv2 62.0，AssA 62.5 则高于 60.6。**AI** 分开连续运动更新和身份记忆更新值得检验，尤其错误合并后是否继续污染后续状态。**UN** MTAD 缺视觉 query、视觉置信和框内偏移，需独立验证物理残差、候选竞争或历史更新能否成为可靠证据。 [原文 §4.4](https://proceedings.neurips.cc/paper_files/paper/2025/file/07054a34f24ac3ef64c5f2fdf571b8c0-Paper-Conference.pdf)
- **资产与权限** 作者仓有训练入口、模型、配置、视频数据处理和 CUDA 扩展说明，尚未下载或执行。公开视觉权重或同数据复现不能替代 MTAD 许可。 [作者仓](https://github.com/altkddhfcjs/DualTemporalMOT)

## S-ON102 Wang 等，LA-MOTR，ICCV 2025
- **SC** 解耦当前物体与历史轨检测，再让关联可训练，可减轻共用 decoder 的训练目标冲突。**DE** §§3.1–3.4，SOTD 用两个分支解码同一帧图像；SGLA 每层把物体与历史轨的预测框差编码成相对空间特征，用关联矩阵作为后续层注意力 logit 的附加项，同时交换两组 embedding 的上下文。训练分别监督检测、轨迹和关联。两边空间预测已经含当前图像信息，不能将数值收益直接归因于时间外推。 [正式论文](https://www.openaccess.thecvf.com/content/ICCV2025/papers/Wang_LA-MOTR_End-to-End_Multi-Object_Tracking_by_Learnable_Association_ICCV_2025_paper.pdf)
- **DE** §4.4 表 4 DanceTrack-val，单 decoder／SGLA 去 RSC／完整 SGLA 的 HOTA 60.220／62.753／64.474，AssA 47.509／49.084／51.913，各方案重训。表 5 双向 concat 自注意 HOTA 64.474，两个交叉注意方向 63.896、64.008，后一方向 IDF1 67.194 高于 concat 66.956。表 6 作者轨迹更新 HOTA 64.474、AssA 51.913，替代 TIM 为 64.589、52.159。**AI** 借鉴的是同一前端和候选图上把相对位移、观测年龄和运动不确定性供给边分数。缺乏双侧分支时，同帧全局上下文的关联增量不容易识别，须保留分支支持诊断。**UN** 无图像且首报只有一位置时的有效表示、开放未匹配和共享组件泛化。 [正式论文表 4–6](https://www.openaccess.thecvf.com/content/ICCV2025/papers/Wang_LA-MOTR_End-to-End_Multi-Object_Tracking_by_Learnable_Association_ICCV_2025_paper.pdf)
- **资产与权限** 论文给出的作者 GitHub 链接，本次网页与公开仓库内容接口均返回 404。代码、权重和可执行复现状态仍待核。 [原文所列链接](https://github.com/PenK1nG/LA-MOTR)

## S-ON103 Kim 等，PlugTrack，AAAI 2026
- **SC** 线性和非线性运动会共存，按轨迹状态混合 KF 与数据驱动模型可以缓解单一预测器偏差。**DE** 原文 Proposed Method，式 1–12。五帧盒轨迹输入两层 128 维 LSTM，附加 KF 与 DiffMOT 或 TrackSSM 下一帧预测差、KF 已有观测的逐维创新平方／方差及其三帧汇总。输出每维混合权重。训练时用带高斯扰动的 625 组权重对真实下一帧框择优作为软目标，测试只运行学习权重。训练分域，Adam .001、batch 2048、220 或 270 epochs。未来框只作训练目标。 [正式论文](https://ojs.aaai.org/index.php/AAAI/article/download/37491/41453) · [作者稿含附录](https://arxiv.org/html/2511.13105)
- **DE** Fig. 2，作者报告 KF 在 MOT17 的 12,061/20,000、DanceTrack 的 1,700/5,000 条评估 tracklet 上优于所比数据预测器。表 3，DanceTrack→MOT20 的 TrackSSM HOTA 47.7→54.2，反向 52.5→54.3。表 5，DanceTrack-val 直接送历史给混合权重模型的 HOTA 59.2，加入时序模块 60.2，三模块完整 60.8。表 1 DiffMOT 上仍有单指标下降，表 4 TrackSSM 37.2→34.2 FPS、DiffMOT 25.9→24.7 FPS。**AI** 对 MTAD 首测可让 CV-KF 和独立非线性运动器共享合法历史，比较固定混合、仅由已到同源创新和时距决定的混合，再考虑监督权重。用未来轨迹优化权重只能是训练目标或诊断。**UN** 创新若由已接受但实际错配的跨源量测形成，是否会把关联错误当机动并强化错误。框尺寸、GIoU 与原视频权重不对应严格 MTAD。 [正式论文 Fig. 2／Tables 1、3–5](https://ojs.aaai.org/index.php/AAAI/article/download/37491/41453)
- **资产与权限** 作者树实查只有两份针对 DiffMOT／TrackSSM 的集成样例，以及 blender、contextual motion encoder、Kalman filter 三个 assets 源文件。README 链接外部预训练模型，未下载核验。仓内没有完整 detector／tracker、端到端训练／评价入口或权重文件，不能把这些片段算完整复现。 [作者仓](https://github.com/VisualScienceLab-KHU/PlugTrack)

## S-ON104｜Fusion-Poly，IROS 2026
**正式出处与阅读范围。** Xian Wu 等，*Fusion-Poly: A Polyhedral Framework Based on Spatial-Temporal Fusion for 3D Multi-Object Tracking*。作者仓注明 IROS 2026 已接收。会议索引的第三方转录列 #2446、T2LBY05，官方索引本次无法直取。核作者 2026-08-04 v2 正文 §III–IV、表 I–VII 和公开实现，正式 IEEE DOI 未核得。 [作者全文](https://arxiv.org/html/2603.08199v2) · [作者仓接收说明](https://github.com/K544-AD/Fusion-Poly/tree/cfca8596b0bfa99fd318a21fae690bc9dff90ef2) · [会议索引转录](https://raw.githubusercontent.com/gisbi-kim/iros2026-explorer/main/output/papers.json)

**SC／DE，方法。** 作者主张异频弱观测可在共同扫描之间维持运动和存在状态。§III-C–E 先按观测组合级联匹配，同步时依次用混合、纯 3D、纯 2D，异频时将已有轨迹投影到图像，按 IoU 匹配 2D 框。位置更新使用 KF，存在评分单独衰减与 Noisy-OR 更新。式 8–11 的方差推导假定两源分数无偏且噪声不相关、组合取最优权重、当前更新的先验评分固定。该推导约束的是评分方差，身份正确率和实测置信校准另需证据。 [方法原文](https://arxiv.org/html/2603.08199v2#S3)

**DE，试验与反例。** nuScenes 总计 1,000 个真实驾驶场景。§IV-A/B 的标注评价仍在 2 Hz 关键帧，每两个关键帧间从真实原始相机图像预先选择最接近中点的一帧，形成约 4 Hz 输入，LiDAR 检测保持 2 Hz。验证表 III 同检测器，全方案从 2→4 Hz，AMOTA 76.9→77.1，IDS 446→416，FP 13,131→12,679，FN 15,894→15,974。只有加密输入的 Exp0→4，AMOTA 75.5→75.4、IDS 884→886、FN 16,804→17,425。异频级联已有的 Exp5→6 增加存在处理后 AMOTA 76.6→77.0、IDS 463→420、FN 15,678→15,967。表 VII 的 Noisy-OR 比 Max 为 77.1 对 75.9 AMOTA、416 对 484 IDS。测试表 I 的 76.5 AMOTA 使用另一检测器组合，不能并到验证消融。 [表 I–VII](https://arxiv.org/html/2603.08199v2#S4)

**AI／UN，迁移与资产。** 保留弱单源观测可维持旧身份这一可检验假设，原文依赖相机标定、2D/3D 框、分类和检测置信。MTAD 位置报文缺这些输入，且应区分源没有发报与源扫描为空。公开 Python 代码按 `frame_id` 与 `is_key_frame` 驱动，运动模型的名义间隔取配置，未核其支持任意原生时间间隔。约 4 Hz 中点重采样和 2 Hz 评分是记录回放条件，缺独立网络到达与乱序评测。未运行代码。 [轨迹更新源码](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/tracking/nusc_tracker.py#L57-L100) · [置信源码](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/tracking/nusc_score_manage.py#L57-L137) · [运动源码](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/motion_module/kalman_filter.py#L30-L42)

**2026-11-12深层源码补证。** loader时间字段为item、KF固定Δ，test只写关键帧；async_2d_motion_update随后无条件恢复state/P。当前SHA的异步相机主要更新存在/寿命，未证明实际运动校正。另核未配2D不出生、入口缺auto_finetune_module和代码许可缺项。[E-ON119完整证据](online_fusion_dataset_code_audit_20261112.md#e-on119fusion-poly-的内部更新与公开输出)，不将原文成绩推为该源码已独立复现。

## S-ON105｜SparseCoop，AAAI 2026
**正式出处与阅读范围。** Jiahao Wang 等，*SparseCoop: Cooperative Perception with Kinematic-Grounded Queries*，AAAI 40(12), 9876–9884，DOI `10.1609/aaai.v40i12.37952`。核正式正文 §3–4、表 1–2、图 6–7 和作者关联实现。 [正式记录](https://ojs.aaai.org/index.php/AAAI/article/view/37952) · [正式全文](https://ojs.aaai.org/index.php/AAAI/article/download/37952/41914)

**SC／DE，方法。** §3.2–3.5 用各方递推的稀疏对象查询表示目标。查询携带 3D 几何、速度、置信和外观特征。将远端位置用实际查询时间差做 CV 投影，结合 3D 状态 L1 与特征余弦代价，匹配后粗融合。符合交互筛选的两侧未匹配查询也进入后续跨时刻、跨源与图像特征细化，远处目标可走直接输出路径。训练以真值构造去噪查询，分别注入本地量测与跨源变换扰动，并将其与普通查询隔离。 [方法原文](https://arxiv.org/html/2512.06838#S3)

**DE，试验与反例。** 表 1 的真实 V2X-Seq 是 2 Hz 验证回放，SparseCoop AP/AMOTA 为 .530/.421，CoopTrack .390/.328，末端融合 .196/.263。Griffin-25m 是模拟验证集，SparseCoop .559/.509、11.64 FPS、9.73×10⁴ B/s。正文的最高性能说法按表头应限于中间融合，表列早期融合 .607/.670 更高，代价 3.11×10⁸ B/s、5.17 FPS。表 2 在真实验证集去掉延迟补偿 .505/.414，去掉几何外观匹配 .502/.414，去掉粗融合 .489/.375，去掉多上下文 .512/.379，去掉变换噪声训练 .531/.394。图 6 显示交互范围过小会留下重复目标，AMOTA 峰值范围随数据从 30 m 变为 15 m。图 7 人为延迟加在模拟 Griffin，论文报告 ≥200 ms 时 AP 超过早期融合，整体仍随延迟退化。 [正式全文，表 1–2、图 6–7](https://ojs.aaai.org/index.php/AAAI/article/download/37952/41914)

**AI／UN，迁移与资产。** 未匹配仍可维持候选和单源输出，随后用到达证据减少重复，是可分离检验的机制。论文的 GPS／姿态变换、已估速度、框、图像特征和局部查询置信不属于严格 MTAD 字段。AMOTA 和模拟延迟 AP 没有分离固定发布下的错链持续和修订代价。公开 MIT 仓有训练、测试、分割及 Griffin 人为延迟配置，代码确实用两时戳之差投影，也有输入几何筛选与查询补全。未运行训练，最终模型权重未核。 [作者代码](https://github.com/wang-jh18-SVM/SparseCoop/tree/1f5741ccc62be8d8d5bedd296615b75b4c10fc7e) · [时差投影与筛选](https://github.com/wang-jh18-SVM/SparseCoop/blob/1f5741ccc62be8d8d5bedd296615b75b4c10fc7e/projects/mmdet3d_plugin/models/instance_bank.py#L705-L741) · [查询融合](https://github.com/wang-jh18-SVM/SparseCoop/blob/1f5741ccc62be8d8d5bedd296615b75b4c10fc7e/projects/mmdet3d_plugin/models/instance_bank.py#L1112-L1216)

## S-ON106｜V-PMB 坐标下降推导，FUSION 2026
**正式出处与阅读范围。** Ángel F. García-Fernández、Yuxuan Xia，*Variational PMB filter via coordinate descent Kullback-Leibler divergence minimisation*，FUSION 2026，DOI `10.23919/FUSION67272.2026.11726766`。读作者全文 §II–VI、表 I、附录关键式及作者 MATLAB 投影实现。 [IEEE 记录](https://ieeexplore.ieee.org/abstract/document/11726766) · [作者全文](https://arxiv.org/html/2605.07309) · [会议日程](https://www.ntnu.edu/fusion2026/friday)

**SC／DE，方法与证明。** 新增点是重推已有 V-PMB。在含轨迹索引和全局假设变量的增广空间，交替更新 PMB 分量和逐假设置换，置换步骤用二分指派。§III 式 15、22–24 的交替步骤使该 KLD 目标不增加。式 25–26 的精确混合推导保留 PHD（一阶目标强度），并未证明持续身份、全局最优或经过 Gaussian 矩匹配后仍逐点保持强度。§IV 使用 Gaussian 状态和存在概率实现。 [§II–IV](https://arxiv.org/html/2605.07309#S2)

**DE，试验与反例。** §V 用已知扫描机会的单源二维位置仿真，101 步、100 次 MC，四目标中点靠近，一目标在第 50 步消失。近匀速，扫描间隔 1，R=I，pS=.99，平均杂波 10。pD=.9 时表 I 的 PMBM/Murty-PMB/BP-PMB/GNN-PMB/V-PMB RMS-GOSPA 为 2.68/3.07/3.26/3.54/2.83，Intel Core Ultra 7 155H 上整段平均 4.2/.4/.3/.3/1.9 秒。PMBM 保留 200 假设且总体最好。V-PMB 接近 PMBM，但主要差异集中于消失目标持续造成的假目标代价。pD=.99 时 GNN 2.83 略优 BP 2.85，顺序应以表为准。BP 无门控，其他所述实现用椭圆门，不能把性能或速度差全归给边缘化。 [仿真、图 2–3、表 I](https://arxiv.org/html/2605.07309#S5)

**AI／UN，迁移与资产。** 支持把保留互斥假设及压缩方式作为竞争分量中的独立对照，也提示成本和消失处理会影响表面收益。移植完整滤波需明确定义 MTAD 的检测机会、杂波、出生与寿命，原论文未评价异步多源或身份连续。作者 MATLAB 公开，`VPMB_projection.m` 用普通 PMB 初始化、逐假设重排、阈值和迭代上限。未执行代码。 [作者投影源码](https://github.com/Agarciafernandez/MTT/blob/master/PMBM%20filter/VPMB_projection.m)

## S-ON107｜OptiPMB，IEEE T-ITS 2025
**正式出处与阅读范围。** Guanhua Ding 等，*OptiPMB: Enhancing 3D Multi-Object Tracking With Optimized Poisson Multi-Bernoulli Filtering*，IEEE T-ITS 26(12), 22312–22328，DOI `10.1109/TITS.2025.3619674`。核作者 v2 正文 §IV–V、表 I–II、V–VI 及公开 Python 代码，版本日期为 2026-02-03，正式刊期为 2025 年 12 月。 [IEEE 记录](https://ieeexplore.ieee.org/document/11218799/) · [作者全文](https://arxiv.org/html/2503.12968v2)

**SC／DE，方法。** 将在线单框检测的 GNN-PMB 改成有自适应检测概率、量测驱动混合出生、PPP 裁剪和提取机制的持续状态系统。§IV-D–H 只保留全局最佳匹配，目标出生得到固定 ID，临时漏检由存在后验和漏检计数共同决定输出。式 34 的检测概率从预测 3D 框内 LiDAR 点数估可见性，式 35–36 的未匹配出生分流用检测置信区分杂波和潜在出生。 [§IV](https://arxiv.org/html/2503.12968v2#S4)

**DE，试验与反例。** 真实 nuScenes／KITTI 记录的逐帧检测回放。nuScenes test 表 II，同 CenterPoint 下 GNN-PMB AMOTA .678、770 IDS，OptiPMB .713、257 IDS，同时 NEBP 的 227 IDS 更少。nuScenes val 表 VI，共用 CenterPoint，原基线 AMOTA .696／FP 12,362／FN 20,421／IDS 250／17.5 FPS。单加自适应检出变为 .688／13,755／21,458／178／15.4，减少换手同时增加假漏；单加出生变为 .726／14,403／16,061／214／20.1，明显增召回也增 FP；全模块 .741／12,677／16,707／227／11.3。计时排除检测器，不能当端到端时延。KITTI 表 V 中同 CasA 下 OptiPMB 相较 RobMOT HOTA 81.76 对 81.22，但 IDS 17 对 6。 [§V，表 II、V、VI](https://arxiv.org/html/2503.12968v2#S5)

**AI／UN，迁移与资产。** 可以独立检验生存、出生和确认对持续错链、漏链的影响，原系统按 LiDAR 帧到达，既无跨源轨迹身份交换，也没有通过 1 Hz 无报文时刻产生可信负证据。MTAD 缺点云可见性及检测分数，不能将报文缺席替代原式的可见性。作者仓有 Python 跟踪入口、配置及公开检测结果说明。作者 v2 式 28 对未检测 PPP 印成乘 pD，公开源码 L679 实际乘 `(1-p_D)`，这里保留来源差异，未核正式排版勘误。未运行代码。 [作者仓](https://github.com/dinggh0817/OptiPMB/tree/ed0e0467efb08fd8a96b03647b09169564a74acd) · [自适应检出实现](https://github.com/dinggh0817/OptiPMB/blob/ed0e0467efb08fd8a96b03647b09169564a74acd/trackers/OptiPMB/OptiPMB_Tracker.py#L445-L462) · [PPP 更新](https://github.com/dinggh0817/OptiPMB/blob/ed0e0467efb08fd8a96b03647b09169564a74acd/trackers/OptiPMB/OptiPMB_Tracker.py#L673-L680)

## S-ON108 Wei、Liang、Meyer，NEMOT，IEEE TSP 2026
- **SC** 用学习分别补充贝叶斯多目标跟踪的状态预测和量测更新，可保留显式关联、漏检及出生语义。**DE** §§III–V。运动核以当前二维位置与速度、上一步 GRU 隐状态及按距离加权的邻居位置速度为条件，做非 Markov 概率预测，初始隐状态为零，不足邻居权重为零。§IV-B 作者报告试过学习式 query/key 权重，在现数据上不及距离规则，未给定量对照。sigma points 将个体或联合状态不确定性传播进转移，粒子近似预测分布。更新核另依赖 LiDAR／相机 BEV、框尺寸和方向来学习亲和及假阳性似然因子，以含未配状态的双向一致因子图做 loopy BP。§VI-B 运动预训练使用加噪、加偏和随机删状态的真值轨迹，再联合优化。运动可单独启用而量测保持经典模型。 [正式发表](https://ieeexplore.ieee.org/document/11353058/) · [作者稿 v3](https://arxiv.org/html/2506.18124v3)
- **DE** §VII-B 表 III，nuScenes-val 基础／仅学更新／仅学预测／两者 AMOTA 75.5／76.7／76.6／77.2，AMOTP 52.0／49.5／50.0／49.7，完整模型的定位指标略输只学更新。表 IV 的同一历史来自量测与真值 Hungarian 对齐，评的是有身份锚的一步位置预测。CV／个体历史／个体与邻居历史的车辆 MSE 为 .434／.299／.285，行人为 .090／.061／.058。前一变化同时换了 CV 与学习式转移，不能单归因于历史长度；后一变化更接近邻居信息增量。表 V 的端到端跟踪用经典量测更新，独立 sigma points→联合 sigma points AMOTA 76.6→76.6、AMOTP 50.2→50.0、4→2 FPS。**AI** 先做仅本轨历史的预测对照，邻居输入再做独立开关，同样报连续身份与预测误差。**UN** 当前 MTAD 的异步时间、位置派生速度、无可靠邻居身份时，论文的优势和标称置信度均未建立。 [原文 §VII-B](https://arxiv.org/html/2506.18124v3#S7.SS2)
- **资产与权限** 期刊和作者实验室公开论文。此次未找到对应 NEMOT 实现或权重的可核链接。BEV 与视觉量测增强必须从严格 MTAD 的仅位置运动适配中剥离，且训练标签不得进入预测。 [作者实验室](https://fmeyer.ucsd.edu/) · [作者稿](https://arxiv.org/html/2506.18124v3)

## S-ON109 · MOSES，ICLR 2026
**定位**　Yalavarthi 等，*Reliable Probabilistic Forecasting of Irregular Time Series through Marginalization-Consistent Flows*。读会议原文 §2–5、表 2–4。 [会议原文](https://proceedings.iclr.cc/paper_files/paper/2026/file/899c6a43b9976e1077522fe5a39cafa3-Paper-Conference.pdf) · [作者代码](https://github.com/yalavarthivk/separable_flows)

- **SC**　对任意变量及不规则预测时点给出边缘一致的联合预测，联合训练还能改善部分边缘预报。
- **DE**　给定观测历史，潜在多元高斯混合的权重与请求的查询点集合无关，均值、低秩相关与方差按查询坐标生成。逐坐标可逆映射保留相应边缘关系。作者比较先在同一时间坐标上建联合模型，再边缘化，与直接查询子集的数学一致性。四数据集是气象和医疗，医疗为 36 小时历史和 3 个未来预测步，数据拆分 70/10/20。表 2 联合训练后 MIMIC-IV 边缘 NLL，ProFITi 0.500±0.322、MOSES −0.634±0.017。表 3 同场联合 Energy Score 0.808→0.906，越低越好，且边缘 CRPS 0.279→0.245。表 4 比较不同编码器。
- **AI**　不同候选的最后报告年龄各异，统一查询到同一比较时间可避免拿不同时间状态直接比。先用共享历史编码器及均值比较高斯与混合似然，再核是否确实需要可逆变换。数学一致性可核，概率校准和关联收益需各自检验。
- **UN**　未见开放人口身份、显式无配、单点首报、同源重复或跨源误差相关实验。无 MTAD 预训练权重，也无证据表明联合似然能区分一个几何合理的唯一假候选和真边。

## S-ON110 · MFPD，AAMAS 2025 Research Paper Track
**定位**　Ma、Han、Yao，*Multi-Ship Future Interaction Trajectory Prediction via Pre-Initializer Diffusion Model*，页 1408–1417。读 §3.1–3.5、图 2–3、§4.2–4.5 表 1–2。 [会议原文](https://www.ifaamas.org/Proceedings/aamas2025/pdfs/p1408.pdf)

- **SC**　用预初始化器替代前段扩散采样，再用少量迭代细化，有望减少推断耗时并保留交互多模态预测。
- **DE**　初始分布由条件均值、方差和相关样本生成。条件还读 AIS 船属性、速航和按船首向旋转的 ENC。§3.2 从历史轨迹描述未来条件的编码。§4.3 明确周围船未来状态由同维度 RNN 预先生成，再由 BiLSTM 编码。威海使用 20 秒采样，表 2 的 10 步预初始化版 minADE/minFDE 15.68/22.87 m、0.15 秒，去掉预初始化后的 200 步为 16.51/23.59、3.11 秒，20 步为 21.34/28.61、0.29 秒。一起移除未来交互和 ENC 为 17.53/26.41 m、约 0.15 秒，无法分别归因。表 1 南通 5 分钟下 MFPD minADE 6.15 m，LED 为 6.02 m。
- **AI**　船舶邻居运动确有同域方法先例。多样本的最小误差适合检验预测覆盖，无法直接代表到达一条观测时所需的似然和空配风险。表 2 时间只用于原任务比较。
- **UN**　现有原文没有可逐行核对的推断数据管道。正文描述的是预生成未来预测，RNN 的训练数据、测试时实际输入和批处理边界仍待用资产核实。当前严格 MTAD 输入缺 ENC、独立 AIS 属性和在线速航口径，未找到已核作者复现资产。

## S-ON111 · DI-MTP，IEEE T-ITS 2026
**定位**　Zhang 等，*Unified Multimodal Vessel Trajectory Prediction With Explainable Navigation Intention*，27(1)，258–269。2025 年 11 月作者稿，2026 年 1 月卷期。读 §III-B、§IV、§V-B–D 表 II 和图 3。 [出版 DOI](https://doi.org/10.1109/TITS.2025.3635392) · [作者全文](https://arxiv.org/html/2511.14265) · [作者代码](https://github.com/EurusC/DI-MTP)

- **SC**　以历史航迹构造持续意图树，以 CVAE 与非局部注意力产生临时意图并协调交互。
- **DE**　从已按 AIS 身份连好的轨迹切分，过滤短片段（§III-B 示例阈值为 20 点），正文描述三次样条重采样至 30 秒格点，常用 6 步历史和 12 步未来，每个时刻生成 50 条。表 II 海南 GRU-CVAE 65.37/94.33 m，DI-MTP 42.87/69.07 m。§V-C 实际从多条中选择 ADE+FDE 最小的共同索引。图 3 的短历史结果覆盖 2–10 个等间隔采样点，没有单个不规则位置的结果。
- **AI**　只借鉴训练阶段抽取位置轨迹的运动原型，连续时钟对齐和首报的表示能力需重新建立。对已到历史以外的样条节点不得进入推断。作为运动模式路线，原型与普通混合头需同输入、同训练量比较。
- **UN**　作者公开示例不提供全量数据。代码先丢不足 10 点的片段，30 秒格点经 pandas 时间插值，与正文示例阈值和三次样条描述不同。示例随机切分会遇批，正式表对应的预处理、空间或身份切分和原型泄漏边界仍未核清。未执行代码。该论文不评价跨源身份或 1 Hz 发布。 [示例过滤](https://github.com/EurusC/DI-MTP/blob/e5b230bf1e9a09b1c8dacd6424c90f6d5a6f1891/data_preprocess.py#L43-L67) · [示例插值](https://github.com/EurusC/DI-MTP/blob/e5b230bf1e9a09b1c8dacd6424c90f6d5a6f1891/data_utils.py#L56-L65)

- **DE／UN，示例预测权限**　公开流程对选中的整个会遇段计算并保存 mask。`encounter.py` 遍历段内全部共同索引，用 SOG/COG 检查相遇，`predict` 实际读取该 mask。未看到这一路径把 mask 限于当前观测前缀。该默认示例欠缺严格在线权限，正式表的运行管道是否相同仍未知。原型训练脚本把新拟合 KMeans 限于 `traj_train`，可加载的 AE 权重来源仍需核。 [mask 构造](https://github.com/EurusC/DI-MTP/blob/e5b230bf1e9a09b1c8dacd6424c90f6d5a6f1891/encounter.py#L90-L111) · [推断读取](https://github.com/EurusC/DI-MTP/blob/e5b230bf1e9a09b1c8dacd6424c90f6d5a6f1891/model/model.py#L242-L265) · [原型训练](https://github.com/EurusC/DI-MTP/blob/e5b230bf1e9a09b1c8dacd6424c90f6d5a6f1891/train_route_extract.py#L144-L168)

## 近邻回读 · S-ON21，IEEE T-ITS 2026

Lu 等 *Graph Learning-Driven Multi-Vessel Association* 已入库，此次只针对输入权限回读。§III–IV 从 AIS 航向/速度/类型等和 CCTV 检测、画面地标取得对齐及两模态图，通过图内和跨图几何一致性求局部匹配。§V 是交通密集水域的 AIS–CCTV 场景，已有身份或关联质量原表不能转作开放人口逐秒对照。MTAD 有跨源相对偏差但当前口径缺图像和地标，关联头可作近邻，原系统输入保持作者口径。真实到达、可逆修订、可观测空配先验和作者资产覆盖仍待核。 [正式刊物记录](https://ira.lib.polyu.edu.hk/handle/10397/119909) · [作者全文](https://arxiv.org/html/2504.09197)

## S-ON112 Kim 等，GRAE-3DMOT，CVPR 2025

C-ON30 定向补读，独立于上面的 12 篇。**SC** 作者提出几何关系编码，把检测内部的空间关系和轨迹—检测时空关系转换为关联分数。**DE** nuScenes 的 CenterPoint 设置中，补充材料表 S-1 固定同一较宽的检测关系范围，从绝对边表示改为几何和特征的相对差，AMOTA .725→.737、AMOTP .494→.488、ID switches 277→150。表 S-4 中加入轨迹特征，换手 193→150，同时 FRAG 264→315。两个身份指标异向。**AI** 固定测量条件看配对相对表示及长错链，比只看预测点误差更贴近跨源关联。**UN** 原系统用检测框、朝向、尺寸及点云检测器，作者公开仓为 beta，二维异步位置适配与空配能力未核。 [会议正文](https://openaccess.thecvf.com/content/CVPR2025/html/Kim_GRAE-3DMOT_Geometry_Relation-Aware_Encoder_for_Online_3D_Multi-Object_Tracking_CVPR_2025_paper.html) · [补充表 S-1 与 S-4](https://openaccess.thecvf.com/content/CVPR2025/supplemental/Kim_GRAE-3DMOT_Geometry_Relation-Aware_CVPR_2025_supplemental.pdf)

**DE 补充** 作者仓 `63def8b` 对同身份边设 1 并用 focal loss 训练。预测依次对高、低检测置信组用带 `cost_limit` 的部分指派，两组的分数门限不同，未配量测再按检测置信管理出生。该代码可作为学习边分数的参照，空配门限仍为手设。未运行作者代码。 [作者推断代码](https://github.com/altkddhfcjs/GRAE-3DMOT/blob/63def8bde5e199a4e77fdf4fab76a4b3511fe132/trainer/predictor.py#L291-L350)

C-ON30 复核 S-ON108 NEMOT 表 III、VI。单独增强更新的 AMOTA 76.7 与单独增强运动的 76.6 来自相同检测，联合为 77.2。单独假警强度、单独配对亲和和联合更新分别 75.9、76.4、76.7。其假警强度描述检测是否属杂波，MTAD 真目标的暂时无对侧属于另一事件。S-ON102 LA-MOTR 表 4 的相对空间消融各自重训，显示学习关联的可能性，同时含检测协同。S-ON51 MOTIP 表 4 在自注意和数据增强固定时，有／无 Hungarian 的 HOTA 同为 62.2，AssA 51.8／51.5，模型有独立新生 token。视频新生与 MTAD 门外、未见和单源持续须按各自到达权限定义。 [NEMOT 消融](https://arxiv.org/html/2506.18124v3#S7.SS2) · [LA-MOTR 原文](https://openaccess.thecvf.com/content/ICCV2025/papers/Wang_LA-MOTR_End-to-End_Multi-Object_Tracking_by_Learnable_Association_ICCV_2025_paper.pdf) · [MOTIP 原文](https://arxiv.org/html/2403.16848v2#S3.SS4)
