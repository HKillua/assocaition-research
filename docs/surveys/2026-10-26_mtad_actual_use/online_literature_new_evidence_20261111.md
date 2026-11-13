# 在线关联何时值得等待

`ANALYSIS_PACKAGE` v1.0，`AP-ONLINE-NEW-EVIDENCE-20261111`，2026-11-11，partial。纳入本轮用于解释首报错配、候选缺席、确认等待和拒配的来源。只核所列正文、实验及对照，SC 为作者主张，DE 为直接证据，AI 为项目推断，UN 为待证。下游 [Mode C v7](online_causal_replay_mode_c_20261111.md#v7-候选扩展与新报文证据)。

### S-ON57 Vaquero 等，BUSCA，ECCV 2024

读正式版 §3–4、图 3–4、表 2。DE 对失跟轨用已有历史、运动及邻近检测生成候选，用决策 Transformer 选候选，也能选当前候选不适合或已有轨疑为虚假。MOT17 val 用去掉离线插值和逐序列阈值的 ByteTrack，基线 FP/FN 为 3410/9120。只用虚假轨 token 的 FP 增 1501，完整配置 FP 增 479、FN 降 794，HOTA 67.4→67.6。SC 作者报告因果补跟可保持部分遮挡目标。AI 局部身份继续和跨源身份确认可各自决策，减少漏跟可能带来额外假轨。UN 光学外观缺失后，位置是否仍能证实持续身份。 [会议原文](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/09351.pdf)

### S-ON58 Herrmann 等，海岸雷达混合 TBD，2025 预印本

读作者 v1 §IV-A/C、图 6–9、表 III–IV。DE 2025-03-21 特隆赫姆实采 250 幅 X 波段雷达图，2.5 秒一扫，两船有独立 GNSS，其它用 AIS。低信噪对照中 TBD 组件对弱船 Pioner 首次给出持续航迹在第 99 扫，较持续的 JIPDA 对照在第 151 扫，约 130 秒差。低门 JIPDA 第 110 扫的短轨不可作持续确认。表 IV 的整条混合链平均计算 1.06 秒／扫，低门 JIPDA .28 秒／扫。表 III 总 GOSPA 混合 550.86、低门 621.11、高门 606.51，正文次序与表有一处差异，取表。混合有两条误轨各持续两扫，约第 100 扫的定位误差并非全面改善。SC 作者归因于保留弱回波及分段融合。AI 新的原始回波与等待积累共同改变证据，不能归因给单独增加等待。UN MTAD 无全幅回波，实测参考也缺少一部分真实目标。 [作者原文](https://arxiv.org/html/2508.16169v1)

### S-ON59 Xia 等，多扫描轨迹 PMBM，JAIF 2019

读 arXiv v2 2020，§7.3 表 I/图 4。DE 多扫描数据关联和固定滞后平滑在仿真中单列。轨迹 PMBM 的 RMS LP 轨迹误差在平滑前后为 141.91／128.25，当前 GOSPA 同为 150.02，换配分量同为 9.68，耗时 4.41／4.61 秒。SC 作者讨论联合轨迹估计与平滑。AI 报告历史拟合变好不能代替记录首次跨源决策或身份改善。UN 稀疏航迹关联及实际发布。 [作者原文](https://arxiv.org/pdf/1912.01748)

### S-ON60 Draves 等，异步航迹假设分布式融合，2026 预印本

读 v1 §§III-F/G、IV-B、V、图 5–6。DE 卫星量测模拟中组合局部航迹、逐次选择和剪枝。作者以场景末尾最佳假设的历史评价多假设，以单帧结果评价 GNN。最佳假设吸收不足 80% 的源航迹，早期歧义使一个目标后段失去双视角，发生漂移。SC 作者报告保留轨迹的较高关联纯度并承认协议差异。AI 只评已保留轨及末版历史会漏掉等待、剪枝和首次错误，关联纯度和状态可辨识性也可能反向。UN 海事实测、同发布版本的比较、迟到乱序；原文 §III-G 指出当前滤波路径不处理 OOSM。 [预印本原文](https://arxiv.org/html/2610.20290v1)

### S-ON61 Sarlin 等，SuperGlue，CVPR 2020

读会议版 §3.2 式 8–10、§5.4 表 4。DE 双侧添加可重复使用的空配节点，用有边际约束的最优运输学部分匹配。室内同 SuperPoint 特征，最近邻互选→无图网络的最优匹配层，精度 50.4→66.0%，匹配得分 18.8→17.2%；完整版为 84.4% 和 31.5%。SC 作者主张用场景上下文及可拒配约束。AI 只比较精度会忽略接受量，一对一空配应先核 MTAD 有多少同刻争用和真正重复片段。UN 图像深度、姿态生成的监督与项目航迹语义等价性。 [会议原文](https://conferences.computer.org/cvpr/pdfs/CVPR2020-1XMljIyuXWg2zC9bnL19Tw/716800e937/716800e937.pdf)

### S-ON62 Neira 与 Tardós，联合相容性检验，IEEE TRA 2001

读正式版 §§II–IV、图 3–6。DE 同时检验一组地标创新及其相关性。60 m 机器人走廊回访，在简单情形近邻与联合分支定界接近，额外注入杂波或提高位置误差时近邻失效而联合约束更稳。SC 作者将效果归因于跨地标联合相容性。AI 海事联合排序需要先查真实争用和共模误差，静态地标、已知协方差及同步观测均不同。UN 当前报告不含后验协方差，未证二部容量约束普遍成立。 [正式 PDF](https://www.cs.cmu.edu/~motionplanning/papers/sbp_papers/n/00976019.pdf)

### S-ON63 Wojke 等，Deep SORT，ICIP 2017

读作者稿 §2.3、算法 1、§3 表 2。DE 按最近一次观测年龄依序关联，以防高不确定旧轨用标准化残差抢占观测。MOT16 的 SORT 与整套 Deep SORT 相比，ID 切换 1423→781，FP 8698→12852，碎片 1835→2008。SC 作者解释匹配级联及外观补救。AI 旧候选的状态寿命和身份检索寿命可以不同，需要独立评价。UN 年龄规则单独效应、无外观海事输入。 [作者稿](https://arxiv.org/pdf/1703.07402)

### S-ON64 Pastor 等，顺序航迹片段确认，CEAS Space Journal 2023

读正式版 §§2–3。DE 到达时拓展／剪枝，至少四段才做高精重算与确认。两周单雷达模拟 75184 段，3953 个至少四段的目标中 3876 个检出，77 个漏检，其中 38 个恰有四段，另有 17 个典型低轨目标的报告间隔过长。过滤大幅降低复杂度，同时把首个确认从暴力搜索的第 2234 段推迟到 4453 段。SC 作者讨论过滤和确认条件的资源取舍。AI 硬性积累条数对稀疏目标不公平，继续等待要量化每次报告是否有增量。UN 海事现场和真实网络。 [正式原文](https://link.springer.com/article/10.1007/s12567-022-00441-4)

### S-ON65 Hem 与 Brekke，AIS／雷达 JIPDA 的处理时机，JAIF 2022

读正式版 §§VI、VIII-B/C、算法 1–3、图 4–7。DE 同一框架可逐条处理 AIS，也可收集到下一雷达扫描批处理。100 组仿真中三种 AIS 处理表现接近，实测只比较逐条更新、纯雷达与 BP-PF，使用 S-ON44 同一 Autosea 海试的不同片段。AIS 去掉用于参考的事先插值，部分船报频偏高，一艘仅报一次且成功关联。另一段偏移与 AIS 短缺叠加发生 BP-PF 断轨，增加运动适配也可能产生假轨。SC 作者称三种 AIS 处理相对纯雷达有收益。AI 海事证据支持处理时机独立比较，现有现场数据不能判定等待一定胜出。UN 匿名航迹、真实发布时间和同覆盖持续 ID。 [正式目录](https://isif.org/media/variations-joint-integrated-data-association-radar-and-target-provided-measurements) · [机构全文](https://ntnuopen.ntnu.no/ntnu-xmlui/bitstream/handle/11250/3059989/Variations-of-joint-integrated-data-association-with-radar-and-target-provided%2Bmeasurements.pdf?sequence=1)

### S-ON66 Herrmann 等，目标存在概率管理，IEEE TAES

读作者 v2 §IV-C、§V-A/B、图 5–6、表 II，正式 DOI 10.1109/TAES.2025.3624188。DE 在已给出生位置的 100 次仿真上用同一雷达 TBD 结构，对比显式存在概率与 SNR 阈值管理。Swerling 0 总 RMS GOSPA .67 对 .91，虚警分量 .40 对 .60，漏失 .03 对 .36；Swerling I 总 1.03 对 1.76、虚警 .57 对 1.47，漏失反而 .57 对 .55。SC 作者将部分持续误轨归于时间相关的强度先验。AI 生命周期证据和关联置信分别报告，避免用无报直接推不存在。UN 海事匿名片段、已给出生位置之外的影响、真实传输和时钟。此仿真不为 S-ON58 增加独立现场样本。 [作者全文](https://arxiv.org/html/2504.20526v2) · [正式 DOI](https://doi.org/10.1109/TAES.2025.3624188)

检索覆盖 `track confirmation false alarm`、`asynchronous sensor track hypotheses`、`near-online fixed lag data association`、`partial assignment dustbin`、`maritime radar track-before-detect`，对照前轮在线来源。另筛到 Wang 等 Signal Processing 2025 的多帧回波方法，出版页仅可取摘要及引言，输入需雷达回波，暂未纳入直接数值证据。 [原刊](https://www.sciencedirect.com/science/article/pii/S0165168425001483)
