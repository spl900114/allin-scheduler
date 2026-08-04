# Allin-Scheduler README

> 通用 AI Agent 多角色编排调度器  
> 适用任何 AI Agent 框架（Hermes, ChatGPT, Claude, 通义千问等）  
> 不依赖特定平台，**一个 Python 脚本 + 一份 YAML 配置**即可运行

---

## 一句话

**让 AI Agent 能像项目经理一样：grill 问清需求 → 拆 DAG 任务 → 并行派发多个角色 → 门禁验收。**

---

## 文件结构

```
allin-scheduler/
├── README.md              ← 你正在看这个
├── scheduler.py           ← 编排引擎（可执行 Python 脚本）
├── config.yaml            ← 配置（角色、门禁、超时）
├── SKILL.md               ← AI Agent 的"使用说明书"（通用 markdown）
└── examples/
    ├── simple-dag.yaml    ← 简单 DAG 示例
    └── full-flow.md       ← 完整运作流程示例
```

---

## 快速开始

```bash
# 1. 定义你的 DAG 任务
# 编辑 dag.yaml（参考 examples/simple-dag.yaml）

# 2. 运行调度器
python scheduler.py dag.yaml

# 3. 查看结果
cat output/schedule-report.md
```

---

## 核心概念

| 概念 | 说明 |
|------|------|
| **Grill** | 执行调度前的需求拷问阶段，确保目标清晰 |
| **DAG** | 有向无环图，表达任务依赖关系 |
| **Role** | 专业角色（architect / backend-engineer / ...） |
| **Gate** | 门禁，每个阶段完成后的质量检查点 |
| **Agent** | 执行具体任务的工作单元 |

---

## 适用场景

- 多角色协作的软件开发项目
- 需要阶段门禁的质量管控流程
- 多人天的工作需要拆解并行
- 每次交付前需要完整性校验
