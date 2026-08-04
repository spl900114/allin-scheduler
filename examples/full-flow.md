# Allin-Scheduler 完整运作流程示例

> 以 TMC 智慧空间助手 Phase 2 AR 导航模块为例，展示一次完整调度周期的每一步。

---

## 场景

用户说："给 TMC 智慧空间助手增加 AR 导航功能。"

---

## Step 0：Grilling 前置拷问

编排内核先执行一次需求拷问：

| 维度 | 用户回答 |
|------|---------|
| **目标** | 用户走进办公楼，打开手机浏览器，摄像头画面中叠加 3D 箭头指引到会议室 |
| **边界** | 只在 4F 范围；不需要室外导航；不需要多人协同 |
| **风险** | iOS Safari 可能不支持 WebXR；公司网络摄像头权限有策略限制 |
| **验收** | Android Chrome 真 AR 叠加箭头；iOS Safari 降级到屏幕方向提示；导航响应 < 2s |
| **凭据** | 无外部依赖（纯前端） |

**产出:** `grill-session-2026-08-03.md`

```
意图: 增加 AR 室内导航功能
范围: 4F 室内，摄像头叠加 3D 箭头指引到目标房间
验收: Android AR / iOS 降级 / 响应 < 2s
```

---

## Step 1：状态机入口

清晰 + 新功能 + 新文件 → **Full 路径**

```
exploring → specifying → bridging → approved-for-build → executing → closing
```

---

## Step 2：DAG 任务分解

编排内核拆解出 7 个节点（见 examples/simple-dag.yaml），包含：

- 前置调研（desktop-engineer）
- 前置架构方案（architect, front）
- 并行开发（desktop-engineer × 2 + ui-ux-designer）
- 集成（desktop-engineer）
- 后置审核（architect, back）

**循环检测:** 遍历所有 parents 链，无循环 ✅

---

## Step 3：并行派发

### 第 1 批（2 节点）

| 节点 | 角色 | 说明 |
|------|------|------|
| `m13-webxr-presearch` | desktop-engineer | 调研 WebXR 兼容性 |
| `m13-arch-plan` | architect (front) | 需要等上一步完成 |

→ 实际只有 `m13-webxr-presearch` 可立即派发。
→ `m13-arch-plan` 等它完成后续发。

### 第 2 批：上下文传递

前置产出摘要注入 context：

```
[前置产出]
m13-webxr-presearch: 产出 research/webxr-compatibility.md
  - iOS Safari: 不支持 hit-test, 需降级到 DeviceOrientation
  - Android Chrome: 完整支持 WebXR AR
─────────────────────────────
```

| 节点 | 角色 | 说明 |
|------|------|------|
| `m13-threejs-scene` | desktop-engineer | 搭 Three.js 场景 |
| `m14-ar-ui` | ui-ux-designer | 设计 HUD UI |

→ 并行 2 个节点

### 第 3 批

| 节点 | 角色 | 说明 |
|------|------|------|
| `m14-3d-arrow` | desktop-engineer | 等 threejs-scene 完成 |
| `m14-nav-page` | desktop-engineer | 等 3d-arrow + ar-ui → 同角色合并为一个 goal |

### 第 4 批

| 节点 | 角色 | 说明 |
|------|------|------|
| `m14-arch-review` | architect (back) | 后置审核 |

---

## Step 4：完整性门控

每个 Agent 返回后校验：

- `m13-webxr-presearch` → `research/webxr-compatibility.md` ✅ 存在且 > 0 字节
- `m13-threejs-scene` → `src/ar/scene.ts` ✅ 存在
- `m14-ar-ui` → `contracts/design/ar-hud-tokens.json` ✅ 存在
- ...

**发现 bug（qa 阶段）:** 门禁不在此处触发，见 G3

---

## Step 5：失败处理

假设 `m13-webxr-presearch` 超时未返回（stall > 10 分钟）:
1. 终止该 Agent
2. 标记 FAILED
3. 告知用户
4. 不阻断后续批次 — 继续派发下一个已知信息能跑的节点

---

## G3 质量门禁

qa-engineer 拿到全部交付后：

1. 运行所有测试
2. 发现 ARNav.vue 的 Three.js 场景在 Android 低端机上帧率 < 15fps
3. → 自动创建修复任务派给 desktop-engineer
4. desktop-engineer 优化后 qa 重新验证
5. 验证通过 → G3 ✅

---

## G4 交付门禁

devops-engineer 拿到全部交付后：

1. 检查 DEPLOY.md ✅
2. 检查 .env.example ✅
3. 检查 contracts/ 同步 ✅
4. G0~G3 全部 ✅
5. → G4 ✅

---

## 最终交付

编排内核汇总全部产出，向用户展示：

```
TMC 智慧空间助手 — AR 导航模块已就绪 ✅

新增文件:
  src/ar/scene.ts             — Three.js WebXR 场景
  src/ar/Arrow3D.ts           — 3D 箭头模型
  src/components/ARNav.vue    — AR 导航页面
  research/webxr-compatibility.md
  docs/downgrade-plan.md
  contracts/design/ar-hud-tokens.json

新增依赖:
  three.js  ^0.170.0
  @webxr/polyfill  ^0.5.0

门禁:
  G0 ✅  G1 ✅  G2 ✅  G3 ✅  G4 ✅

演示: 打开 http://localhost:5173/ar-nav
```
