"""Multi-slice / multi-sample comparison tools."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from ..tools.store import get_adata, has_data
from ..tools.style import apply_style, spatial_style, CLUSTER_PALETTE


def tool_detect_slices() -> str:
    if not has_data():
        return "No data loaded."
    adata = get_adata()
    slice_keywords = ["slice", "sample", "batch", "donor", "condition", "timepoint", "stage", "region"]
    found = []
    for col in adata.obs.columns:
        if any(kw in col.lower() for kw in slice_keywords):
            n_cats = adata.obs[col].nunique()
            if 2 <= n_cats <= 20:
                found.append((col, n_cats, sorted(adata.obs[col].unique().astype(str))))
    if not found:
        return "No slice/multi-sample columns detected."
    lines = ["## Detected Slice/Multi-Sample Columns", ""]
    for col, n_cats, cats in found:
        lines.append(f"- **{col}**: {n_cats} categories — {cats[:5]}")
    return "\n".join(lines)


def tool_run_multislice_comparison(slice_key: str = None) -> dict:
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}
    adata = get_adata()
    if slice_key is None:
        for col in ["slice", "sample", "batch", "stage"]:
            if col in adata.obs.columns and 2 <= adata.obs[col].nunique() <= 20:
                slice_key = col
                break
    if slice_key is None or slice_key not in adata.obs.columns:
        return {"figures": {}, "summary": "No valid slice key found. Use detect_slices first."}
    figures = {}
    if "leiden" in adata.obs.columns:
        ct = pd.crosstab(adata.obs[slice_key], adata.obs["leiden"])
        fig_comp = px.bar(ct, barmode="stack", title=f"Cluster Composition by {slice_key}", color_discrete_sequence=CLUSTER_PALETTE)
        apply_style(fig_comp)
        figures["slice_composition"] = fig_comp
    return {"figures": figures, "summary": f"Multislice comparison by `{slice_key}`: {adata.obs[slice_key].nunique()} groups, {adata.n_obs:,} cells."}
