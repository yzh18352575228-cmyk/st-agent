"""Procedural memory — deterministic rules that fix LLM plans before execution.

Unlike working memory (observational) and session summary (declarative),
procedural memory encodes HOW to do things correctly:
dependency ordering, parameter guards, skip conditions.
"""

from typing import Callable, Any
from dataclasses import dataclass, field


@dataclass
class Procedure:
    """A single procedural rule: condition + action."""
    name: str
    description: str
    condition: Callable[[dict[str, Any]], bool]
    action: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
    priority: int = 5


def _insert_before(plan, target_tool, insert_tool, default_args=None):
    """Insert insert_tool before target_tool in plan. Handle reorder if needed."""
    if default_args is None:
        default_args = {}
    existing_tools = [s["tool"] for s in plan]
    target_idx = next((i for i, s in enumerate(plan) if s["tool"] == target_tool), -1)
    if target_idx == -1:
        return plan
    insert_idx = next((i for i, s in enumerate(plan) if s["tool"] == insert_tool), -1)
    if insert_idx == -1:
        plan.insert(target_idx, {"tool": insert_tool, "args": dict(default_args), "reason": f"[程序性记忆自动插入] {target_tool} 的前置依赖"})
    elif insert_idx > target_idx:
        step = plan.pop(insert_idx)
        plan.insert(target_idx, step)
        step["reason"] = f"[程序性记忆重排序] {target_tool} 的前置依赖，移至{target_tool}之前"
    return plan


def _remove_tools(plan, tool_names):
    return [s for s in plan if s["tool"] not in tool_names]


PROCEDURES: list[Procedure] = [
    Procedure(name="preprocess_before_clustering", description="run_clustering 需要 PCA，若 PCA 不存在则自动插入 run_preprocess", priority=10, condition=lambda snap: (not snap.get("has_pca", False)), action=lambda plan: _insert_before(plan, "run_clustering", "run_preprocess", {"n_hvg": 2000, "n_pcs": 30})),
    Procedure(name="clustering_before_marker", description="run_marker_analysis 需要 leiden 列，若不存在则自动插入 run_clustering", priority=9, condition=lambda snap: (not snap.get("has_leiden", False)), action=lambda plan: _insert_before(plan, "run_marker_analysis", "run_clustering", {"resolution": 0.5})),
    Procedure(name="clustering_before_spatial_clusters", description="plot_spatial_clusters 需要 leiden，若不存在则自动插入 run_clustering", priority=9, condition=lambda snap: (not snap.get("has_leiden", False)), action=lambda plan: _insert_before(plan, "plot_spatial_clusters", "run_clustering", {"resolution": 0.5})),
    Procedure(name="marker_before_enrichment", description="run_enrichment_analysis 需要 marker 基因，若不存在则自动插入 run_marker_analysis", priority=8, condition=lambda snap: (snap.get("has_leiden", False)), action=lambda plan: _insert_before(plan, "run_enrichment_analysis", "run_marker_analysis", {"n_genes": 10})),
    Procedure(name="remove_spatial_tools_if_no_coords", description="无空间坐标时移除所有空间可视化工具", priority=8, condition=lambda snap: (snap.get("loaded", False) and not snap.get("has_spatial", False)), action=lambda plan: _remove_tools(plan, ["plot_spatial_clusters", "plot_spatial_gene", "run_spatial_domain", "run_neighborhood_analysis"])),
    Procedure(name="load_before_any_analysis", description="数据未加载时，任何分析工具前自动插入 load_data", priority=20, condition=lambda snap: (not snap.get("loaded", False)), action=lambda plan: _insert_before(plan, plan[0]["tool"] if plan else "run_qc", "load_data", {}) if plan else plan),
    Procedure(name="qc_before_preprocess", description="run_preprocess 之前需要 run_qc", priority=7, condition=lambda snap: (not snap.get("qc_filtered", False)), action=lambda plan: _insert_before(plan, "run_preprocess", "run_qc", {"min_genes": 200, "min_cells": 3, "max_mito_pct": 20.0})),
]


def apply_procedures(plan, snapshot):
    """Apply procedural rules to fix an LLM-generated plan."""
    if not plan:
        return plan, []
    applied = []
    for proc in sorted(PROCEDURES, key=lambda p: -p.priority):
        try:
            if proc.condition(snapshot):
                before = list(plan)
                plan = proc.action(plan)
                if plan != before:
                    applied.append(proc.name)
        except Exception:
            pass
    return plan, applied
