# Allin-Scheduler（通用 AI Agent 版）

> 通用 AI Agent 多角色编排调度器
> 适用任意 AI Agent 框架（Codex / Hermes / ChatGPT / Claude / 通义千问 / 文心一言 等）
> 不依赖特定平台，**一个 Python 脚本 + 一份 YAML 配置**即可运行

## 一句话

让 AI Agent 像项目经理一样：**grill 问清需求 -> 拆 DAG 任务 -> 并行派发多角色 -> 门禁验收**。

本工具负责"规划"部分（校验 / 排序 / 分批 / 出报告）；"执行"部分由宿主 Agent 按 `SKILL.md` 完成。

## 文件结构

```
allin-scheduler/
├── scheduler.py           <- 编排引擎（可执行 Python 脚本）
├── config.yaml            <- 配置（角色、门禁、超时、输出目录）
├── README.md              <- 你正在看这个
├── SKILL.md               <- AI Agent 的使用说明书（通用 markdown）
└── examples/
    ├── simple-dag.yaml    <- 简单 DAG 示例
    └── full-flow.md       <- 完整运作流程示例
```

## 快速开始

```bash
# 1. 定义你的 DAG 任务（参考 examples/simple-dag.yaml）
# 2. 运行调度器
python scheduler.py dag.yaml
# 3. 查看结果
cat output/schedule-report.md
```

常用模式：

```bash
python scheduler.py dag.yaml --validate   # 只校验拓扑（不写文件）
python scheduler.py dag.yaml              # 生成 JSON 计划
python scheduler.py dag.yaml --report     # 生成 Markdown 批次报告
python scheduler.py dag.yaml --verify     # 完整性门控：校验各节点 output_path 是否存在
python scheduler.py dag.yaml --config my-config.yaml  # 指定配置文件
```

> Windows 中文控制台（GBK）已内置编码兜底，直接可跑，无需手动设 `PYTHONIOENCODING`。

`--verify` 会以 DAG 文件所在目录为根，逐个检查 `output_path` 是否存在且非空，缺文件时列出 ❌ 节点并以 exit=1 退出，适合作为执行完一批后的门禁检查。可用 `--root <路径>` 指定根目录。

## 核心概念

| 概念 | 说明 |
|------|------|
| **Grill** | 执行调度前的需求拷问阶段，确保目标清晰 |
| **DAG** | 有向无环图，表达任务依赖关系 |
| **Role** | 专业角色（architect / backend-engineer / ...） |
| **Gate** | 门禁，每个阶段完成后的质量检查点 |
| **Agent** | 执行具体任务的工作单元 |

## 适用场景

- 多角色协作的软件/文档/数据项目
- 需要阶段门禁的质量控制流程
- 多人天的工作需要拆解并行
- 每次交付前需要完整性校验

## 与 TMC 智慧空间助手的关系

仓库内已内置本项目 Phase 2 关键路径 DAG：`phase-2-ar-dag.yaml`（M13->M14 共 10 节点）。
修改计划后重新生成报告：

```bash
python scripts/allin-scheduler/scheduler.py phase-2-ar-dag.yaml --report
```

报告输出到 `scripts/allin-scheduler/output/schedule-report.md`。
