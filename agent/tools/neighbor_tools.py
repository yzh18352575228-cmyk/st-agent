"""Spatial neighborhood analysis tools."""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import squidpy as sq
from ..tools.store import get_adata, set_adata, has_data
from ..tools.style import apply_style, DIVERGING_SCALE, CLUSTER_PALETTE


def tool_run_neighborhood_analysis(cluster_key: str = "leiden", n_rings: int = 1, spatial_key: str = "spatial") -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if spatial_key not in adata.obsm:
        for k in adata.obsm.keys():
            if "spatial" in k.lower():
                spatial_key = k
                break
        else:
            return {"figures": {}, "summary": f"No spatial key found. Available: {list(adata.obsm.keys())}"}
    figures = {}
    sq.gr.spatial_neighbors(adata, spatial_key=spatial_key, n_rings=n_rings, coord_type="generic")
    if "spatial_connectivities" in adata.obsp:
        degrees = np.array(adata.obsp["spatial_connectivities"].sum(axis=1)).flatten()
        fig_degree = go.Figure(go.Histogram(x=degrees, nbinsx=30, marker_color="#4C72B0"))
        apply_style(fig_degree)
        fig_degree.update_layout(title="Spatial Connectivity Degree Distribution", xaxis_title="Degree", yaxis_title="Count", height=300)
        figures["connectivity_degree"] = fig_degree
    if cluster_key in adata.obs:
        try:
            sq.gr.nhood_enrichment(adata, cluster_key=cluster_key)
            if "leiden_nhood_enrichment" in adata.uns:
                z = adata.uns["leiden_nhood_enrichment"]["zscore"]
                clusters = sorted(adata.obs[cluster_key].unique(), key=lambda x: int(x))
                fig_enrich = px.imshow(z, x=clusters, y=clusters, color_continuous_scale=DIVERGING_SCALE, title=f"Cluster Co-localization Enrichment (z-score)", aspect="auto")
                apply_style(fig_enrich)
                fig_enrich.update_layout(height=400)
                figures["enrichment_heatmap"] = fig_enrich
        except Exception:
            pass
    avg_degree = float(np.mean(degrees)) if "spatial_connectivities" in adata.obsp else 0
    summary = f"## Neighborhood Analysis\n- Spatial neighbors built (n_rings={n_rings})\n- Avg degree: {avg_degree:.1f}\n- Figures: {len(figures)}"
    set_adata(adata)
    return {"figures": figures, "summary": summary}
