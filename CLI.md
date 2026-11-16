# 在线观测命令

从在线仓库根目录执行，使用 Python 3.10+ 标准库。新研究运行前先对照[研究状态](docs/research_status.md)与[科研流程](docs/research_workflow.md)。

| 命令 | 用途 |
|---|---|
| `python -m online_observation causal-replay --help` | 单场、逐秒的工程回放，验证递送及输出。CSV 整行速航是工程控制，字段权限见[数据约定](docs/data_contract.md#在线字段可用时间)。 |
| `python -m online_observation.peer_experiment --help` | 原 28 场同行适配，使用有序 Level1 分卷；先冻结预测，再读取标签和参考。 |
| `python -m online_observation.peer_chain_audit --help` | 在原适配的私有冻结结果上核长错链和报文支撑。 |
| `python -m online_observation.peer_history_experiment --help` | 历史格消融，`--frozen` 指向原 28 场适配结果。加 `--frozen-history` 指向 v1.5 三臂输出，执行固定的五臂比较。 |
| `python -m unittest discover -s online_observation/tests` | 软件核验。 |

研究运行命令和配置见[对应报告](docs/reports/README.md)。私有输出含片段身份和坐标。旧诊断命令见[历史归档](docs/history/README.md)。
