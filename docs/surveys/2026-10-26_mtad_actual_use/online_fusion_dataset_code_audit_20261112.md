# 在线融合的数据处理与公开实现核验

`ANALYSIS_PACKAGE` v1.0，`AN-ONLINE-FUSION-DATA-CODE-20261112`，2026-11-12，partial。承接用户要求，核外部在线融合如何把记录数据变成在线输入，以及公开代码能迁移到什么层次。SC 为作者主张，DE 为正文、数据说明或静态代码直接证据，AI 为分析推断，UN 为未知。本轮未运行作者算法、下载大数据、训练或产生新 MTAD 成绩。既有来源沿原 ID 补证，不把补读算成新增论文。

## 范围与证据地图

优先纯传感器的真实报告与扫描协议，补充 2025–2026 年视觉/协同感知的异步更新机制。纳入能追到数据入口、时间处理、更新循环或公开条件的来源。以下工程来源不自动具有同行基线资格。

| 来源 | 实际阅读/复核 | 新证据 |
|---|---|---|
| S-ON104 Fusion-Poly，作者仓称 IROS 2026 已接收 | 复用 v2 正文 §§III–IV、表 I–VII 的[原分析](online_literature_recent_2025_2026_20261112.md#s-on104fusion-poly-iros-2026)，本轮核 v1 方法/实验及固定源码的 reader、更新、输出和配置。未独立核正式会议录。 | E-ON119 |
| S-ON131 Larsen & Mathiassen，FUSION 2026 | 作者稿 §§III–V、表 II、官方日程与作者 PR。 | E-ON120，更新 E-ON97 的资产状态 |
| S-ON148 Stone Soup v1.9.1，框架与官方示例 | 双雷达 track fusion、时间合并、预测、Chernoff、航迹 feeder 与 OOS 示例。是工程来源，非新论文。 | E-ON121 |
| S-ON6 DeepSORVF，IEEE TITS 2023 | 复核作者稿 §§III-A/C/D、IV-A/B/C/D，表 III/IV 与 main/AIS/FUS/reader/许可；延续[原来源](online_literature_analysis_20261111.md#s-on6-guo-等deepsorvfieee-tits-2023)。 | E-ON122 |
| S-ON52 Hem 等，IEEE Access 2024／Mariner | 正式版 §§III-E、IV-B、VI-B；作者数据 schema 和文件树。未读二进制记录。 | E-ON123 |
| S-ON22 Gaglione 等，IEEE TSP 2022 | 正式版 §II、VI-C、VII 与同组作者 2024 评论 §I-B。 | 事件处理证据归 E-ON123a |
| S-ON149 Harbour 2026 | README 身份、loader/tracker/CFM/real evaluation、许可树。课程工程，非期刊论文。 | E-ON124 |
| S-ON150 WHUT-MSFVessel，Sensors 2025 | 正文 §3.2.1、作者 GitHub 当前完整树与 README。 | E-ON125 |
| S-ON147 HAXR 2026 v1.1.0 | DLR 数据条目，伴随库 README、utilities 全文、许可。数据来源，未核到同名顶刊算法论文。 | E-ON126 |
| S-ON151 LRCP，WACV 2025 | 补充性局部源码核验 loader、延迟编码、两阶段模型、许可，未完成独立全文分析。 | E-ON127，partial，仅机制线索 |
| S-ON97 CD-PMBM、S-ON146 TM-PMBM，IEEE TSP 2025 | 复用已有正文分析，定向复核作者 MATLAB 的实际输入、扫描/窗口与预测更新。 | E-ON128 |
| S-ON44 VIMMJIPDA，IEEE JOE 2021，2025公开工程 | 复用论文来源，本轮发现并读公开核心代码与仿真包装接口，未运行。发布年份不改写为论文年份。 | E-ON129 |

共同研究问题是：何时有一条新观察，何时只是把旧状态预测到现在；算法实际输出在哪些时刻；“不上报”如何进入存在和关联判断。正文结果用于理解原研究，不能与 MTAD 数值混比。

## E-ON119：Fusion-Poly 的内部更新与公开输出

版本 `cfca8596b0bfa99fd318a21fae690bc9dff90ef2`，[作者仓](https://github.com/K544-AD/Fusion-Poly/tree/cfca8596b0bfa99fd318a21fae690bc9dff90ef2)；[论文 v2](https://arxiv.org/html/2603.08199v2)。

**原问题和机制。** SC 异频弱观测能在共同扫描之间维持目标。DE 同步时混合、纯 3D、纯 2D 分级关联，中间相机帧续已有轨；位置预测、存在分数和生命周期是不同状态。作者验证表 III 同检测器完整方案 2→4 Hz，AMOTA 76.9→77.1、IDS 446→416，同时 FN 15,894→15,974。只加密输入的实验也有退化，不能把更多更新等同更完整检测。原文未给 MTAD 首报/未见真对侧错接/确认等待，不确定性未给跨场区间。

**实际数据与循环。** `test.py` L18–22、`dataloader/nusc_loader.py` L27–33 读预生成检测 JSON 与 nuScenes。`data/script/detect2d.py` L92–145 利用前后关键帧时间选择最靠中点的真实图像，`concat_2d_detection.py` L119–141 插入回放。此为事先构造采样协议，未发现取未来检测内容修正当前状态。[选帧](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/data/script/detect2d.py#L92)

- loader L113–119 的 `timestamp` 实赋 `item`，KF L31–44 从配置取固定 Δt，高频配置 L56–61 为 0.25 秒。真实相机 token 用来取标定和姿态，不能由此宣称任意原生 Δt 的预测。[loader](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/dataloader/nusc_loader.py#L113) · [KF](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/motion_module/kalman_filter.py#L31)
- `nusc_tracker.py` L217–278 只让混合/3D-only 未匹配检测出生，2D-only 续已有轨。各类 `min_hit=1`，合格 3D 轨可立即 active。这与 MTAD 两源都给位置的对称性不同。[出生与更新](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/tracking/nusc_tracker.py#L217)
- `async_2d_motion_update` L193–218 虽计算观测和增益，随后无条件恢复 state/P。因此该 SHA 的异步相机匹配影响存在分数、命中和生命周期，不能写成已经实现有效的异步运动校正。[恢复操作](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/motion_module/kalman_filter.py#L193) · [异步评分](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/tracking/nusc_score_manage.py#L108)
- `test.py` L54–59 跳过非关键帧输出，内部约 4 Hz 输入只在 2 Hz 关键帧写评价结果。不是持续发布全部中间结果。[输出条件](https://github.com/K544-AD/Fusion-Poly/blob/cfca8596b0bfa99fd318a21fae690bc9dff90ef2/test.py#L54)

**复现和迁移。** Python 3.7 及检测器依赖；入口 L6 无条件导入 `auto_finetune_module`，固定完整树未见该文件；未见 LICENSE。此为静态运行与授权材料缺项，未执行不能宣称必然运行失败。AI 可借鉴单源保留、存在/身份/位置证据分工；图像 IoU、标定、检测分、出生非对称和固定 Δt 须重建条件。UN 代码与作者表格的精确运行版本、校准与成绩复现。状态为机制来源，尚非可直接运行的 MTAD 作者基线。

## E-ON120：DetectorContext 作者机制已公开，完整海试复现仍缺

[论文](https://arxiv.org/html/2603.15137v1)，[FUSION 官方议程 #315](https://www.ntnu.edu/fusion2026/thursday)。论文真实两场海事雷达 0.8 Hz／LiDAR 10 Hz，按原生扫描处理，统一在雷达时刻评价。问题是覆盖外的高频空扫错误地削弱低频源维持的真轨。状态相关检测率和量测相关杂波只在一次已知扫描中进入似然。表 II 与消融结果保留在 [S-ON131/E-ON97 原分析](online_sensor_association_sources_20261112.md)。这支持观测机会建模，未验证匿名轨迹两源首报的拒配。

作者 martinvl 于 2026-06-23 提交官方 [PR #1291](https://github.com/dstl/Stone-Soup/pull/1291)，本次查询 open、未合并。head `53879cb5fd38dac084e89132a3f801aa5bf6cc97`。9 个改动文件包含接口、GM-PHD 路径、测试与教程，未包含 USV 数据、真实 reader、两场配置和完整表 II 复现。教程是一维、6 个规则秒步。作者说明 feeder context 保留、PDA/JPDA、粒子路径待后续。

`types/detector_context.py` L9–37 提供两个查询函数，`tracker/pointprocess.py` L78–93 传递 context；L34–37 的 callable 检测率直接返回 float，标量路径转换 Probability。官方 review 指出对数域语义和概率检查不同，该 SHA 尚存在，若采用必须先核该问题。[接口](https://github.com/martinvl/Stone-Soup/blob/53879cb5fd38dac084e89132a3f801aa5bf6cc97/stonesoup/types/detector_context.py#L9) · [传递](https://github.com/martinvl/Stone-Soup/blob/53879cb5fd38dac084e89132a3f801aa5bf6cc97/stonesoup/tracker/pointprocess.py#L78) · [教程](https://github.com/martinvl/Stone-Soup/blob/53879cb5fd38dac084e89132a3f801aa5bf6cc97/docs/tutorials/filters/DetectorContextTutorial.py#L40)

**资产判断更新。** 不能沿用“没有公开实现”，也不能说“完整论文可以复现”。框架 MIT，论文真实数据许可/入口未核到。AI 机制实现可审查，MTAD 缺空扫描、物理覆盖和检测机会，不能用周围有报文替代这些条件，原活动密度代理失败 E-ON42 继续有效。

## E-ON121：Stone Soup 的报告后验融合、相关性与迟到示例

S-ON148 是框架版本，不单计为期刊论文。固定 v1.9.1 `a4336b920a799cfe0a77ecb05867c5deeb371c7a`，[MIT](https://github.com/dstl/Stone-Soup/blob/a4336b920a799cfe0a77ecb05867c5deeb371c7a/LICENSE)。

`Track2Track_Fusion_Example.py` 是 50 步双模拟雷达，本地 JPDA/GM-LCC、集中量测 GM-PHD 与航迹融合 GM-PHD 比较。航迹作为带协方差的检测，ChernoffUpdater 的 CI 权重固定默认 0.5；各模拟时刻每源运行一次，融合器消费两个批次。未知对应通过距离候选与 GM-PHD 处理，元数据 track_id 没有被距离假设当真对应读取。未运行该示例，不报告我方数值。[配置 L434–473](https://github.com/dstl/Stone-Soup/blob/a4336b920a799cfe0a77ecb05867c5deeb371c7a/docs/examples/trackfusion/Track2Track_Fusion_Example.py#L434) · [循环 L583–601](https://github.com/dstl/Stone-Soup/blob/a4336b920a799cfe0a77ecb05867c5deeb371c7a/docs/examples/trackfusion/Track2Track_Fusion_Example.py#L583)

`MultiDataFeeder` L14–25 按输入时间戳 heap merge，要求每流已排序，没有独立接收时钟；`DistanceHypothesiser` L71–94、`KalmanPredictor` L188–204 预测到输入检测时刻。`Tracks2GaussianDetectionFeeder` L17–47 每批取所有 live tracks 最新状态，没有新量测版本去重。相邻局部后验共享历史，CI 为未知相关性保守融合；它没有提供信息谱系或阻止额外旧后验重放。[merge](https://github.com/dstl/Stone-Soup/blob/a4336b920a799cfe0a77ecb05867c5deeb371c7a/stonesoup/feeder/multi.py#L14) · [track feeder](https://github.com/dstl/Stone-Soup/blob/a4336b920a799cfe0a77ecb05867c5deeb371c7a/stonesoup/feeder/track.py#L17)

OOS 示例为已知固定 5 秒迟到、单目标、已知归属，L119–127 把第二源 timestamp 直接设为物理时刻+5 秒，L224–277 手工构造 SingleHypothesis。可学等待/丢弃/直接处理的对照，不能照搬为具备三时钟的多目标迟到基线。[OOS 入口](https://github.com/dstl/Stone-Soup/blob/a4336b920a799cfe0a77ecb05867c5deeb371c7a/docs/examples/oosm/KalmanFilterOOSMExample.py#L119)

AI 可用工程骨架建立本地独立实现或清晰的外部适配对照；MTAD 仍需位置噪声、局部协方差和真实扫描语义。CI 不修复错配与配准偏差。重复后验是源实现风险，不能直接声称当前 MTAD 回放已有此故障。

## E-ON122：DeepSORVF 的已收缓存和确认轮次

固定作者仓 `8e767c9ddd03426cf2c6324b0a8030d4360bc276`，[正文](https://arxiv.org/html/2302.11283)。问题是异步 AIS 与视频的坐标、缺失及遮挡；E-FastDTW×方向惩罚、Hungarian、绑定历史与遮挡补偿。原 26 实录场均 MOFA/IDF1 91.13/95.59%，十段消融 DeepSORVF(w/o)/full MOFA 89.93/96.04、IDF1 94.69/97.98（表 III/IV），不是多次独立试验区间，也没有独立位置融合精度。

`main.py` L64–87 视频帧驱动内部时钟，AIS/FUS 只在秒边界更新与记录；`AIS_utils.py` L296–305 读取当前秒命名 CSV，缺文件返回空表，L204–219 将当秒读入及前秒缺报船按最后 SOG/COG推到当前。L188–201 直接把预测记录 timestamp 改成当前秒。它没有保留独立的“最后真实报文时刻”字段，持续缺报情况下 `AIS_las` 也会递推。[主循环](https://github.com/gy65896/DeepSORVF/blob/8e767c9ddd03426cf2c6324b0a8030d4360bc276/main.py#L64) · [预测](https://github.com/gy65896/DeepSORVF/blob/8e767c9ddd03426cf2c6324b0a8030d4360bc276/utils/AIS_utils.py#L181)

`FUS_utils.py` L222–230 每次成功匹配把计数+1，未检查两端是否各有新真实量测；L151–172 绑定结果优先，L244–246 超过 bin_num 进入绑定。作者稿 §III-D 为 Mat_min=15、T_max=15 秒；当前公开源码 L104–106 为 bin_num=3、fog_num=3，即需严格大于3。源码与论文不是相同确认设置。缓存推算形成的新位置不等于新增独立身份证据。[计数和绑定](https://github.com/gy65896/DeepSORVF/blob/8e767c9ddd03426cf2c6324b0a8030d4360bc276/utils/FUS_utils.py#L195)

复现条件还包括 YOLOX/DeepSORT、外观权重、固定相机标定及数据。README 限非商业研究，而根 License 是 CC0，二者表述冲突，第三方检测器权利另核；本轮不直接搬入代码，也不作法律结论。AI 可迁移异步前缀距离与绑定/解除对照，严格位置 MTAD 不使用原 raw SOG/COG，须记录实测/预测与报告版本。UN 新真实报告计数替代轮次计数对作者任务或 MTAD 的实际效果。

## E-ON123 / E-ON123a：真正海事在线系统怎样组织新报告

**S-ON52 Mariner。** 正式版 §VI-B 为真实 2023-10 雷达+AIS输出到避碰 MPC；§III-E/IV-B 让未收到 AIS 不改变存在权重，雷达空扫另按检出处理。假设目标自报无杂波，不能照搬给 MTAD 匿名源。[正式原文](https://doi.org/10.1109/ACCESS.2024.3389824)

数据仓 `6e1a0bf23f831f778aa9c793d49d9adf6da95814` 只有 README、LICENSE、5个npz，无算法。README L16–29 radar 为扫描列表、AIS为每次到达列表，皆单 UTC，AIS 有 MMSI/速航；L40–54输出按雷达时刻组织，字段表未声明持续 track_id/MMSI，GT按对象的GPS列表。不能由 schema 推出三时钟或持续ID可算。CC BY-NC 4.0。海试与 Ravens 合成AIS、GPS生成AIS的LiDAR例分开。原数值、消融限制复用 S-ON52，不将真实闭环当本轮复现。[公开 schema](https://github.com/autosit/autonomy-field-test-data/blob/6e1a0bf23f831f778aa9c793d49d9adf6da95814/README.md#L16)

**S-ON22 Gaglione。** 正文 §II/Fig1 把雷达两时刻之间新到 AIS 按 RID 分组联合处理；§VI-C另比报告一到即处理。意大利双HFSWR+AIS约7.5小时，雷达步16.64秒。评估对AIS参考的三次插值不进入在线输入，GT只覆盖AIS船。[正文](https://repositum.tuwien.at/bitstream/20.500.12708/150324/4/Gaglione-2022-IEEE%20Transactions%20on%20Signal%20Processing-am.pdf)

同组作者 2024 评论 §I-B 明确当时 BP-PF+AIS 实现未公开，本次未检得更新作者库，不推为永久不存在。评论另给 VIMMJIPDA+AIS 作者代码 DOI 10.24433/CO.4125751.v2，列为另一个来源线索。[评论](https://repositum.tuwien.at/bitstream/20.500.12708/203689/2/Gaglione-2024-Journal%20of%20Advances%20In%20Information%20Fusion-am.pdf)

AI 可研究新报告即时更新与有界合批的精度/延迟代价，不能借用AIS身份、雷达range/bearing/range-rate到匿名位置任务。没有接收时间不能把不等间隔称乱序处理。

## E-ON124 / E-ON125：两条公开海事线索的实际边界

**S-ON149 Harbour**，`d75106fb36629d1a8999775818ca53fdbd8353af`。README L3明确 DTU34763、2026春课程项目，非顶刊作者复现，树无LICENSE、API license=null。`tracker.py` L1179–1232按报告自身时间分组消费，当前快照未见旧AIS换新时钟重复注入。`run_real_data.py` L99–108/174–189/357–363用同一AIS作输入和双侧插值参考，RMSE不能当独立融合精度。`loader.py` L92–103/126–139 自船剔除和 `manager.py` L89–116有全量GNSS两侧插值，严格前缀需重建。[身份](https://github.com/elifpulukcu/harbour-multi-sensor-tracking/blob/d75106fb36629d1a8999775818ca53fdbd8353af/README.md#L3) · [事件循环](https://github.com/elifpulukcu/harbour-multi-sensor-tracking/blob/d75106fb36629d1a8999775818ca53fdbd8353af/src/ekf/tracker.py#L1179) · [评估](https://github.com/elifpulukcu/harbour-multi-sensor-tracking/blob/d75106fb36629d1a8999775818ca53fdbd8353af/examples/run_real_data.py#L174) · [两侧插值](https://github.com/elifpulukcu/harbour-multi-sensor-tracking/blob/d75106fb36629d1a8999775818ca53fdbd8353af/src/real_data/loader.py#L92)

**S-ON150 WHUT-MSFVessel**，Sensors2025 §3.2.1按最后AIS速航推到雷达时刻，可见光取距雷达最近帧，其他帧沿用上次融合。UN 是否允许未来帧、缓冲预算。作者仓 `ac1a403ee37b15a0152110d0d495261089e4cae5` 当前完整树只有README，提供部分研究数据百度盘，无算法或LICENSE，不能登记成开源算法。[正文](https://www.mdpi.com/1424-8220/25/7/2179) · [作者材料](https://github.com/yixiiii/Multi-Source-Fusion-for-Vessels/blob/ac1a403ee37b15a0152110d0d495261089e4cae5/README.md#L1)

## E-ON126：HAXR 给出更真实的扫描边界，也有重叠

S-ON147，DLR HAXR v1.1.0，2026-02-24，数据 DOI10.5281/zenodo.19824555。13个部分重叠X波段雷达，按UTC小时提供HDF5原始反射cells、tod/幅值、滑动旋转索引，匿名AIS的uid在资料内稳定。站位置局部坐标10m取整。AIS本来是同一个流，按各站覆盖过滤并转换后分别提供，不能当作13份独立AIS。[数据说明 §§Radar/AIS](https://zenodo.org/records/19824555)

伴随库 `0f3cdde4598c931841be8ffefed951d1a83cb94b`，`utilities.py` load_cycle取cycle/first:last包含端点，arg_next_frame/iter_frames跳到前一窗结束之后才开始的下一窗。相邻cycle高度重叠，逐cycle当独立新扫描会重复消费cells。API已有不重叠frame迭代，不需另造规则。[源文件](https://github.com/DLR-KN/haxr/blob/0f3cdde4598c931841be8ffefed951d1a83cb94b/src/haxr/utilities.py#L25)

数据页列Copyright，伴随库LGPL3，须区分数据与软件授权。未下载5.4GB原始数据、未做检测和持续ID评估，不能称已形成外部验证集。AI 该资料适合进一步研究真实扫描机会和覆盖；另需提取器、真实接收时钟、独立目标真值，AIS既输入又参考时尤其要分开。

## E-ON127：LRCP 的局部代码补证

S-ON151，WACV2025的协同点云检测来源，补充核作者链接重定向后的 `junjie-wang-dev/LRCP`，`d0a7eec53e95ced27365866921f805270987b605`。loader训练随机历史延迟、测试固定延迟，按帧索引×100ms；meta_flow用历史BEV和延迟编码估偏移，point_pillar_deformable两阶段。原始点云、监督偏移和缓存特征均不在MTAD字段。只支持明确保存年龄和过去特征的接口思想，未完成全文分析，不使用其数值作证据，也不是持续ID基线。[loader](https://github.com/junjie-wang-dev/LRCP/blob/d0a7eec53e95ced27365866921f805270987b605/opencood/data_utils/datasets/basedataset/v2xsim_basedataset.py#L215) · [模型](https://github.com/junjie-wang-dev/LRCP/blob/d0a7eec53e95ced27365866921f805270987b605/opencood/models/meta_flow.py#L167)。仓许可限学术用途且限制转交，不按宽松授权处理。

## E-ON128：2025 TSP 两种概率骨架，输入条件不同

**S-ON97 CD-PMBM。** García-Fernández & Särkkä，*Gaussian Multi-Target Filtering With Target Dynamics Driven by a Stochastic Differential Equation*，IEEE TSP73:664–675，2025，DOI10.1109/TSP.2025.3535556，[作者稿v2](https://arxiv.org/html/2411.19814v2)。新生PPP、指数寿命、连续SDE；已知不规则扫描时刻输入匿名检测集合，每目标每次扫描至多一个点。更新不读取source/local-ID，保留全局关联假设。原结果与边界见[已有S-ON97](online_literature_continuous_baselines_20261112.md)。

**源码定位订正。** 当前论文对应入口为 `PMBMtarget_cd_filter_linear_SDE.m`，不沿用只指旧 `PMBMtarget_cd_filter.m` 的不充分定位。固定 `cc5c6df0e9343dc1345d91ed6ab95f01db4d1821`，L85–89更新输入z/H/R/p_d/intensity_clutter/Nhyp_max，L121–132按真实Δ更新出生/存活/转移。[作者入口](https://github.com/Agarciafernandez/MTT/blob/cc5c6df0e9343dc1345d91ed6ab95f01db4d1821/CD%20MTT%20filters/PMBMtarget_cd_filter_linear_SDE.m#L85)

**S-ON146 TM-PMBM。** Fontana等，*Poisson multi-Bernoulli mixture filter for trajectory measurements*，IEEE TSP73:4301–4314，2025，DOI10.1109/TSP.2025.3623496，[作者稿v2](https://arxiv.org/html/2504.08421v2)。固定作者仓 `7b5b63fd29f0917bf7e2a2b2904918e773fc89ae`。输入窗口首端/末端/双端三类轨迹量测，内部两端已为同一个物理对象；轨迹量测与系统目标的对应未知，窗末更新再边缘化。`TM_PMBM_filter.m` L95–127、`CreateTrajectoryMeasurement.m` L45–70直接体现两端同真目标生成，场景L23–31为独立两端量测噪声 `kron(eye(2),R.partial)`。不能拿标签把MTAD跨源端点预先拼真。[入口](https://github.com/mrcfon/TM-PMBM/blob/7b5b63fd29f0917bf7e2a2b2904918e773fc89ae/PMBM_filter/TM_PMBM_filter.m#L95) · [生成器](https://github.com/mrcfon/TM-PMBM/blob/7b5b63fd29f0917bf7e2a2b2904918e773fc89ae/PMBM_filter/CreateTrajectoryMeasurement.m#L45)

AI 两者值得保留为联合存在/关联的强系统候选。MTAD需核源报告机会、误差相关、片段出生与物理出生区别；同刻多个来源不能直接合成普通单扫描多点集合。仅校准参数/换合法SDE可明确称共同任务适配；加入local-ID锁定、相关端点、CI、重叠区间或回溯，均改变模型，需保留原版并拆对照。缺条件不排除整类概率法，也不能把无法证实的空扫似然写成真实物理概率。作者代码许可本轮未补核，移入项目源码前仍需确认。

## E-ON129：可读的海事 VIMMJIPDA 核心，区别于 AIS 扩展

新检得 [NTNU公开工程](https://github.com/ntnu-itk-autonomous-ship-lab/vimmjipda)，当前 `b4a0f77ddf72dc8ffd66095418732996c14ea1eb`。README将核心明确对应S-ON44的2021论文，并给CodeOcean3448343/v1，metadata作者为Brekke/Hem/Tokle；仿真接口是Wien/Tengesdal所作，仓称2025年11月公开。根MIT(2025 NTNU-ITK)，核心另有MIT。不是2025新算法论文，也没有核到它等于另一个CodeOcean DOI10.24433/CO.4125751.v2的AIS扩展。[身份](https://github.com/ntnu-itk-autonomous-ship-lab/vimmjipda/blob/b4a0f77ddf72dc8ffd66095418732996c14ea1eb/README.md)

`code/import_data.py` L35–95/98–141从.mat读逐扫描位置集合和时间，AIS/GPS作为单独参考返回；当前树不含两份.mat。`run.py` L27–30默认关闭IMM、多目标和visibility，L45–53逐扫描manager.step，包括空集合。默认命令不是完整VIMMJIPDA设置，复现必须报告开关。[实际入口](https://github.com/ntnu-itk-autonomous-ship-lab/vimmjipda/blob/b4a0f77ddf72dc8ffd66095418732996c14ea1eb/vimmjipda/code/run.py#L27)

`tracking/trackers.py` L45–67预测、门控、冲突组件、条件后验与混合压缩，L69–79运动按实际dt；L113–139区分存在、可见和漏检项，L230–238的存活/可见转移则按一次调用乘固定模型，并非连续时间按秒率。`managers.py` L30–44分开正式和暂定轨迹，存在概率达标才确认。[核心](https://github.com/ntnu-itk-autonomous-ship-lab/vimmjipda/blob/b4a0f77ddf72dc8ffd66095418732996c14ea1eb/vimmjipda/code/tracking/trackers.py#L45)

外层仿真包装 `vimmjipda_tracker_interface.py` L63明确只支持雷达，L99–136只收radar，且仅有新量测时才调用manager；不能直接拿它当AIS多源融合，外层与原始入口的空扫处理也不同。AI 可借鉴聚类关联和存在/可见状态核心，适配原生异步需重核每次事件的存活/可见概率语义。UN 原数据可下载性、完整作者结果复现、AIS扩展代码；本轮CodeOcean DOI经浏览工具无法访问，公开状态留unknown，不改为不存在。[包装](https://github.com/ntnu-itk-autonomous-ship-lab/vimmjipda/blob/b4a0f77ddf72dc8ffd66095418732996c14ea1eb/vimmjipda/vimmjipda_tracker_interface.py#L89)

## 主张—实现核对与交接

| 容易混淆的主张 | 本轮DE | 保留的限制 |
|---|---|---|
| 多频输入意味着同频率对外输出 | Fusion-Poly有4Hz内部事件，只写2Hz结果 | 中间时刻身份和延迟未评 |
| 外推到现在就是收到新证据 | DeepSORVF改预测timestamp并按轮次计数；HAXR相邻窗复用cells | 源报告版本、状态时刻和观察时刻须分开 |
| 未报告就是一次漏检 | Mariner不惩罚无AIS；DetectorContext要已知扫描上下文 | MTAD目前缺扫描清单，不能从报文密度推物理机会 |
| 公开GitHub就是作者完整开源基线 | 有缺模块、仅数据入口、课程工程、部分作者PR | 身份、代码、数据、许可、原结果重现分开 |
| CI处理相关性便自动去重 | 官方feeder不判断新量测版本 | 保守融合不代替证据谱系 |

`candidate_P`：P-ON1/4 的时间与信息权限，P-ON2/3 的缺报/空配和单源持续状态。`candidate_F`：内部更新/发布分离、旧报告预测与新证据不等价、已知观察机会才有空扫似然。`results_with_uncertainty`：以上原文表格及旧来源原分析；静态源码无性能效应量。`limitations_biases_and_ethics`：来源任务和参考差异、许可缺项、未执行边界均逐项列出。`reproducibility_and_transferability`：保留分层候选，不能从可读代码宣称成功迁移。`unresolved_questions`：MTAD报告误差模型、扫描机会、接收时钟、独立物理参考；候选改造后能否保留原机制。`next_skill`：deep-read Mode C v31，再作有条件迁移筛选。

## E-ON130 MTAD 原件中的报告生成与交互时钟

来源沿用 S-ON1。2026-11-12 针对性复核数据论文 §2.1、§2.6(b–g,j,2–3)、表1、答疑 Q5/Q12/Q15、评分 V4 pp1–2 与 V3 激励器归档。已保存原件，本次直接读文本，未执行激励器。

| 要核的条件 | DE | UN 与适用范围 |
|---|---|---|
| 全源扫描及每目标检出概率 | §2.6(d) 的0.8／0.9用于在栅格内抽取整条AIS航迹，源没有选中轨迹时重抽。§2.6(e) 随各轨持续时段按周期分点、扰动时间，再插值，首尾例外。 | 表1的10／20秒不足以恢复共同扫描机会。无完整扫描列表、空扫、覆盖或目标级检测尝试记录。每扫描似然需要另有观测模型和证据。 |
| 源片段与物理生灭 | §2.6(b–c,f–g,2–3) 重置共存起点、缩短首尾、生成中断后设批号，两源混合再按首报时间重编批。Q12/Q15说明同目标同源可有多个片段。 | `(source,batch)` 首报只建立加工源片段首次可用。真实物理出生、死亡及可见性的时间未知。 |
| 交互、真实收报和实际输出 | V4 pp1–2／Q5说按加工时刻每片2秒并握手。V3 zip `Release@20221027/Doc/ChangeLog.txt` L9–10 指明该科目改为10秒。V3 `ReadMe.txt` L13–16、L47规定序号、长度、载荷和首个期望响应。V4结果的生成时刻取当片最小量测时间向下取整为毫秒。 | 两个宽度均为数据发送协议，版本须注明。实际服务端执行仅有二进制，未验证空发送片；客户端解包无独立接收时间。V4生成时刻是评分锚点，墙时另需记录。 |

可用的事件单位为一条加工位置报告的 `(source,batch,time)`。相同单位的重放、该报告的外推或由它形成的局部后验不增加独有报告数；若多条新报告在母AIS中共享插值支撑，它们也未必统计独立。严格回放可在加工时钟上重建已见、超龄和当前报告变化。物理漏检、收报延迟与原始报告噪声相关性保留未知。 [数据论文正文提取（公开出处）](https://doi.org/10.11999/JEIT221202) · [V4原件提取](../source-provenance.md "原件 目标航迹关联评分细则V4.pdf.txt") · [官方V3归档](../source-provenance.md "原件 AlgoStimulatorRelease-V3.zip")

## 原有竞争机制的同任务近邻补读

沿用 `SRC-MHT2TA-2025` 与原 `AP-MHT2TA-20261015-v1`。本轮定向回核 Xu等，FITEE2025，§2.1/2.6、§3/4、表3–4与原补充分析。正文先按跨源冲突分簇，再在当前窗枚举并以边分平均值选匹配。训练随机60秒窗，测试60秒窗、间隔60秒，编码使用窗内终点和场景归一化。五个固定半合成场景共50次Monte Carlo，作者报告AF1 .8888、LCSS .8257，90目标下F1 .7946/.7513。作者分数、几何门和假设选择共同变化，表3无递推保留分支的单因子证据。原文没有跟踪一组备选随原生报文的寿命、持续ID和首确代价，所报关联时间亦未计从首报到窗结束的等待。 [完整来源分析（公开出处）](https://doi.org/10.1631/FITEE.2400340) · [正式论文](https://doi.org/10.1631/FITEE.2400340)

S-ON60 Draves等，MFI2026，复核§III-B–H、§IV–VI。其分区保存互斥源轨组合并随新量测更新，分数使用创新、协方差和轨迹组合规模项。每分区预算随当前最佳假设数变化，作者报告过度裁剪反例。其身份继承依同一假设根，迟到输入可回写轨迹状态，模拟场景的立体方位与通信条件与MTAD不同。两者共同提示对照应固定边分数和候选，观察原生时刻是否真的存在可分辨竞争，再区分延迟、局部搜索与多帧分支的贡献。 [原文](https://arxiv.org/html/2610.20290v1) · [正式议程](https://www.mfi2026.org/program.html)
