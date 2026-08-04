# Allin-Scheduler — 通用 AI Agent 编排调度器

> 多角色 DAG 调度 + grilling 前置拷问 + 门禁验收
> 不依赖 Hermes / LangChain / 任何特定框架
> 通用 markdown 格式，任何 AI Agent 都能读懂并执行

---

## 工作流程全景

```
用户一句话指令
      │
      ▼
┌─────────────────────────────┐
│ Phase 0: Grilling 前置拷问    │
│  ─ 目标 / 边界 / 风险 /      │
│    验收标准 / 前置依赖        │
│  ─ 产出写入 grill-session.md │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ Phase 1: 状态机入口           │
│  ─ Quick/Hotfix（短路径）     │
│  ─ Full（完整流程）           │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ Phase 2: DAG 任务分解         │
│  ─ 角色分配 + 依赖 + 产出路径 │
│  ─ 循环检测                  │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ Phase 3: 并行派发             │
│  ─ 每批 ≤N 个并发             │
│  ─ 批次间上下文传递           │
│  ─ 同角色串行合并             │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ Phase 4: 完整性门控 + 重试    │
│  ─ 角色级产出校验             │
│  ─ ≤2 轮回派重试             │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ Phase 5: 失败处理             │
│  ─ API 超时重试              │
│  ─ Stall 超时（10min）       │
│  ─ FAILED 不阻断后续          │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ G3 质量门禁 → G4 交付门禁     │
│  qa-engineer → devops-engineer│
└─────────────────────────────┘
```

---

## 调度模式检测

allin-scheduler 在 Phase 0 之前先检测当前 Agent 环境支持哪种调度模式：

| 模式 | 检测条件 | 行为 |
|------|---------|------|
| **多子 Agent 模式** | 框架支持创建/派发子 Agent（如 Hermes delegate_task、Claude Project 多 Agent、自定义多实例） | **按需自动创建角色子 Agent**，按 DAG 并行派发 |
| **单 Agent 模式（Fallback）** | 不支持子 Agent / 用户未配置多角色 | 编排内核自己扮演全部角色，按 DAG 拓扑顺序**串行执行** |

> 单 Agent 模式没有并行加速，但流程完整（Grill → DAG → 门禁），一样能用。

---

## 角色列表

| 角色标识 | 专长 | 调度方式 |
|----------|------|---------|
| `product-manager` | 需求 / PRD / 功能规划 | 独立 Agent / 编排内核自演 |
| `architect` | 系统架构 / 契约 / 技术选型 | 独立 Agent / 编排内核自演 |
| `backend-engineer` | API / DB / 业务逻辑 | 独立 Agent / 编排内核自演 |
| `desktop-engineer` | 前端 / 桌面端 | 独立 Agent / 编排内核自演 |
| `ui-ux-designer` | 界面 / 交互设计 | 独立 Agent / 编排内核自演 |
| `qa-engineer` | 测试策略 / 测试编写 | 独立 Agent / 编排内核自演 |
| `devops-engineer` | CI/CD / 部署 / 监控 | 独立 Agent / 编排内核自演 |

### 多子 Agent 模式：按需自动创建角色

当处于多子 Agent 模式时，编排内核在 Phase 2 解析 DAG 后**自动识别需要哪些角色**，然后**按需创建**对应的子 Agent：

```
DAG 用了 architect + desktop-engineer + qa-engineer
     ↓
编排内核检查: 这 3 个角色有现成子 Agent 吗？
     ├── 有 → 直接复用
     └── 没有 → 自动创建
           ├── 创建 arch-Agent（注入架构师 SOUL + 契约上下文）
           ├── 创建 frontend-Agent（注入前端 SOUL + 代码上下文）
           └── 创建 qa-Agent（注入测试 SOUL + 测试上下文）
     ↓
按 DAG 依赖并行派发
```

**创建角色时注入的内容：**
- 角色身份（该角色的专业定位、能力边界）
- 项目上下文（PROJECT_ROOT、契约指针、前置批次摘要）
- 当前 DAG 节点的 goal + output_path + verification

**角色复用策略：** 同一项目多次调度时，已创建的角色子 Agent 保留在当前项目上下文中，下次可直接复用，避免重复创建。

---

## Phase 0：Grilling 前置拷问

在调度任何任务之前，必须先执行一次需求拷问，确保目标明确。

### 拷问维度

| 维度 | 问题示例 |
|------|---------|
| 目标 | "这个功能要解决什么具体问题？用户场景是什么？" |
| 边界 | "边界在哪？哪些场景不在范围内？" |
| 风险 | "最大的技术风险/不确定性是什么？" |
| 验收标准 | "怎么才算做完？什么指标衡量成功？" |
| 前置依赖 | "有哪些外部依赖还没确认？凭据有吗？" |

### 产出

grilling 产出写入 `.hermes/plans/grill-session-<date>.md`（或其他同效用文件名）：
- 一句话意图
- 变更范围
- 验收条件
- 依赖清单

---

## Phase 1：状态机入口

### 判断路径

基于 grilling 后的清晰度选择路径：

| 路径 | 条件 | 行为 |
|------|------|------|
| **仍模糊** | grilling 后仍不清楚 | 再次 grill 或触发 need-explorer |
| **Quick/Hotfix** | 仅改现有代码逻辑，不新增文件、不改 schema/契约/外部依赖 | 直接进入 execution |
| **Full** | 新功能/新模块/新文件/改 schema/新依赖 | 走完整状态机 |

### 完整状态机（Full 路径）

```
exploring → specifying → bridging → approved-for-build → executing → closing
```

探索 → 规格 → 契约 → 批准建设 → 执行 → 关闭

---

## Phase 2：DAG 任务分解

### 节点定义

每个任务节点包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `node_id` | 唯一标识 | `m13-webxr-presearch` |
| `assignee` | 角色标识 | `desktop-engineer` |
| `arch_phase` | 架构阶段：`front`（前置定方案）/ `back`（后置审核）/ 留空 | `front` |
| `parents` | 依赖节点 ID 列表 | `[]` 或 `["m12-oapi-design"]` |
| `goal` | 任务目标 | "调研 WebXR 兼容性，输出兼容矩阵" |
| `context` | 项目上下文 | 含 PROJECT_ROOT + 契约指针 |
| `output_path` | 期望产出路径 | `research/webxr-compatibility.md` |
| `verification` | 完成标准 | "文件存在且内容非空" |

### DAG 循环检测

编排引擎在分解后遍历所有节点的 parents 链，发现循环依赖（如 A→B→C→A）则报错并要求手动修正。

### Architect 先后置分流

- `arch_phase: front`（前置架构）：在第一批发出，定技术方案、选型、契约骨架
- `arch_phase: back`（后置审核）：在工程师任务全部完成后发出，审核交付、同步契约

---

## Phase 3：派发（多子 Agent / 单 Agent）

### 多子 Agent 模式：并行派发

```
parents 为空的节点 → 按需创建/复用子 Agent 并并行派发（≤并发数）
parents 不为空的节点 → 等所有 parent 完成后分批发出
```

批次拆分规则：
- 每批 ≤ max_concurrency 个并发（默认 5）
- 排序策略：工作量大的节点优先发出
- 第二批在上批全部返回后发出

**创建子 Agent 的 context 注入模板：**
```
PROJECT_ROOT=<绝对路径>
角色: <当前角色名>
任务: <当前节点 goal>
产出路径: <output_path>
完成标准: <verification>
[前置产出]
<上一批的关键产出摘要>
─────────────────────────────
```

### 单 Agent 模式：串行执行

没有子 Agent 能力时，编排内核自己按 DAG 拓扑顺序逐个执行：

```
按 topo_sort 顺序:
  for each 节点:
    执行该节点的 goal
    产出到 output_path
    自我完整性校验
    通过 → 继续下一个
    不通过 → 回退重做（≤2 轮）
```

**区别：**
- 没有并行加速——一次只做一个任务
- 没有角色切换——编排内核自己扮演所有角色
- 但流程完整——Grill → DAG → 执行 → 门禁，一个不落

### 批次间上下文传递

每批 Agent 返回后，编排引擎提取其关键产出路径 + 摘要，注入下一批每个节点的 context 开头：

```
[前置产出]
M13-01: 产出 research/webxr-compatibility.md，结论是 iOS Safari 不支持 hit-test
M13-02: 产出 docs/downgrade-plan.md，降级方案分 3 档
─────────────────────────────
```

### 同角色串行处理

如果 DAG 中多个节点 assignee 相同且有依赖关系，合并到同一个 goal 中一次性发出，避免 Agent 反复加载上下文。

---

## Phase 4：完整性门控

### 校验标准

| 角色 | 必检项 | 重试条件 |
|------|-------|---------|
| `*-engineer` | 代码文件存在且非空 | 缺文件 → 回派（≤2 轮） |
| `qa-engineer` | 测试文件存在且非空 | 同上 |
| `architect` | 契约/文档文件存在 | 同上 |
| 其余角色 | 对应文档存在 | 同上 |

### 重试

- 重试时附缺口说明
- ≤2 轮回派
- 仍失败 → 标记 `FAILED`，告知用户

---

## Phase 5：失败处理

| 失败类型 | 处理 |
|---------|------|
| API 超时 / 504 | 自动重试 2 次 |
| 完整性缺口 | 回派重试（≤2 轮，附缺口说明） |
| Agent stall（>10 分钟无输出） | 终止该 Agent，标记 FAILED |
| 以上仍失败 | 标记 FAILED，告知用户，不阻断后续 |

---

## 门禁判定

### G3 质量门禁（qa-engineer 完成时触发）

```yaml
check:
  - tests_pass: true
  - tsc_zero_errors: true
  - no_p0_bugs: true
```

qa-engineer 发现 bug → 自动创建修复任务回派对应 engineer，修复后 qa 再验证。验证通过才算 G3 通过。

### G4 交付门禁（devops-engineer 完成时触发）

```yaml
check:
  - deploy_script: true
  - monitoring: true
  - contracts_synced: true
  - g0_g1_g2_g3_pass: true
```

---

## YAML 配置参考（config.yaml）

```yaml
# allin-scheduler 全局配置
project:
  root: "."
  name: "my-project"

# 并发限制
max_concurrency: 5

# 超时
stall_timeout_minutes: 10
api_retry_count: 2

# 门禁
gates:
  g0: auto
  g1: auto
  g2: auto
  g3: qa-engineer
  g4: devops-engineer

# 角色
roles:
  - product-manager
  - architect
  - backend-engineer
  - desktop-engineer
  - ui-ux-designer
  - qa-engineer
  - devops-engineer
```

---

## DAG 示例（dag.yaml）

```yaml
nodes:
  - node_id: m13-webxr-presearch
    assignee: desktop-engineer
    parents: []
    goal: "调研 iOS Safari 和 Android Chrome 的 WebXR 兼容性"
    output_path: research/webxr-compatibility.md
    verification: "文件存在且非空"

  - node_id: m13-downgrade-plan
    assignee: architect
    arch_phase: front
    parents: [m13-webxr-presearch]
    goal: "基于兼容性调研输出降级方案"
    output_path: docs/downgrade-plan.md
    verification: "文件存在且非空"
```

---

## 适配不同 AI Agent 平台

| 平台 | 适配方法 |
|------|---------|
| **Hermes** | 直接使用 SKILL.md，用 `delegate_task` 派发 |
| **ChatGPT / GPTs** | 将 SKILL.md 作为 Knowledge 文件上传，用 Actions 调 API |
| **Claude / Cline** | 复制 SKILL.md 到项目根目录 |
| **通义千问 / 文心一言** | 将规则注入 System Prompt |
| **自建 Agent** | 用 scheduler.py + config.yaml 实现编排引擎 |
