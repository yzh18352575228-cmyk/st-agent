"""Preprocessing tools.

Tools:
  run_preprocess(n_hvg=2000, n_pcs=30) → normalize, log1p, HVG, scale, PCA
"""

import scanpy as sc
import plotly.graph_objects as go
import numpy as np
from ..tools.store import get_adata, set_adata, has_data
from ..tools.style import apply_style, ACCENT_RED, ACCENT_BLUE


def tool_run_preprocess(n_hvg: int = 2000, n_pcs: int = 30) -> dict:
    """Normalize, log1p, HVG, scale, PCA."""
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if adata.n_obs < 10:
        return {"figures": {}, "summary": f"Too few cells ({adata.n_obs}) for preprocessing."}

    # Early gene filter to save memory
    sc.pp.filter_genes(adata, min_cells=3)
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    # HVG
    try:
        sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor="seurat")
    except Exception:
        sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor="seurat_v3")

    adata.layers["scaled"] = adata[:, adata.var["highly_variable"]].X.copy()
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=n_pcs, svd_solver="arpack")

    figures = {}
    # HVG scatter
    hvg_df = adata.var[["means", "dispersions_norm", "highly_variable"]].copy()
    fig_hvg = go.Figure()
    fig_hvg.add_trace(go.Scatter(x=hvg_df["means"][~hvg_df["highly_variable"]], y=hvg_df["dispersions_norm"][~hvg_df["highly_variable"]], mode="markers", marker=dict(size=2, color="gray"), name="Other"))
    fig_hvg.add_trace(go.Scatter(x=hvg_df["means"][hvg_df["highly_variable"]], y=hvg_df["dispersions_norm"][hvg_df["highly_variable"]], mode="markers", marker=dict(size=2, color=ACCENT_RED), name="HVG"))
    apply_style(fig_hvg)
    fig_hvg.update_layout(title=f"HVG Selection (n={n_hvg})", xaxis_title="Mean expression", yaxis_title="Normalized dispersion", height=400)
    figures["hvg_scatter"] = fig_hvg

    # PCA elbow
    var_ratio = adata.uns["pca"]["variance_ratio"]
    fig_elbow = go.Figure()
    fig_elbow.add_trace(go.Scatter(x=list(range(1, len(var_ratio) + 1)), y=np.cumsum(var_ratio), mode="lines+markers", marker_color=ACCENT_BLUE))
    apply_style(fig_elbow)
    fig_elbow.update_layout(title="PCA Elbow Plot", xaxis_title="PC", yaxis_title="Cumulative variance", height=350)
    figures["pca_elbow"] = fig_elbow

    set_adata(adata)
    summary = f"## Preprocessing\n- HVG: {n_hvg}\n- PCs: {n_pcs}\n- Cumulative variance: {np.cumsum(var_ratio)[n_pcs-1]:.1%}"
    return {"figures": figures, "summary": summary}
