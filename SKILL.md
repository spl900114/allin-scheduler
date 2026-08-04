---
name: allin-scheduler
description: 通用 AI Agent 多角色 DAG 编排调度器（Codex/Hermes/ChatGPT/Claude/通义千问 通用）。当用户需要把多步任务拆成 DAG、排依赖批次、校验循环依赖、生成调度报告、规划多角色开发流程、或按阶段门禁执行项目计划时使用。
---

# Allin-Scheduler — 通用 AI Agent 多角色编排调度器

> 多角色 DAG 调度 + grilling 前置拷问 + 门禁验收
> 不依赖 Codex / Hermes / LangChain / 任何特定框架
> 通用 markdown 格式，任意 AI Agent 都能读懂并执行

## 运行方式（先读这个）

配套脚本 `scheduler.py` 负责**纯规划**：

```bash
python scheduler.py dag.yaml --validate   # 只校验拓扑
python scheduler.py dag.yaml              # 出 JSON 计划
python scheduler.py dag.yaml --report     # 出 Markdown 批次报告
python scheduler.py dag.yaml --verify     # 完整性门控:校验各节点 output_path 是否存在
python scheduler.py dag.yaml --config my-config.yaml  # 指定配置文件
```

依赖：`pip install pyyaml`。Windows 中文控制台已内置编码兜底，直接可跑。

## 工作流程全景

```
用户一句话指令
      |
      v
┌──────────────────────────────┐
│ Phase 0: Grilling 前置拷问    │
│   目标 / 边界 / 风险 /        │
│   验收标准 / 前置依赖         │
│   产出写入 grill-session.md   │
└──────────────────────────────┘
      |
      v
┌──────────────────────────────┐
│ Phase 1: 状态机入口           │
│   Quick/Hotfix（捷径）        │
│   Full（完整流程）            │
└──────────────────────────────┘
      |
      v
┌──────────────────────────────┐
│ Phase 2: DAG 任务分解         │
│   角色分配 + 依赖 + 产出路径  │
│   循环检测                   │
└──────────────────────────────┘
      |
      v
┌──────────────────────────────┐
│ Phase 3: 派发                │
│   多子 Agent：每批 <= 并发数  │
│   单 Agent：按拓扑串行        │
│   批间上下文传递             │
└──────────────────────────────┘
      |
      v
┌──────────────────────────────┐
│ Phase 4: 完整性门控 + 重试    │
│   角色级产物校验              │
│   最多 2 轮回派重试           │
└──────────────────────────────┘
      |
      v
┌──────────────────────────────┐
│ Phase 5: 失败处理             │
│   API 超时重试 / Stall 超时   │
│   FAILED 不阻断后续           │
└──────────────────────────────┘
      |
      v
┌──────────────────────────────┐
│ G3 质量门禁 -> G4 交付门禁    │
│ qa-engineer -> devops-engineer│
└──────────────────────────────┘
```

## 调度模式检测

调度内核在 Phase 0 之前先检测当前 Agent 环境支持哪种调度模式：

| 模式 | 检测条件 | 行为 |
|------|---------|------|
| **多子 Agent 模式** | 框架支持创建/派发子 Agent（如 Codex spawn_agent、Hermes delegate_task、Claude Project 多 Agent、自建多实例） | 按需创建角色子 Agent，按 DAG 并行派发 |
| **单 Agent 模式（Fallback）** | 不支持子 Agent / 用户未配置多角色 | 调度内核自己扮演全部角色，按 DAG 拓扑顺序串行执行 |
| **纯规划模式** | 只使用 scheduler.py | 只产出批次计划/报告，由人或其它工具执行 |

> 注意：`scheduler.py` 本身只实现"纯规划模式"；多子 Agent / 单 Agent 执行模式是给宿主 Agent 的编排规范。

### 自动模式选择（默认行为，无需用户指定）

收到任务后由调度内核自动选模式，**不等用户说"并行/串行"**：

| 任务情况 | 自动选择 |
|---|---|
| 用户只要计划 / 报告 / 排批次 | **纯规划模式**：跑 scheduler.py，不派任何子 Agent |
| 执行时：同批有 2-3 个互相独立（无依赖、产出路径不冲突）且够分量（effort >= 0.5 人天 或预计 >= 30 分钟）的节点 | **多子 Agent 并行**：按宿主平台并发上限执行（Codex 环境上限 3 个子 Agent）；槽位不足时自动降级串行 |
| 执行时：其余情况（单节点、链式依赖、共享同一文件/状态、小任务） | **单 Agent 串行** |
| 任务模糊 / 信息不足 | 先 grill，不急着选模式 |

判断口诀：**独立 + 够分量 + 槽位够 -> 并行；只要计划 -> 纯规划；其余 -> 串行。**

选并行时向用户说明理由（哪几个节点独立、为什么值得并行），用户可随时打断改回串行。

## 角色列表

| 角色标识 | 专长 | 调度方式 |
|----------|------|---------|
| `product-manager` | 需求 / PRD / 功能规划 | 独立 Agent / 调度内核自演 |
| `architect` | 系统架构 / 契约 / 技术选型 | 独立 Agent / 调度内核自演 |
| `backend-engineer` | API / DB / 业务逻辑 | 独立 Agent / 调度内核自演 |
| `frontend-engineer` | 前端 / 桌面端 | 独立 Agent / 调度内核自演 |
| `ui-ux-designer` | 界面 / 交互设计 | 独立 Agent / 调度内核自演 |
| `qa-engineer` | 测试策略 / 测试编写 | 独立 Agent / 调度内核自演 |
| `devops-engineer` | CI/CD / 部署 / 监控 | 独立 Agent / 调度内核自演 |
| `data-engineer` / `ml-engineer` | 数据管道 / 模型 | 独立 Agent / 调度内核自演 |

角色列表可在 `config.yaml` 中按项目增删；DAG 里用了列表外的角色会报验证警告。

### 多子 Agent 模式：按需自动创建角色

```
DAG 用了 architect + frontend-engineer + qa-engineer
      ->
调度内核检查: 这 3 个角色有现成 Agent 吗？
  ├─ 有 -> 直接复用
  └─ 没有 -> 自动创建
       ├─ 创建 arch-Agent（注入架构师 SOUL + 契约上下文）
       ├─ 创建 frontend-Agent（注入前端 SOUL + 代码上下文）
       └─ 创建 qa-Agent（注入测试 SOUL + 测试上下文）
      ->
按 DAG 依赖并行派发
```

创建角色时注入的内容：角色身份、项目上下文（PROJECT_ROOT、契约指针、前置批次摘要）、当前 DAG 节点的 goal + output_path + verification。

角色复用策略：同一项目多次调度时，已创建的角色子 Agent 保留在当前项目上下文中，下次直接复用。

## Phase 0：Grilling 前置拷问

在调度任何任务之前，必须先执行一次需求拷问，确保目标明确。

| 维度 | 问题示例 |
|------|---------|
| 目标 | "这个功能要解决什么具体问题？用户场景是什么？" |
| 边界 | "边界在哪？哪些场景不在范围内？" |
| 风险 | "最大的技术风险/不确定性是什么？" |
| 验收标准 | "怎样才算做完？什么指标度量成功？" |
| 前置依赖 | "有哪些外部依赖还没确认？凭据有吗？" |

产出写入 `grill-session-<date>.md`：一句话意图、变更范围、验收条件、依赖清单。

## Phase 1：状态机入口

| 路径 | 条件 | 行为 |
|------|------|------|
| **仍模糊** | grilling 后仍不清楚 | 再次 grill 或触发 need-explorer |
| **Quick/Hotfix** | 仅改现有代码逻辑，不新增文件、不改 schema/契约/外部依赖 | 直接进入 execution |
| **Full** | 新功能/新模块/新文件/改 schema/新依赖 | 走完整状态机 |

完整状态机：`exploring -> specifying -> bridging -> approved-for-build -> executing -> closing`

## Phase 2：DAG 任务分解

### 节点字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `node_id` | 唯一标识 | `m13-webxr-presearch` |
| `assignee` | 角色标识 | `frontend-engineer` |
| `arch_phase` | 架构阶段：`front`（前置定方案）/ `back`（后置审内核）/ 留空 | `front` |
| `parents` | 依赖节点 ID 列表 | `[]` 或 `["m12-oapi-design"]` |
| `goal` | 任务目标 | "调研 WebXR 兼容性，输出兼容矩阵" |
| `context` | 项目上下文 | 含 PROJECT_ROOT + 契约指针 |
| `output_path` | 期望产出路径 | `research/webxr-compatibility.md` |
| `verification` | 完成标准 | "文件存在且内容非空" |
| `effort` | 可选：预估人天，用于排序 | `0.5` |

### DAG 循环检测

调度引擎在分解后遍历所有节点的 parents 链，发现循环依赖（如 A->B->C->A）则报错并要求手动修正。

### Architect 先后置分离

- `arch_phase: front`（前置架构）：在第一批发，定技术方案、选型、契约框架
- `arch_phase: back`（后置内核）：在工程师任务全部完成后发，审核交付、同步契约

## Phase 3：派发

### 多子 Agent 模式：并行派发

```
parents 为空的节点 -> 按需创建/复用子 Agent 并并行派发（<= 并发数）
parents 不为空的节点 -> 等所有 parent 完成后分批发
```

批次拆分规则：每批 <= max_concurrency（默认 5）；排序策略：工作量大的节点优先发出；第二批在上批全部返回后发出。

### 单 Agent 模式：串行执行

```
按 topo_sort 顺序:
  for each 节点:
    执行该节点的 goal
    产出到 output_path
    自我完整性校验
    通过 -> 继续下一个
    不通过 -> 退回重做（<=2 轮）
```

### 批间上下文传递

每批 Agent 返回后，调度引擎提取其关键产出路径 + 摘要，注入下一批每个节点的 context 开头：

```
[前置产出]
M13-01: 产出 research/webxr-compatibility.md，结论是 iOS Safari 不支持 hit-test
M13-02: 产出 docs/downgrade-plan.md，降级方案分 3 档
──────────────────────────────
```

### 同角色串行处理

如果 DAG 中多个节点 assignee 相同且有依赖关系，合并到同一个 goal 中一次性发出，避免 Agent 反复加载上下文。

## Phase 4：完整性门控

先用脚本自动校验产物是否落地：

```bash
python scheduler.py dag.yaml --verify   # 缺文件时 exit=1，并在控制台列出 ❌ 节点
```

| 角色 | 必检项 | 重试条件 |
|------|--------|---------|
| `*-engineer` | 代码文件存在且非空 | 缺文件 -> 回派（<=2 轮） |
| `qa-engineer` | 测试文件存在且非空 | 同上 |
| `architect` | 契约/文档文件存在 | 同上 |
| 其余角色 | 对应文档存在 | 同上 |

脚本校验通过后再做角色级审查；重试时附缺口说明；仍失败 -> 标记 `FAILED`，告知用户。

## Phase 5：失败处理

| 失败类型 | 处理 |
|---------|------|
| API 超时 / 504 | 自动重试 2 次 |
| 完整性缺失 | 回派重试（<=2 轮，附缺口说明） |
| Agent stall（> 10 分钟无输出） | 终止该 Agent，标记 FAILED |
| 以上仍失败 | 标记 FAILED，告知用户，不阻断后续 |

## 门禁判定

### G3 质量门禁（qa-engineer 完成时触发）

```yaml
check:
  - tests_pass: true
  - tsc_zero_errors: true
  - no_p0_bugs: true
```

qa-engineer 发现 bug -> 自动创建修复任务回派对应 engineer，修复后 qa 再验证。验证通过才算 G3 通过。

### G4 交付门禁（devops-engineer 完成时触发）

```yaml
check:
  - deploy_script: true
  - monitoring: true
  - contracts_synced: true
  - g0_g1_g2_g3_pass: true
```

## 适配不同 AI Agent 平台

| 平台 | 适配方法 |
|------|---------|
| **Codex** | 直接使用 SKILL.md，用 spawn_agent / followup_task 派发 |
| **Hermes** | 直接使用 SKILL.md，用 delegate_task 派发 |
| **ChatGPT / GPTs** | 将 SKILL.md 作为 Knowledge 文件上传，用 Actions 调 API |
| **Claude / Cline** | 复制 SKILL.md 到项目根目录 |
| **通义千问 / 文心一言** | 将规则注入 System Prompt |
| **自建 Agent** | 用 scheduler.py + config.yaml 实现编排引擎 |
