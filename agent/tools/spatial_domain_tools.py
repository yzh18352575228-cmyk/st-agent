"""Spatial domain detection via graph-based Leiden on spatial neighbors."""

import numpy as np
import plotly.express as px
import pandas as pd
import squidpy as sq
from ..tools.store import get_adata, has_data, set_adata
from ..tools.style import spatial_style, CLUSTER_PALETTE


def tool_run_spatial_domain(n_domains: int = None, resolution: float = 1.0, spatial_key: str = "spatial") -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if spatial_key not in adata.obsm:
        for k in adata.obsm.keys():
            if "spatial" in k.lower():
                spatial_key = k
                break
        else:
            return {"figures": {}, "summary": f"No spatial key found. Keys: {list(adata.obsm.keys())}"}
    try:
        sq.gr.spatial_neighbors(adata, spatial_key=spatial_key, coord_type="generic")
    except Exception:
        pass
    if "spatial_connectivities" not in adata.obsp:
        sq.gr.spatial_neighbors(adata, spatial_key=spatial_key, coord_type="generic")
    import scanpy as sc
    sc.tl.leiden(adata, adjacency=adata.obsp["spatial_connectivities"], key_added="spatial_domain", resolution=resolution)
    n_domains = adata.obs["spatial_domain"].nunique()
    figures = {}
    coords = adata.obsm[spatial_key]
    df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "Domain": adata.obs["spatial_domain"].values.astype(str)})
    fig = px.scatter(df, x="x", y="y", color="Domain", title=f"Spatial Domains (resolution={resolution})", color_discrete_sequence=CLUSTER_PALETTE)
    spatial_style(fig)
    figures["spatial_domains"] = fig
    fig_sizes = px.bar(x=adata.obs["spatial_domain"].value_counts().index.astype(str), y=adata.obs["spatial_domain"].value_counts().values, title="Domain Sizes", color_discrete_sequence=CLUSTER_PALETTE)
    figures["domain_sizes"] = fig_sizes
    set_adata(adata)
    return {"figures": figures, "summary": f"Spatial domain detection complete: {n_domains} domains (resolution={resolution})."}
