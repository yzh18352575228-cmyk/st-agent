"""Spatially Variable Genes (SVG) via Moran's I."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import squidpy as sq
from ..tools.store import get_adata, set_adata, has_data
from ..tools.style import apply_style, spatial_style, ACCENT_RED, ACCENT_BLUE, CONTINUOUS_SCALE


def tool_run_svg_analysis(n_top: int = 50, spatial_key: str = "spatial") -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if spatial_key not in adata.obsm:
        for k in adata.obsm.keys():
            if "spatial" in k.lower():
                spatial_key = k
                break
        else:
            return {"figures": {}, "summary": f"No spatial key in obsm. Keys: {list(adata.obsm.keys())}"}
    sq.gr.spatial_neighbors(adata, spatial_key=spatial_key, coord_type="generic")
    sq.gr.spatial_autocorr(adata, mode="moran", n_perms=100)
    moran_key = "moranI"
    if moran_key not in adata.uns:
        return {"figures": {}, "summary": "Moran's I analysis produced no results."}
    moran_df = adata.uns[moran_key].copy()
    moran_df = moran_df.sort_values("I", ascending=False)
    top_genes = moran_df.head(n_top)
    figures = {}
    fig_hist = go.Figure(go.Histogram(x=moran_df["I"], nbinsx=50, marker_color=ACCENT_BLUE))
    apply_style(fig_hist)
    fig_hist.update_layout(title=f"Moran's I Distribution (n={len(moran_df)})", xaxis_title="Moran's I", yaxis_title="Gene count", height=300)
    figures["moran_histogram"] = fig_hist
    top_summary = top_genes[["I"]].copy()
    top_summary.index.name = "Gene"
    summary = f"## SVG Analysis (Moran's I)\n- Genes analyzed: {len(moran_df)}\n- Moran's I range: [{moran_df['I'].min():.3f}, {moran_df['I'].max():.3f}]\n- Top {n_top} SVGs:\n\n" + top_summary.head(15).to_markdown()
    set_adata(adata)
    return {"figures": figures, "summary": summary}
