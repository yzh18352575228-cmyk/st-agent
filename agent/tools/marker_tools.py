"""Marker gene analysis tools.

Tools:
  run_marker_analysis(cluster_key='leiden', n_genes=10, method='wilcoxon') → dotplot + ranked table
"""

import scanpy as sc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from ..tools.store import get_adata, set_adata, has_data
from ..tools.style import apply_style, DIVERGING_SCALE


def tool_run_marker_analysis(cluster_key: str = "leiden", n_genes: int = 10, method: str = "wilcoxon") -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if cluster_key not in adata.obs:
        return {"figures": {}, "summary": f"Cluster key `{cluster_key}` not in adata.obs."}

    sc.tl.rank_genes_groups(adata, groupby=cluster_key, method=method, n_genes=n_genes)
    clusters = adata.obs[cluster_key].unique()
    n_cl = len(clusters)

    # Build ranked gene table
    table_lines = [f"## Marker Genes — {cluster_key}", "", f"Method: {method} | Genes per cluster: {n_genes}", ""]
    for c in sorted(clusters):
        genes = adata.uns["rank_genes_groups"]["names"][c][:n_genes]
        scores = adata.uns["rank_genes_groups"]["scores"][c][:n_genes]
        table_lines.append(f"**Cluster {c}**: {', '.join(genes[:5])}")

    # Dotplot via scanpy
    sc.pl.dotplot(adata, var_names=[adata.uns["rank_genes_groups"]["names"][c][0] for c in sorted(clusters)[:3]], groupby=cluster_key, show=False)

    figures = {}
    summary = "\n".join(table_lines)
    set_adata(adata)
    return {"figures": figures, "summary": summary}
