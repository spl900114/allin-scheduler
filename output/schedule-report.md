# Allin-Scheduler 调度计划 — Phase 2 AR 导航模块

**节点总数:** 7
**并行数上限:** 5
**stall 超时:** 10 分钟

**前置架构:** m13-arch-plan
**后置架构:** m14-arch-review

## 批次计划

### 第 1 批 (共 1 个节点)

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-webxr-presearch` | `desktop-engineer` | — | 调研 iOS Safari 和 Android Chrome 的 WebXR 兼容性，输出兼容矩阵 |

### 第 2 批 (共 1 个节点)

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-arch-plan` | `architect` | m13-webxr-presearch | 基于兼容性调研，设计 WebXR 降级方案（AR→方向提示→2D 三档），输出设计文档 |

### 第 3 批 (共 2 个节点)

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-threejs-scene` | `desktop-engineer` | m13-arch-plan | 搭建 Three.js 基础 3D 场景，集成 WebXR API，实现 AR 会话初始化 |
| `m14-ar-ui` | `ui-ux-designer` | m13-arch-plan | 设计 AR 导航页面的 HUD 叠加 UI（上方状态栏、下方控制条、模式切换按钮） |

### 第 4 批 (共 1 个节点)

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m14-3d-arrow` | `desktop-engineer` | m13-threejs-scene | 实现程序化 3D 箭头模型（起点/拐点/终点三种样式），带浮动动画效果 |

### 第 5 批 (共 1 个节点)

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m14-nav-page` | `desktop-engineer` | m14-3d-arrow, m14-ar-ui | 将箭头模型 + AR 场景 + HUD UI 集成为完整的 AR 导航页面组件 ARNav.vue |

### 第 6 批 (共 1 个节点)

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m14-arch-review` | `architect` | m14-nav-page | 审核 AR 导航模块的交付物，确认契约一致性，更新 contracts/ 中的接口定义 |

## DAG 依赖拓扑

```
m13-webxr-presearch [desktop-engineer]
  m13-arch-plan [architect] ← m13-webxr-presearch
  m13-threejs-scene [desktop-engineer] ← m13-arch-plan
  m14-ar-ui [ui-ux-designer] ← m13-arch-plan
  m14-3d-arrow [desktop-engineer] ← m13-threejs-scene
    m14-nav-page [desktop-engineer] ← m14-3d-arrow, m14-ar-ui
  m14-arch-review [architect] ← m14-nav-page
```
