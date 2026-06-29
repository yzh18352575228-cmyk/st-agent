"""Skill definitions — reusable multi-tool workflows."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Skill:
    """A named, parameterized workflow composed of tool calls."""
    name: str
    display_name: str
    description: str
    steps: list[str]
    default_args: dict[str, dict[str, Any]] = field(default_factory=dict)
    requires: list[str] = field(default_factory=list)


SKILLS: dict[str, Skill] = {
    "basic_pipeline": Skill(
        name="basic_pipeline", display_name="基础分析流程",
        description="从加载到 Marker Gene 的完整基础分析流程",
        steps=["get_overview", "run_qc", "run_preprocess", "run_clustering", "plot_spatial_clusters", "run_marker_analysis"],
        default_args={"run_qc": {"min_genes": 200, "min_cells": 3, "max_mito_pct": 20}, "run_preprocess": {"n_hvg": 2000, "n_pcs": 30}, "run_clustering": {"resolution": 0.5}, "plot_spatial_clusters": {}, "run_marker_analysis": {"n_genes": 10}},
    ),
    "spatial_expression": Skill(
        name="spatial_expression", display_name="基因空间表达分析",
        description="在空间坐标上可视化指定基因的表达分布",
        steps=["plot_spatial_gene"], default_args={"plot_spatial_gene": {"gene_name": None}}, requires=["has_spatial"],
    ),
    "extended_analysis": Skill(
        name="extended_analysis", display_name="扩展分析流程",
        description="空间邻域分析、SVG识别、细胞通讯检测",
        steps=["run_neighborhood_analysis", "run_svg_analysis", "run_cell_communication"],
        default_args={"run_neighborhood_analysis": {}, "run_svg_analysis": {"n_top": 20}, "run_cell_communication": {}}, requires=["has_leiden", "has_spatial"],
    ),
    "cluster_interpretation": Skill(
        name="cluster_interpretation", display_name="聚类结果解释",
        description="对已有聚类结果进行 Marker 分析和富集分析",
        steps=["run_marker_analysis", "run_enrichment_analysis"],
        default_args={"run_marker_analysis": {"n_genes": 10}, "run_enrichment_analysis": {}}, requires=["has_leiden"],
    ),
    "report_generation": Skill(
        name="report_generation", display_name="生成分析报告",
        description="基于当前所有分析结果自动生成 HTML 报告",
        steps=["run_generate_report"], default_args={"run_generate_report": {}},
    ),
    "cross_stage_pipeline": Skill(
        name="cross_stage_pipeline", display_name="跨阶段分析流程",
        description="多文件加载→合并→跨发育阶段对比",
        steps=["load_multiple", "merge_samples", "cross_stage_comparison"],
        default_args={"cross_stage_comparison": {"resolution": 0.8}},
    ),
}


def get_skill(name: str) -> Optional[Skill]:
    return SKILLS.get(name)


def expand_skill(skill: Skill, user_args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    user_args = user_args or {}
    plan = []
    for tool_name in skill.steps:
        args = dict(skill.default_args.get(tool_name, {}))
        if tool_name in user_args:
            args.update(user_args[tool_name])
        plan.append({"tool": tool_name, "args": args, "reason": f"skill:{skill.name}"})
    return plan


def get_skill_descriptions() -> str:
    lines = ["## 可用工作流（Skills）"]
    for name, skill in SKILLS.items():
        req = f"（需要：{', '.join(skill.requires)}）" if skill.requires else ""
        lines.append(f"- {name}: {skill.display_name} — {skill.description}{req}")
    return "\n".join(lines)
