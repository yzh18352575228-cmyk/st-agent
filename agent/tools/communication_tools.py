"""Cell-cell communication analysis via ligand-receptor interactions."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import squidpy as sq
from ..tools.store import get_adata, has_data
from ..tools.style import apply_style, CLUSTER_PALETTE, DIVERGING_SCALE


def tool_run_cell_communication(cluster_key: str = "leiden", n_perms: int = 200, alpha: float = 0.05) -> dict:
    """Infer ligand-receptor interactions between cell clusters via squidpy ligrec."""
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if cluster_key not in adata.obs:
        return {"figures": {}, "summary": f"Cluster key `{cluster_key}` not in adata.obs."}
    if adata.raw is None:
        for lkey in ["raw", "counts", "raw_counts"]:
            if lkey in adata.layers:
                try:
                    import anndata as ad
                    adata.raw = ad.AnnData(adata.layers[lkey], obs=adata.obs, var=adata.var)
                    break
                except Exception:
                    pass
    if adata.raw is None:
        return {"figures": {}, "summary": "Missing raw counts (adata.raw). Run run_preprocess first."}
    figures = {}
    try:
        sq.gr.ligrec(adata, n_perms=n_perms, cluster_key=cluster_key, use_raw=True, transmitter_params={"categories": "ligand"}, receiver_params={"categories": "receptor"})
    except Exception:
        try:
            sq.gr.ligrec(adata, n_perms=n_perms, cluster_key=cluster_key, use_raw=False, transmitter_params={"categories": "ligand"}, receiver_params={"categories": "receptor"})
        except Exception as e2:
            return {"figures": {}, "summary": f"ligrec failed: {e2}"}
    if "ligrec" not in adata.uns:
        return {"figures": {}, "summary": "Ligand-receptor analysis produced no results."}
    means = adata.uns["ligrec"].get("means")
    pvalues = adata.uns["ligrec"].get("pvalues")
    if means is None or means.empty:
        return {"figures": {}, "summary": "No significant LR interactions found."}
    sig_pairs = []
    if pvalues is not None:
        for (src, tgt), row in pvalues.iterrows():
            sig_genes = row[row < alpha].index.tolist()
            if sig_genes:
                sig_pairs.append({"source": src, "target": tgt, "n_pairs": len(sig_genes), "top_genes": sig_genes[:5]})
    clusters = sorted(adata.obs[cluster_key].unique())
    n_cl = len(clusters)
    matrix = np.zeros((n_cl, n_cl))
    for sp in sig_pairs:
        try:
            si = list(clusters).index(sp["source"])
            ti = list(clusters).index(sp["target"])
            matrix[si, ti] = sp["n_pairs"]
        except ValueError:
            pass
    if matrix.sum() > 0:
        fig_heat = px.imshow(matrix, x=[f"Target {c}" for c in clusters], y=[f"Source {c}" for c in clusters], color_continuous_scale="Viridis", title=f"Ligand-Receptor Interaction Pairs — {cluster_key}", labels=dict(color="# significant LR pairs"), aspect="auto")
        apply_style(fig_heat)
        fig_heat.update_layout(height=450)
        figures["lr_heatmap"] = fig_heat
    top_n = min(10, len(sig_pairs))
    table_lines = [f"## Cell-Cell Communication", f"", f"- Method: squidpy ligrec (OmniPath database, {n_perms} permutations)", f"- Threshold: alpha={alpha}", f"- Significant cluster pairs: {len(sig_pairs)}", f"", f"### Top {top_n} Interacting Pairs", "", "| Source | Target | # LR pairs | Top genes |", "|--------|--------|-----------|-----------|"]
    for sp in sig_pairs[:top_n]:
        table_lines.append(f"| {sp['source']} | {sp['target']} | {sp['n_pairs']} | {', '.join(sp['top_genes'][:4])} |")
    return {"figures": figures, "summary": "\n".join(table_lines)}
