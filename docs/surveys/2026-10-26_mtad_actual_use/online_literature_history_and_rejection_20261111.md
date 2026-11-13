# 在线历史片段检索与无历史拒配的原文依据

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-HISTORY-AND-REJECTION-20261111`，2026-11-11，partial。各条按实际核读版本和章节定位。SC 为作者主张，DE 为直接证据，AI 为面向 MTAD 的推断，UN 为未知。第一阶段先核超龄真候选，第二阶段再用无对侧历史的结果。下游为在线 Mode C。

## 超龄历史与状态有效期

### S-ON67 Ahmed、Jun、Ding，AIS 时空关联，IEEE TITS

读 arXiv v2 §§II、IV-A/B、V-B/D，表 I/VII/VIII 及复现说明 pp.1–2。DE 海岸警卫队 AIS 去船 ID，并对部分测试人工挖空；在线先按位置、速航预测与选轨，随后以超龄端点、距离和空间区先验合并。缺报测试 4/5 的完整流程连续性／平均完整性为 .99/.88 与 1.00/.92，GNN 为 .62/.49 与 .78/.49。开放 AIS 前 25000 点、186 船的完整流程仍报告 27 条合并、23 条断轨。作者复现说明显示主要表格从事后合并产物生成。SC 事后合并补在线外推失准后的断轨。AI 历史 ID 记忆与当前位置新鲜度应分开；利用末端和空间先验的结果不能解释首报当时的准确性。UN 匿名双源、原生成速航不可用、旧状态资格与错并风险。 [作者原文](https://arxiv.org/html/2010.15921) · [作者代码及数据](https://doi.org/10.5281/zenodo.6862930) · [复现说明](https://zenodo.org/api/records/6862930/files/J87_Reproducibility_Report.pdf/content)

### S-ON68 Lee 等，LOMM，ICCV 2025

读会议版 §§3–5，表 3–4。DE 保留每个身份的最新视觉特征及占用状态，先维护已有对象、再安排新对象。YouTube-VIS 2022／ResNet-50，表 3 在 DVIS 从无额外记忆的 33.9 AP 到 LOM 39.2，加入解耦关联的完整模型 41.1；仅当前或仅过去锚分别 39.3、39.2，融合锚 41.1。表 4 相对 DVIS 的报告计算时间 91.26→101.16 ms。SC 最新可用特征比一律混合历史更有利。AI 可以保留识别线索，同时拒绝把旧位置直接当当前状态。UN 只有稀疏位置的 MTAD 对应方式，米制老化和真实到达。 [会议原文](https://www.openaccess.thecvf.com/content/ICCV2025/papers/Lee_LOMM_Latest_Object_Memory_Management_for_Temporally_Consistent_Video_Instance_ICCV_2025_paper.pdf)

### S-ON69 Zhang 等，ByteTrack，ECCV 2022

定向读会议版 §§3、4.1–4.2、表 1–2、图 4，补核原先只作对照的 lost 生命周期。DE 失跟身份保留 30 帧用于再匹配，期间不输出该框与 ID。MOT17 验证同为第一层 IoU，第二层 Re-ID 与 IoU 的 ID 切换 231/159；BDD100K 上两层 Re-ID IDF1 53.4，第一层 Re-ID、第二层 IoU 为 54.8。作者在 BDD100K 不用原 Kalman 路径。SC 低置信检测仍可为重接提供证据。AI 运动先验、重接时可用观测与保留寿命分开试；30 帧参数及其收益不能转给 10/20 秒航迹。UN 保留寿命的独立消融，超龄经纬的预测误差。 [会议原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136820001.pdf)

### S-ON70 渤海高频雷达片段关联，Remote Sensing 2025

读正式版 §§2–3、表 3–4。DE 多阶段粗门、双向片段代价及全局启发式匹配，渤海 107 片段、58 个可连接，49 TP/7 FP/9 FN，IGS 38/16/20，模糊法 35/17/23。超长中断可能使真对在粗门先被排除。§3.2.2 图 11–12 的 77 号旧段本应连 53，方法仍错连 80。SC 组合门和优化提高匹配质量。AI 先拆年龄可达、空间入门、与当前假近邻及新增假近邻竞争。UN 双向完整片段需要新片段后续行，首报当时同等输入与效果。 [正式原文](https://www.mdpi.com/2072-4292/17/3/500)

### S-ON71 Gao 与 Wang，MeMOTR，ICCV 2023

读作者原文 §3.4、§4.6、表 6–7，静态核固定提交的轨迹寿命。DE DanceTrack 无两组件时 AssA/IDF1 52.1/64.1，单加记忆 52.9/64.7，单加注意力 50.7/62.4，两组件 55.0/67.1。更新率 .02 比 .01 的 ID 切换少（1213 对 1237），AssA 却低（53.5 对 55.0）。代码在低置信时保留活动身份的历史，连续漏检达到容限即删身份。SC 依靠长期记忆区分活动对象。AI 特征历史跨度与轨迹删除后的检索能力是两个条件。UN 删除后重接和位置输入迁移。 [作者原文](https://arxiv.org/html/2307.15700) · [固定提交的生命周期实现](https://github.com/MCG-NJU/MeMOTR/blob/eb7a177b9cbcb89742ec69b2545ab3af2ea31a80/models/runtime_tracker.py#L43-L55)

## 无对侧历史时的可匹配性与拒配

### S-ON72 Lindenberger 等，LightGlue，ICCV 2023

读作者版 §3.2 式 5–7、§5 表 4/图 6。DE 学习逐特征可匹配性，另计算候选两两相似度，再联合决定对应。在合成单应实验中，去可匹配性→完整配置，精度 67.4→86.8%，召回 97.0→96.3%，计算 18.9→19.4 ms。SC 可匹配性与具体对应分别建模。AI 固定几何首选，单独验证可观察的对侧活动是否能帮助接收决策。UN 图像对应监督与匿名船舶局部报告活动并不等价，未证明报告少就是无对应。 [会议目录](https://openaccess.thecvf.com/content/ICCV2023/html/Lindenberger_LightGlue_Local_Feature_Matching_at_Light_Speed_ICCV_2023_paper.html) · [作者原文](https://arxiv.org/html/2306.13643)

### S-ON73 Possegger 等，在线遮挡地测距离，CVPR 2014

读会议原文 §3.2–3.4 式 3–5、图 3、表 2。DE 用地面与相机标定、投影框、静态遮挡及检测可靠性在特定情景下解释漏检。Town Centre 整体对照相对在线 Wu，MOTA 69.5→70.7，身份切换 209→157，MOTP 68.7→68.6。SC 可见性模型可维持被遮挡身份。AI 有独立覆盖或几何锚才可把缺报解释为预期漏检，MTAD 的报告活动只能当代理。UN 这些组件的独立消融、无物理视场时的可靠性。 [会议目录](https://www.cv-foundation.org/openaccess/content_cvpr_2014/html/Possegger_Occlusion_Geodesics_for_2014_CVPR_paper.html) · [会议原文镜像](https://citeseerx.ist.psu.edu/document?doi=ec77855438dc6a181f7762e32c7b0101520b10f0&repid=rep1&type=pdf)

### S-ON74 Vaze 等，开集识别难度，ICLR 2022

读作者稿 §§4–5，表 3。DE 固定 1000 个未知类的 ImageNet 易→难协议，最大 logit 的开集 AUROC 78.2→72.6，ARPL+ 79.0→73.6。单加随机未知类别的影响远小于语义相近。SC 难未知样本应与容易的域外样本分开评价。AI 28 个本来能过 4 km 门的缺历史错配属于几何有迷惑性的子域，不能用空门事件拉高拒配分数。UN 海事轨迹类别、开集分布和部署阈值。 [作者原文](https://www.robots.ox.ac.uk/~vedaldi/assets/pubs/vaze22open-set.pdf)

### S-ON75 Jones 等，选择分类的组间可靠性，ICLR 2021

读作者稿 §4 图 2、§7 图 5。DE 五个基准里总体条件准确率随覆盖降低而提高，CelebA 最弱组下降，Waterbirds、CheXpert、CivilComments 的最弱组方向混合。MultiNLI 总覆盖 50% 时最弱组 65→75%，次弱组 77→95%。极低覆盖估计波动大。SC 分组下收益不由总体决定。AI 分场和有实际支持的报告源分别给接收量、保正确和拒错误，稀疏组不能当零风险。UN 三开发场以外的稳定性、分组构造。 [作者原文](https://arxiv.org/pdf/2010.14134)

### S-ON76 Traub 等，选择性分类风险评价，NeurIPS 2024

读会议原文 §§2–4 式 3/6、图 1/3。DE 区分接收条件错误率和全体错误接收率。原研究以 AUGRC 替换 AURC 时，6 个同分布基准中 5 个的前三方法改变，500 次 bootstrap 下仍可看到排序差异。SC 指标的分母与下游应用条件要一致。AI 本项目须并报全体错接、接收内错接、正确损失和目标错配拒掉数。UN 真实海事错误成本与数据分布外保证。 [会议原文](https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf)

检索覆盖 `online tracklet reactivation identity memory`、`maritime AIS gap track association`、`local feature matchability`、`open set recognition hard near neighbor`、`selective risk group coverage` 和 `occlusion detector reliability`。同一作者报告的长记忆与具体活动轨迹寿命分别读。未把只有书目的 TITS 生成式片段匹配当作原文证据。已核版本未进行复现。
