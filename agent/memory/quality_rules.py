"""Quality rules for the checker node.

Each rule checks the output of a specific tool and decides
whether the result is acceptable or needs a retry with adjusted params.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Any


@dataclass
class QualityRule:
    """A quality check for a specific tool's output."""
    tool_name: str
    description: str
    check: Callable[[dict[str, Any], str], tuple[bool, str]]
    fix_args: Optional[Callable[[dict[str, Any]], dict[str, Any]]] = None


QUALITY_RULES: list[QualityRule] = [
    QualityRule(tool_name="run_qc", description="QC 后细胞数不能低于 50",
        check=lambda snap, result: (snap.get("n_obs", 999) >= 50, f"QC后仅剩 {snap.get('n_obs', '?')} 个细胞，阈值过严" if snap.get("n_obs", 999) < 50 else ""),
        fix_args=lambda args: {**args, "min_genes": max(50, args.get("min_genes", 200) // 2), "max_mito_pct": min(50, args.get("max_mito_pct", 20) * 1.5)}),
    QualityRule(tool_name="run_clustering", description="聚类后必须在 obs 中生成 leiden 列",
        check=lambda snap, result: (snap.get("has_leiden", False), "聚类未生成 leiden 列" if not snap.get("has_leiden", False) else ""),
        fix_args=lambda args: {**args, "resolution": min(2.0, args.get("resolution", 0.5) * 1.5)}),
    QualityRule(tool_name="run_preprocess", description="预处理后必须生成 X_pca",
        check=lambda snap, result: (snap.get("has_pca", False), "预处理未生成 PCA 结果" if not snap.get("has_pca", False) else ""),
        fix_args=None),
]


def get_rule(tool_name: str) -> Optional[QualityRule]:
    """Find the quality rule for a given tool. Returns None if no rule exists."""
    for r in QUALITY_RULES:
        if r.tool_name == tool_name:
            return r
    return None
