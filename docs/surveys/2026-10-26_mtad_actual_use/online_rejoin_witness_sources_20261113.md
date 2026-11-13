# 纯传感器关联中的反向验证与排除证据

2026-11-13。问题是单报使假候选相对更差时，已到历史可否独立于该报的坐标给出同向排除。补读2025–2026雷达跟踪和多假设原文。DE为直接证据，SC为作者主张，AI为项目推断，UN为未知。

|来源与阅读范围|DE与SC|AI与UN|
|---|---|---|
|E-ON248，既有Kropfreiter、Williams、Meyer，IEEE TSP 2026，作者稿 §§IV、VII-C、VIII|在雷达／声纳数据单元上显式分配观测贡献并用置信传播处理竞争。其模型假定每对象最多贡献一个单元、每单元最多一个对象，十条相交轨迹的主要实验为合成。|支持按报告来源标记哪份数据进入似然。MTAD 没有回波单元，不能从无报推出物理漏检，也不能将同一报告当两个独立票。 [作者全文](https://arxiv.org/html/2504.16814) · [机构记录](https://repositum.tuwien.at/handle/20.500.12708/230580)|
|E-ON249，Remote Sensing 2025，*A Track Segment Association Method Based on Heuristic Optimization Algorithm and Multistage Discrimination*，全文 §§2–4|渤海高频地波雷达，约1帧／分钟。新旧片段正反分配、寻找公共状态，遮断期可不用可能错误的点。使用完整候选片段作分段连接。|正反两个读出若共享原点，不能当统计独立。可借鉴不吃可疑点的反向证据，对已到端点逐一限权。原采样及片段任务与 MTAD 当批不同。 [原文](https://www.mdpi.com/2072-4292/17/3/500)|
|E-ON250，Remote Sensing 2025，*Adaptive Multi-Radar Anti-Bias Track Association*，全文 §§2.2–2.3、4.4–4.6|利用局部拓扑特征抑制系统偏差，近方位、小角度近似；包含模拟漏检和定位扰动的对照。|参考以位移抵消常值坐标偏差。邻轨拓扑与本轮不同报文验证不是同一信息，既有 C39 已检同源邻轨。 [原文](https://www.mdpi.com/2072-4292/17/11/1876)|
|E-ON251，Ospel 与 Mikus，IEEE TSP 2026，全文 §§II-B/C、III-A4/B2|按传播时差约束候选组，每个检测最多入一个所选组；式39、42优先多独立传感器支撑。六传感器声学实测经人为错时构成重叠，有些组合定位仍好、分组已错。|观测覆盖应和分差分开，缺一个对侧不能当作排除。不同传感器与已知传播时间为原协议条件。 [作者全文](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/ea048f24-3eee-4792-b959-82968bec8bc5/content) · [期刊](https://doi.org/10.1109/TSP.2026.3685137)|
|E-ON252，Zhang、Ge、Wu，Scientific Reports 2025年末上线，全文 Ghost peaks mitigation、式17–19/23–28|被动雷达历史帧可保留同一泄漏形成的假峰，另由距离–Doppler和可见条件排除；相近等Doppler仍难。测得FM参考上合成目标回波及多径。|跨时一致也可重复同一误差。MTAD 无回波及可见性，只能核当前报文不复用，不能推独立物理证据。 [出版方全文](https://www.nature.com/articles/s41598-025-34316-5_reference.pdf)|
|既有 E-ON160，Goodman 等，IEEE TAES 2025 §§II、III；既有 E-ON232–247 原窗证据|前者的附加RF证据经条件独立模型组合，后者分别定位单报复用、缓存以及真边变远的相对排序。|MTAD 的早期原始位置可以隔离当前报文，但上游共同轨迹、配准及早报仍可相关。历史排除读出只代表该已到观测下的相对残差变化。 [论文](https://doi.org/10.1109/TAES.2025.3540829) · [几何增量诊断](../../reports/2026-11-13-online-rejoin-geometry.md)|

沿同一四端组，在报告者的上一原生点时刻和之前固定20秒构造同一三端读出。两条对侧轨均须已有比上一原生点更新的严格批前括点才称新对侧见证。实报当前坐标、KF预测状态和标签均不输入历史读出。只讨论固定候选和已到相对残差，不推物理定位或独立概率。 [Mode C v60](online_causal_replay_mode_c_20261111.md#v60-对侧历史与单报排除)
