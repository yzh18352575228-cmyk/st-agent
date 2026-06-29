"""Clustering tools.

Tools:
  run_clustering(resolution=1.0, n_neighbors=15) → UMAP + Leiden
"""

import scanpy as sc
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from ..tools.store import get_adata, set_adata, has_data
from ..tools.style import apply_style, CLUSTER_PALETTE


def tool_run_clustering(resolution: float = 1.0, n_neighbors: int = 15, n_pcs: int | None = None) -> dict:
    """Build UMAP, run Leiden clustering."""
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if "X_pca" not in adata.obsm:
        return {"figures": {}, "summary": "No PCA found. Run run_preprocess first."}

    actual_pcs = min(n_pcs or adata.obsm["X_pca"].shape[1], adata.obsm["X_pca"].shape[1])
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=actual_pcs)
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=resolution)

    n_clusters = adata.obs["leiden"].nunique()
    figures = {}

    # UMAP
    df_umap = pd.DataFrame({"UMAP1": adata.obsm["X_umap"][:, 0], "UMAP2": adata.obsm["X_umap"][:, 1], "Cluster": adata.obs["leiden"].values.astype(str)})
    fig_umap = px.scatter(df_umap, x="UMAP1", y="UMAP2", color="Cluster", title=f"Leiden Clusters (resolution={resolution})", color_discrete_sequence=CLUSTER_PALETTE)
    apply_style(fig_umap)
    figures["umap_clusters"] = fig_umap

    # Cluster sizes
    sizes = adata.obs["leiden"].value_counts().sort_index()
    fig_sizes = go.Figure(go.Bar(x=sizes.index.astype(str), y=sizes.values, marker_color=CLUSTER_PALETTE[:len(sizes)]))
    apply_style(fig_sizes)
    fig_sizes.update_layout(title="Cluster Sizes", xaxis_title="Cluster", yaxis_title="Cells")
    figures["cluster_sizes"] = fig_sizes

    set_adata(adata)
    summary = f"## Clustering\n- Resolution: {resolution}\n- Clusters: {n_clusters}\n- Sizes: {dict(sizes)}"
    return {"figures": figures, "summary": summary}
