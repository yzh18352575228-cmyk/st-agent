"""Working memory — injects data state awareness into the planner."""

from typing import Any

_store = None


def _get_store():
    global _store
    if _store is None:
        from agent.tools import store as st
        _store = st
    return _store


def get_adata_snapshot() -> dict[str, Any]:
    """Extract key state information from the current AnnData."""
    store = _get_store()
    if not store.has_data():
        return {"loaded": False}
    adata = store.get_adata()
    if adata is None:
        return {"loaded": False}
    has_spatial = any("spatial" in k.lower() for k in adata.obsm.keys())
    completed_raw = adata.uns.get("completed_steps", [])
    completed_steps = list(completed_raw) if completed_raw else []
    return {
        "loaded": True,
        "n_obs": adata.n_obs,
        "n_vars": adata.n_vars,
        "has_spatial": has_spatial,
        "has_pca": "X_pca" in adata.obsm,
        "has_umap": "X_umap" in adata.obsm,
        "has_leiden": "leiden" in adata.obs.columns,
        "has_cell_type": "cell_type" in adata.obs.columns,
        "completed_steps": completed_steps,
        "obs_columns": list(adata.obs.columns),
        "n_hvg": adata.uns.get("n_hvg", None),
        "qc_filtered": "run_qc" in completed_steps,
        "data_path": store.get_primary_path(),
    }


def format_snapshot_for_prompt(snapshot: dict[str, Any]) -> str:
    """Format a snapshot dict into a Chinese text block for the planner prompt."""
    if not snapshot.get("loaded", False):
        return "=== 当前数据状态 ===\n尚未加载任何数据。\n若用户要求分析，必须先规划 load_data。\n=================="
    steps_str = ", ".join(snapshot["completed_steps"]) if snapshot["completed_steps"] else "无"
    lines = [
        "=== 当前数据状态 ===",
        f"数据已加载：是 | 路径：{snapshot.get('data_path', '?')}",
        f"细胞数：{snapshot['n_obs']:,} | 基因数：{snapshot['n_vars']:,}",
        f"已完成步骤：{steps_str}",
        f"空间坐标：{'有' if snapshot['has_spatial'] else '无'} | PCA：{'有' if snapshot['has_pca'] else '无'} | UMAP：{'有' if snapshot['has_umap'] else '无'} | Leiden聚类：{'有' if snapshot['has_leiden'] else '无'}",
    ]
    if snapshot.get("n_hvg"):
        lines.append(f"HVG数：{snapshot['n_hvg']}")
    if snapshot.get("qc_filtered"):
        lines.append("QC过滤：已完成")
    lines.append("==================")
    return "\n".join(lines)


def mark_step_completed(tool_name: str) -> None:
    """Append tool_name to adata.uns['completed_steps']. Idempotent."""
    store = _get_store()
    if not store.has_data():
        return
    adata = store.get_adata()
    if adata is None:
        return
    current = list(adata.uns.get("completed_steps", []))
    if tool_name not in current:
        current.append(tool_name)
        adata.uns["completed_steps"] = current
