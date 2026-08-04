# Allin-Scheduler 完整运作流程示例（通用版）

> 以"智能客服知识助手增加 RAG 问答功能"为例，展示一次完整调度周期的每一步。

---

## 场景

用户说："给智能客服知识助手增加 RAG 问答功能，支持引用来源。"

---

## Step 0：Grilling 前置拷问

调度内核先执行一次需求拷问：

| 维度 | 用户回答 |
|------|---------|
| **目标** | 用户问客服问题时，回答基于公司知识库，并附引用来源 |
| **边界** | 只做文本问答，不做语音/多模态；不处理权限分级 |
| **风险** | 检索准确率不达标；向量库选型不确定；需要 GPU 还是 CPU 推理 |
| **验收** | 10 条典型问题的回答引用正确率 >= 90%；流式首字 < 1s |
| **凭据** | 无外部依赖（纯内部系统 + 现有 AI 大模型） |

**产出:** `grill-session-2026-08-04.md`

```
意图: 增加 RAG 问答功能
范围: 文本问答 + 引用来源，不做语音/多模态
验收: 引用正确率 >= 90% / 首字 < 1s
```

---

## Step 1：状态机入口

清晰 + 新功能 + 新文件 -> **Full 路径**

```
exploring -> specifying -> bridging -> approved-for-build -> executing -> closing
```

---

## Step 2：DAG 任务分解

调度内核拆解出 8 个节点（见 `examples/simple-dag.yaml`），包含：

- 前置调研（backend-engineer + data-engineer，并行）
- 前置架构方案（architect, front）
- 并行开发（backend-engineer + frontend-engineer）
- 集成（backend-engineer）
- 后置审核（architect, back）
- 验收（qa-engineer）

**循环检测** 遍历所有 parents 链，无循环 ✅

---

## Step 3：派发

### 第 1 批（2 节点，并行）

| 节点 | 角色 | 说明 |
|------|------|------|
| `rag-retrieval-presearch` | backend-engineer | 调研检索方案 |
| `kb-schema-design` | data-engineer | 设计知识库 schema |

### 第 2 批：上下文传递

前置产出摘要注入 context：

```
[前置产出]
rag-retrieval-presearch: 产出 research/rag-retrieval-comparison.md
  - 结论: 采用 BM25 + 向量混合召回，向量库选 SQLite-vec
kb-schema-design: 产出 docs/design/kb-schema.md
  - 表: documents / chunks / vectors + 3 个索引
──────────────────────────────
```

### 第 3 批（2 节点，并行）

| 节点 | 角色 | 说明 |
|------|------|------|
| `rag-ingest-pipeline` | backend-engineer | 实现入库管道 |
| `rag-chat-ui` | frontend-engineer | 实现问答界面 |

### 第 4 批

| 节点 | 角色 | 说明 |
|------|------|------|
| `rag-qa-integration` | backend-engineer | 打通端到端链路 |

### 第 5 批 / 第 6 批

| 节点 | 角色 | 说明 |
|------|------|------|
| `rag-arch-review` | architect (back) | 后置审核 |
| `rag-acceptance` | qa-engineer | P0 验收 |

---

## Step 4：完整性门控

每个 Agent 返回后校验：

- `rag-retrieval-presearch` -> `research/rag-retrieval-comparison.md` ✅ 存在且 > 0 字节
- `rag-ingest-pipeline` -> `src/backend/ingest.py` ✅ 存在
- `rag-chat-ui` -> `src/frontend/views/ChatView.vue` ✅ 存在
- ...

---

## Step 5：失败处理

假设 `rag-ingest-pipeline` 超时未返回（stall > 15 分钟）：

1. 终止该 Agent
2. 标记 FAILED
3. 告知用户
4. 不阻断后续批次 —— 继续派发下一个已知信息能跑的节点

---

## G3 质量门禁

qa-engineer 拿到全部交付后：

1. 运行所有测试
2. 发现 ChatView.vue 在低端机上流式渲染卡顿
3. -> 自动创建修复任务派给 frontend-engineer
4. frontend-engineer 优化后 qa 重新验证
5. 验证通过 -> G3 ✅

---

## G4 交付门禁

devops-engineer 拿到全部交付后：

1. 检查 DEPLOY.md ✅
2. 检查 .env.example ✅
3. 检查 contracts/ 同步 ✅
4. G0~G3 全部 ✅
5. -> G4 ✅

---

## 最终交付

调度内核汇总全部产出，向用户展示：

```
智能客服知识助手 - RAG 问答功能已就绪 ✅

新增文件:
  src/backend/ingest.py               - 文档入库管道
  src/backend/qa_router.py            - 检索+生成路由
  src/frontend/views/ChatView.vue     - 问答对话界面
  research/rag-retrieval-comparison.md
  docs/design/rag-architecture.md
  contracts/api/openapi.yaml

新增依赖:
  sqlite-vec  ^0.1.0

门禁:
  G0 ✅  G1 ✅  G2 ✅  G3 ✅  G4 ✅

演示: 打开 http://localhost:5173/chat
```
