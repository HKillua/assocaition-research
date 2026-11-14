# MTAD 在线观测

在本目录运行 `python -m online_observation --help`。需要 NumPy 或 PyTorch 的研究模块可在独立 Python 环境安装 `python -m pip install -e '.[research]'`。

| 内容 | 入口 |
|---|---|
| 当前研究与服务器执行 | [研究状态](docs/research_status.md) · [交接](HandOver/Handover.md) |
| 每次实验遵循的规则 | [AGENTS](AGENTS.md) · [完整科研流程](docs/research_workflow.md) · [技能](.agents/skills/README.md) |
| 数据时序与可见字段 | [MTAD 数据约定](docs/data_contract.md) · [数据名单与对齐配置](configs/data/README.md) |
| 回放与各诊断入口 | [命令](CLI.md) |
| 方案与实际结果 | [提案](docs/proposals/README.md) · [报告](docs/reports/README.md) |
| 历史任务与回传 | [合同与回执](HandOver/README.md) · [服务器规则](docs/server_autonomy.md) |
| 文献、证据矩阵和实验原件索引 | [在线文献与 Mode C](docs/surveys/README.md) · [运行证据](docs/evidence/README.md) |

每次科研实验均遵循[飞书《视频文案》](https://my.feishu.cn/wiki/OHs3w9meHiQ3OXk4XC7ctFPXnxd)和[本仓完整流程](docs/research_workflow.md#2-必须遵守的研究顺序)。本仓从[原在线工程](https://github.com/HKillua/association-code/tree/399da72/online_observation)迁入，历史报告保留原运行编号与来源。原始 MTAD 数据由调用者按数据约定提供。
