# 在线观测基线重启审计

2026-11-14。依据飞书《视频文案》第一章和第三章、仓库 `AGENTS.md`、用户指定的 `research-workflow` 及[项目科研流程](../research_workflow.md)，从复现论文和确立多基线的步骤倒查。飞书把复现论文放在组合探索和深挖现象之前，建议优先核近两年高引、代码与后续改造线索。项目还要求每次实验事前记录来源分析、Mode C、Idea 和可比性判据。[飞书第一章](https://my.feishu.cn/wiki/OHs3w9meHiQ3OXk4XC7ctFPXnxd#Wq7gdDT11otUQsx36z6co1qhnjb) · [飞书第三章](https://my.feishu.cn/wiki/OHs3w9meHiQ3OXk4XC7ctFPXnxd#QxYsdMheSoUZfGxPbYecO8Din7b)

| 可核时间 | 证据与判断 |
|---|---|
| 11-10 | [来源与回放审查](2026-11-10-online-source-and-replay-review.md)已发现候选的输入或复现条件缺口。记录中的回放是工程验证，尚无多套同行整链实测。 |
| **11-11** | **最早能确认的偏差。** [事前方案](../proposals/online_reselection_20261111.md)固定了局部问题、对照和停止条件。随后三个 MTAD 场景的诊断已执行，[执行记录](2026-11-11-online-field-and-method-review.md#开发诊断-v1)仍为 `source_idea_id=none`，后续 Idea 在诊断之后形成。同期也缺少共同协议下的多套同行基线，局部结果不足以驱动整条路线的选型。 |
| 11-12 | [持续基线选型](2026-11-12-online-continuous-baseline-selection.md)把 CV-KF＋GNN 推为持续系统起点。[四臂实验](2026-11-12-online-continuous-factorial.md)有事前 Idea，但只比较位置保持／CV-KF 与局部／全局指派。原图上的两种指派逐场一致。可保留运动与指派的局部归因，无法据此选定同行主基线。 |
| 11-14 | [同行基线审查](2026-11-14-online-peer-baseline-review.md#多基线名单与标准流程)记录了同口径引用数未核、没有 MTAD 同协议整链结果，仍在研究状态给出优先候选。C-ON24 至 C-ON56 中的局部控制保留各自证据范围，不能外推为完整系统或同延迟同行比较。 |

重启点退回**基线来源筛选**。撤销旧同行优先顺序、KF＋GNN 的默认工作基线地位和从旧候选图继续做诊断的队列。现有实现作为历史回放或模块对照，既有 Mode C、Idea、负结果、数据与回执保留原件。缺失的事前记录按原事实保留。曾发布的研究状态与执行交接见[原状态](https://github.com/HKillua/assocaition-research/blob/5b700f38974908ce46c79aa49a7c5ccbe6408045/docs/research_status.md)和[原交接](https://github.com/HKillua/assocaition-research/blob/5b700f38974908ce46c79aa49a7c5ccbe6408045/HandOver/Handover.md)。

历史暴露随数据保留。既有名单审计记录 440 个已用在线场，其中 437 场在 `T_core`，触及该分区全部 84 个共享 A 组件。原 28 场与原 48 场均有开发暴露。原 3000 场名单之外的 25 场／24 组件仍是元数据线索，尚未核定其完整暴露与独立性。本轮仅核文献、代码静态接口和既有记录。`T_test` 继续封存。[原名单审计](2026-11-14-online-peer-baseline-review.md#共同回放与入表证据)

当前唯一入口是[研究状态](../research_status.md)，本轮新增来源及筛选证据见[基线重新筛选](../surveys/2026-11-14-online-baseline-reselection.md)。
