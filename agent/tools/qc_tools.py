"""Quality control tools.

Tools:
  run_qc(min_genes=200, min_cells=3, max_mito_pct=20) → filter cells/genes, return figures
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scanpy as sc
from ..tools.store import get_adata, set_adata, has_data
from ..tools.style import apply_style, ACCENT_RED, ACCENT_BLUE, ACCENT_GREEN


def tool_run_qc(min_genes: int = 200, min_cells: int = 3, max_mito_pct: float = 20.0, min_counts: int | None = None) -> dict:
    """Run QC on the loaded AnnData and return figures + markdown."""
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    n_before_cells, n_before_genes = adata.shape
    adata.var["mt"] = adata.var_names.str.lower().str.startswith("mt-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True, percent_top=None, log1p=False)
    keep_cell = adata.obs["n_genes_by_counts"] >= min_genes
    keep_cell &= adata.obs["pct_counts_mt"] <= max_mito_pct
    if min_counts is not None:
        keep_cell &= adata.obs["total_counts"] >= min_counts
    adata._inplace_subset_obs(keep_cell)
    sc.pp.filter_genes(adata, min_cells=min_cells)
    n_after_cells, n_after_genes = adata.shape

    # Violin subplot
    fig_violin = make_subplots(rows=1, cols=3, subplot_titles=["Genes per cell", "Total counts", "Mito %"])
    metrics = ["n_genes_by_counts", "total_counts", "pct_counts_mt"]
    colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED]
    for i, (metric, col) in enumerate(zip(metrics, colors)):
        fig_violin.add_trace(go.Violin(y=adata.obs[metric].values, name=metric, line_color=col, box_visible=True, meanline_visible=True), row=1, col=i + 1)
    fig_violin.update_layout(height=350, width=900, showlegend=False, title="QC metrics (post-filter)")
    apply_style(fig_violin)

    # Scatter
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scattergl(x=adata.obs["total_counts"], y=adata.obs["n_genes_by_counts"], mode="markers", marker=dict(size=3, color=adata.obs["pct_counts_mt"], colorscale="Viridis", colorbar=dict(title="Mito %"), showscale=True)))
    apply_style(fig_scatter)
    fig_scatter.update_layout(title="Total counts vs genes per cell", xaxis_title="Total counts", yaxis_title="Genes per cell", height=400)

    # Histogram
    fig_ncounts = go.Figure()
    fig_ncounts.add_trace(go.Histogram(x=adata.obs["total_counts"], nbinsx=80, marker_color=ACCENT_GREEN))
    apply_style(fig_ncounts)
    fig_ncounts.update_layout(title="Total counts distribution (post-filter)", xaxis_title="Total counts", yaxis_title="Cell count", height=300)

    set_adata(adata)
    summary = f"## QC Summary\n- Cells retained: **{n_after_cells:,}** / {n_before_cells:,} ({n_after_cells / n_before_cells * 100:.1f}%)\n- Genes retained: **{n_after_genes:,}** / {n_before_genes:,} ({n_after_genes / n_before_genes * 100:.1f}%)\n- Filters: min_genes>={min_genes}, mito%<={max_mito_pct}%, min_cells>={min_cells}"
    return {"figures": {"qc_violin": fig_violin, "qc_scatter": fig_scatter, "qc_ncounts_hist": fig_ncounts}, "summary": summary}
