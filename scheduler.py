#!/usr/bin/env python3
"""
Allin-Scheduler — 通用 AI Agent 多角色编排调度器

不依赖任何特定 AI 框架，纯 Python 标准库。
解析 DAG YAML → 按依赖拓扑排序 → 按角色分组 → 输出调度计划。

用法:
  python scheduler.py dag.yaml               # 解析 DAG 生成调度计划
  python scheduler.py dag.yaml --report       # 生成 markdown 报告
  python scheduler.py dag.yaml --validate     # 仅验证 DAG 拓扑（无循环检测）
"""

import json
import os
import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("""
    [ERROR] PyYAML 未安装。请运行:
      pip install pyyaml
    或使用 Python 3.11+ 内置的 tomllib 替代。
    """, file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────
# DAG 模型
# ──────────────────────────────────────────────

ALL_ROLES = [
    "product-manager", "architect", "backend-engineer",
    "desktop-engineer", "ui-ux-designer", "qa-engineer", "devops-engineer",
]

MAX_CONCURRENCY_DEFAULT = 5
STALL_TIMEOUT_DEFAULT = 10  # minutes


class DAGNode:
    """单个 DAG 任务节点"""

    def __init__(self, data: dict, dag: "DAG"):
        self.node_id = data["node_id"]
        self.assignee = data.get("assignee", "unknown")
        self.arch_phase = data.get("arch_phase", "")
        self.parents = data.get("parents", [])
        self.goal = data.get("goal", "")
        self.context = data.get("context", "")
        self.output_path = data.get("output_path", "")
        self.verification = data.get("verification", "文件存在且非空")
        self._dag = dag

    def __repr__(self):
        return f"<{self.node_id} ({self.assignee}) parents={self.parents}>"


class DAG:
    """有向无环图 — 任务依赖拓扑"""

    def __init__(self, data: dict):
        self.name = data.get("name", "unnamed")
        self.max_concurrency = data.get("max_concurrency", MAX_CONCURRENCY_DEFAULT)
        self.stall_timeout = data.get("stall_timeout_minutes", STALL_TIMEOUT_DEFAULT)
        raw_nodes = data.get("nodes", [])
        self.nodes = {n["node_id"]: DAGNode(n, self) for n in raw_nodes}

    def validate(self) -> list[str]:
        """返回错误列表，空 = 验证通过"""
        errors = []

        # 1. 检查所有 parent 引用存在
        for nid, node in self.nodes.items():
            for p in node.parents:
                if p not in self.nodes:
                    errors.append(f"[{nid}] 依赖 parent '{p}' 不存在")

        # 2. 检查循环依赖
        visited = set()
        in_stack = set()

        def dfs(nid):
            if nid in in_stack:
                cycle = []
                for v in reversed(list(visited)):
                    cycle.append(v)
                    if v == nid:
                        break
                errors.append(f"[CYCLE] 循环依赖: {' → '.join(reversed(cycle))} → {nid}")
                return
            if nid in visited:
                return
            visited.add(nid)
            in_stack.add(nid)
            node = self.nodes.get(nid)
            if node:
                for p in node.parents:
                    dfs(p)
            in_stack.discard(nid)

        for nid in self.nodes:
            dfs(nid)

        # 3. 检查角色是否在已知列表中
        for nid, node in self.nodes.items():
            if node.assignee not in ALL_ROLES:
                errors.append(f"[{nid}] 角色 '{node.assignee}' 不在已知角色列表中")

        return errors

    def topo_sort(self) -> list[str]:
        """拓扑排序，按依赖关系排序节点 ID"""
        in_degree = {nid: len(node.parents) for nid, node in self.nodes.items()}
        graph = {nid: [] for nid in self.nodes}
        for nid, node in self.nodes.items():
            for p in node.parents:
                graph[p].append(nid)

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            queue.sort(key=lambda nid: self._estimate_weight(nid), reverse=True)
            current = queue.pop(0)
            result.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            remaining = set(self.nodes.keys()) - set(result)
            raise ValueError(f"DAG 拓扑排序不完整: 剩余 {remaining} 节点，可能存在循环依赖")
        return result

    def _estimate_weight(self, node_id: str) -> int:
        """估算节点工作量（不精确，仅用于排序）"""
        node = self.nodes[node_id]
        return len(node.goal)  # goal 越长 ≈ 工作量越大

    def plan_batches(self) -> list[list[str]]:
        """按派发批次分组"""
        sorted_ids = self.topo_sort()
        node_map = self.nodes
        assigned = set()
        batches = []

        while len(assigned) < len(sorted_ids):
            # 找出所有 parent 都已分配的节点
            ready = [
                nid for nid in sorted_ids
                if nid not in assigned
                and all(p in assigned for p in node_map[nid].parents)
            ]
            if not ready:
                raise ValueError("DAG 死锁: 有节点永远无法满足依赖")

            batch = []
            # 按角色分组，同角色串行的放入同一个 batch
            role_count = {}
            for nid in ready:
                role = node_map[nid].assignee
                if role_count.get(role, 0) < 1:  # 同角色最多 1 个 per batch
                    batch.append(nid)
                    role_count[role] = role_count.get(role, 0) + 1
                    if len(batch) >= self.max_concurrency:
                        break

            assigned.update(batch)
            batches.append(batch)

        return batches

    def extract_arch_phases(self) -> dict:
        """提取 architect 的前后置阶段"""
        result = {"front": [], "back": []}
        for nid, node in self.nodes.items():
            if node.assignee == "architect":
                if node.arch_phase == "back":
                    result["back"].append(nid)
                else:
                    result["front"].append(nid)
        return result


# ──────────────────────────────────────────────
# 打印 / 报告
# ──────────────────────────────────────────────

def format_schedule_report(dag: DAG, batches: list[list[str]], errors: list[str]) -> str:
    """生成 Markdown 格式的调度报告"""
    lines = []
    lines.append(f"# Allin-Scheduler 调度计划 — {dag.name}")
    lines.append("")
    lines.append(f"**节点总数:** {len(dag.nodes)}")
    lines.append(f"**并行数上限:** {dag.max_concurrency}")
    lines.append(f"**stall 超时:** {dag.stall_timeout} 分钟")
    lines.append("")

    arch = dag.extract_arch_phases()
    if arch["front"]:
        lines.append(f"**前置架构:** {', '.join(arch['front'])}")
    if arch["back"]:
        lines.append(f"**后置架构:** {', '.join(arch['back'])}")
    lines.append("")

    if errors:
        lines.append("## ⚠️ 验证警告")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    lines.append("## 批次计划")
    lines.append("")
    for i, batch in enumerate(batches, 1):
        lines.append(f"### 第 {i} 批 (共 {len(batch)} 个节点)")
        lines.append("")
        lines.append("| 节点 | 角色 | 依赖 | 目标摘要 |")
        lines.append("|------|------|------|---------|")
        for nid in batch:
            node = dag.nodes[nid]
            p = ", ".join(node.parents) if node.parents else "—"
            goal = node.goal[:50] + "..." if len(node.goal) > 50 else node.goal
            lines.append(f"| `{nid}` | `{node.assignee}` | {p} | {goal} |")
        lines.append("")

    lines.append("## DAG 依赖拓扑")
    lines.append("")
    lines.append("```")
    for nid in dag.topo_sort():
        node = dag.nodes[nid]
        indent = "  " * (len(node.parents) if node.parents else 0)
        p = f" ← {', '.join(node.parents)}" if node.parents else ""
        lines.append(f"{indent}{nid} [{node.assignee}]{p}")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    dag_file = sys.argv[1]
    mode = "plan"
    if "--report" in sys.argv:
        mode = "report"
    if "--validate" in sys.argv:
        mode = "validate"

    if not os.path.exists(dag_file):
        print(f"[ERROR] 文件不存在: {dag_file}", file=sys.stderr)
        sys.exit(1)

    with open(dag_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    dag = DAG(data)

    # 验证
    errors = dag.validate()
    if errors:
        print("=" * 60)
        print("  ⚠️  DAG 验证发现以下问题:")
        print("=" * 60)
        for e in errors:
            print(f"  • {e}")
        print()
        if mode == "validate":
            sys.exit(1)
    else:
        print("✅ DAG 验证通过（无循环依赖、所有 parent 引用有效）")
        print()

    if mode == "validate":
        return

    # 拓扑排序 & 批次
    try:
        batches = dag.plan_batches()
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if mode == "report":
        report = format_schedule_report(dag, batches, errors)
        report_path = "output/schedule-report.md"
        os.makedirs("output", exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📄 报告已写入 {report_path}")
        print()
        print(report[:2000])
        if len(report) > 2000:
            print("... (完整报告见文件)")
    else:
        # 默认 plan 模式
        print("=" * 60)
        print(f"  📋 {dag.name} — 调度计划")
        print("=" * 60)
        print(f"  总节点: {len(dag.nodes)} | 并行上限: {dag.max_concurrency}")
        print()
        for i, batch in enumerate(batches, 1):
            print(f"  ───── 第 {i} 批 ({len(batch)} 个节点) ─────")
            for nid in batch:
                node = dag.nodes[nid]
                p = f" [等待: {', '.join(node.parents)}]" if node.parents else ""
                print(f"    [{node.assignee:20s}] {nid}{p}")
            print()

        # 输出 JSON 供外部程序使用
        plan_json = {
            "name": dag.name,
            "node_count": len(dag.nodes),
            "max_concurrency": dag.max_concurrency,
            "stall_timeout": dag.stall_timeout,
            "batches": batches,
            "validation_errors": errors,
        }
        os.makedirs("output", exist_ok=True)
        with open("output/schedule-plan.json", "w", encoding="utf-8") as f:
            json.dump(plan_json, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON 计划已写入 output/schedule-plan.json")


if __name__ == "__main__":
    main()
