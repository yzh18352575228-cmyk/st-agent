"""Gene enrichment analysis tools (GO, KEGG, Reactome) via Enrichr API."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from ..tools.store import get_adata, has_data
from ..tools.style import apply_style, CLUSTER_PALETTE


def tool_run_enrichment_analysis(cluster_key: str = "leiden", n_genes: int = 30, db: str = "GO_Biological_Process_2023") -> dict:
    """GO/KEGG/Reactome enrichment on marker genes via Enrichr REST API."""
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if "rank_genes_groups" not in adata.uns:
        return {"figures": {}, "summary": "No marker genes found. Run run_marker_analysis first."}
    import requests
    figures = {}
    clusters = sorted(adata.obs[cluster_key].unique())
    for c in clusters[:6]:
        genes = list(adata.uns["rank_genes_groups"]["names"][c][:n_genes])
        try:
            r = requests.post("https://maayanlab.cloud/Enrichr/addList", files={"list": (None, "\n".join(genes)), "description": (None, f"cluster_{c}")}, timeout=10)
            user_list_id = r.json()["userListId"]
            r2 = requests.get("https://maayanlab.cloud/Enrichr/enrich", params={"userListId": user_list_id, "backgroundType": db}, timeout=15)
            data = r2.json()
            if db in data and data[db]:
                top = data[db][:10]
                terms = [t[1] for t in top]
                scores = [t[4] for t in top]
                fig = go.Figure(go.Bar(x=scores[::-1], y=terms[::-1], orientation="h", marker_color=CLUSTER_PALETTE[:1]))
                apply_style(fig)
                fig.update_layout(title=f"Cluster {c} — {db}", height=350, margin=dict(l=200))
                figures[f"enrichment_cluster_{c}"] = fig
        except Exception:
            pass
    return {"figures": figures, "summary": f"Enrichment analysis ({db}) complete. {len(figures)} clusters processed."}
