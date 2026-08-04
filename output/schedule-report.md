# Allin-Scheduler 调度计划 — Phase 2 关键路径 · M13→M14 (10 节点)

**节点总数:** 10
**并发数上限:** 5
**stall 超时:** 60 分钟

**前置架构:** m13-02-fallback-plan
**后置架构:** m14-arch-review

## 批次计划

### 第 1 批（共 2 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-05-spatial-db-design` | `backend-engineer` | — | 设计空间数据库 schema（places/path_segments/devices + 多楼层 ... |
| `m13-01-webxr-presearch` | `desktop-engineer` | — | 调研 iOS Safari / Android Chrome / 飞书 / 企微 WebXR 兼容矩... |

### 第 2 批（共 1 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-02-fallback-plan` | `architect` | m13-01-webxr-presearch | 基于兼容性调研，设计 AR→方向提示→2D 三档降级方案 |

### 第 3 批（共 2 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-03-threejs-ar-scene` | `desktop-engineer` | m13-02-fallback-plan | 搭建 Three.js + WebXR 基础 AR 场景，集成 hit-test + dom-ove... |
| `m14-ar-ui-design` | `ui-ux-designer` | m13-02-fallback-plan | 设计 AR 导航 HUD（顶部状态栏/十字指引/底部方向面板/楼层切换） |

### 第 4 批（共 1 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m14-3d-arrow` | `desktop-engineer` | m13-03-threejs-ar-scene | 实现 3D 箭头模型（程序化生成 + 浮动动画 + 指向下一路径点） |

### 第 5 批（共 1 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m13-04-compass-mode` | `desktop-engineer` | m13-02-fallback-plan, m13-05-spatial-db-design | 实现陀螺仪屏幕方向提示模式（iOS Safari 降级方案） |

### 第 6 批（共 1 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m14-ar-nav-page` | `desktop-engineer` | m14-ar-ui-design, m14-3d-arrow, m13-04-compass-mode | 集成 AR 场景 + 3D 箭头 + HUD + 罗盘 → 完整 ARNav.vue |

### 第 7 批（共 1 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m14-arch-review` | `architect` | m14-ar-nav-page | 审核 AR 导航模块，更新 OpenAPI contract + 同步 ADRs |

### 第 8 批（共 1 个节点）

| 节点 | 角色 | 依赖 | 目标摘要 |
|------|------|------|---------|
| `m15-acceptance` | `qa-engineer` | m14-arch-review | P0 验收：4 模式（AR/compass/2D/fallback）+ 跨 IM 兼容 + 性能 |

## DAG 依赖拓扑

```
m13-05-spatial-db-design [backend-engineer]
m13-01-webxr-presearch [desktop-engineer]
  m13-02-fallback-plan [architect] -> m13-01-webxr-presearch
  m13-03-threejs-ar-scene [desktop-engineer] -> m13-02-fallback-plan
  m14-ar-ui-design [ui-ux-designer] -> m13-02-fallback-plan
  m14-3d-arrow [desktop-engineer] -> m13-03-threejs-ar-scene
    m13-04-compass-mode [desktop-engineer] -> m13-02-fallback-plan, m13-05-spatial-db-design
      m14-ar-nav-page [desktop-engineer] -> m14-ar-ui-design, m14-3d-arrow, m13-04-compass-mode
  m14-arch-review [architect] -> m14-ar-nav-page
  m15-acceptance [qa-engineer] -> m14-arch-review
```
