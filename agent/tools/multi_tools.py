"""Multi-file / cross-stage analysis tools."""

import os, re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import scanpy as sc
import anndata as ad
from ..tools.store import get_adatas, get_adata, has_data, set_adata
from ..tools.style import apply_style, CLUSTER_PALETTE


def tool_merge_samples(batch_correct: bool = False) -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adatas = get_adatas()
    if len(adatas) < 2:
        return {"figures": {}, "summary": f"Only {len(adatas)} file(s) loaded. Need at least 2 to merge."}
    paths = list(adatas.keys())
    common_genes = None
    for p in paths:
        genes = set(adatas[p].var_names)
        common_genes = genes if common_genes is None else common_genes & genes
    common_genes = sorted(common_genes)[:8000]
    to_concat = []
    for p in paths:
        a = adatas[p][:, common_genes].copy()
        fname = os.path.basename(p)
        stage = ""
        for tag in ["E7.5", "E7.75", "E8.0", "E8.5", "E9.0"]:
            if tag in fname:
                stage = tag
                break
        a.obs["sample"] = fname[:20]
        a.obs["stage"] = stage or "unknown"
        to_concat.append(a)
    merged = ad.concat(to_concat, join="inner", index_unique="-")
    set_adata(merged, path="merged")
    return {"figures": {}, "summary": f"Merged {len(paths)} files: {merged.n_obs:,} cells, {merged.n_vars:,} genes. Stages: {sorted(merged.obs['stage'].unique())}"}


def tool_cross_stage_comparison(cluster_key: str = "leiden", stage_key: str = "stage", resolution: float = 1.0) -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if stage_key not in adata.obs:
        return {"figures": {}, "summary": f"Stage key `{stage_key}` not found. Run merge_samples first."}
    figures = {}
    stages = sorted(adata.obs[stage_key].unique())
    if len(stages) < 2:
        return {"figures": {}, "summary": f"Only {len(stages)} stage(s) found. Need at least 2 for comparison."}
    sc.pp.pca(adata, n_comps=30)
    sc.pp.neighbors(adata)
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=resolution)
    df = pd.DataFrame({"UMAP1": adata.obsm["X_umap"][:, 0], "UMAP2": adata.obsm["X_umap"][:, 1], "Stage": adata.obs[stage_key].values})
    fig_umap = px.scatter(df, x="UMAP1", y="UMAP2", color="Stage", title="Joint UMAP by Stage", color_discrete_sequence=CLUSTER_PALETTE)
    apply_style(fig_umap)
    figures["joint_umap_stage"] = fig_umap
    counts = adata.obs[stage_key].value_counts()
    summary = f"## Cross-Stage Comparison\n- Stages: {stages}\n- Cells per stage: {dict(counts)}"
    return {"figures": figures, "summary": summary}
