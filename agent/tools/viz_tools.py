"""Spatial visualization tools.

Tools:
  plot_spatial_clusters() — Plotly scatter of spatial coords colored by cluster
  plot_spatial_gene(gene) — Plotly scatter of spatial coords colored by gene expression
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from ..tools.store import get_adata, has_data
from ..tools.style import spatial_style, CLUSTER_PALETTE, CONTINUOUS_SCALE


def _get_spatial_key():
    """Detect spatial key in obsm."""
    adata = get_adata()
    for key in ["spatial", "X_spatial", "spatial_xy"]:
        if key in adata.obsm:
            return key
    for key in adata.obsm.keys():
        if "spatial" in key.lower():
            return key
    raise KeyError("No spatial coordinates in adata.obsm. Keys: " + str(list(adata.obsm.keys())))


def tool_plot_spatial_clusters(cluster_key: str = "leiden") -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    try:
        spat_key = _get_spatial_key()
    except KeyError as e:
        return {"figures": {}, "summary": str(e)}
    coords = adata.obsm[spat_key]
    clusters = adata.obs[cluster_key].values.astype(str)
    df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "Cluster": clusters})
    fig = px.scatter(df, x="x", y="y", color="Cluster", title=f"Spatial distribution — {cluster_key}", color_discrete_sequence=CLUSTER_PALETTE)
    spatial_style(fig)
    return {"figures": {"spatial_clusters": fig}, "summary": "Spatial cluster plot generated."}


def tool_plot_spatial_gene(gene_name: str) -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if gene_name not in adata.var_names:
        close = [g for g in adata.var_names if gene_name.lower() in g.lower()][:5]
        hint = f" Did you mean: {close}" if close else ""
        return {"figures": {}, "summary": f"Gene `{gene_name}` not found.{hint}"}
    try:
        spat_key = _get_spatial_key()
    except KeyError as e:
        return {"figures": {}, "summary": str(e)}
    coords = adata.obsm[spat_key]
    X_slice = adata[:, gene_name].X
    expr = X_slice.toarray().ravel() if hasattr(X_slice, "toarray") else np.array(X_slice).flatten()
    df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], gene_name: expr})
    fig = px.scatter(df, x="x", y="y", color=gene_name, title=f"Spatial expression — {gene_name}", color_continuous_scale=CONTINUOUS_SCALE)
    spatial_style(fig)
    return {"figures": {"spatial_gene": fig}, "summary": f"Spatial expression plot for **{gene_name}** generated."}
