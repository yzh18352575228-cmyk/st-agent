"""Data loading and overview tools."""

import glob
import os
from typing import Optional
import anndata as ad
from ..tools.store import get_adata, set_adata, get_adatas, has_data, add_adata


def tool_load_data(file_path: str) -> str:
    """Load an .h5ad file into the store."""
    try:
        adata = ad.read_h5ad(file_path)
        adata.layers["raw"] = adata.X.copy()
        add_adata(adata, path=file_path)
        n_obs, n_var = adata.shape
        spatial_keys = [k for k in adata.obsm.keys() if "spatial" in k.lower()]
        n_total = len(get_adatas())
        return f"Loaded `{os.path.basename(file_path)}` — {n_obs:,} cells x {n_var:,} genes. ({n_total} file(s) loaded) Spatial key(s): {spatial_keys or 'none in obsm'}"
    except FileNotFoundError:
        return f"File not found: `{file_path}`"
    except Exception as e:
        return f"Failed to read `{file_path}`: {e}"


def tool_load_multiple(glob_pattern: str = "*", file_paths: list[str] | None = None) -> str:
    """Load multiple .h5ad files via glob pattern or explicit path list."""
    if file_paths:
        paths = file_paths
    else:
        paths = sorted(glob.glob(glob_pattern))
        if not paths:
            return f"No .h5ad files found matching `{glob_pattern}`"
    if not paths:
        return "No file paths provided."
    lines = [f"## Loading {len(paths)} files", ""]
    total_cells, failed = 0, 0
    for fp in paths:
        try:
            adata = ad.read_h5ad(fp)
            adata.layers["raw"] = adata.X.copy()
            add_adata(adata, path=fp)
            n_c, n_g = adata.shape
            total_cells += n_c
            fname = os.path.basename(fp)
            stage = ""
            for tag in ["E7.5", "E7.75", "E8.0", "E8.5", "E9.0", "E9.5", "E10.5"]:
                if tag in fname:
                    stage = tag
                    break
            lines.append(f"  `{fname}`: {n_c:,} cells x {n_g:,} genes" + (f" (stage: {stage})" if stage else ""))
        except Exception as e:
            lines.append(f"  `{os.path.basename(fp)}": {e}")
            failed += 1
    lines.append("")
    lines.append(f"- **{len(paths) - failed}** files loaded, **{failed}** failed")
    lines.append(f"- Total: **{total_cells:,}** cells across all files")
    n_loaded = len(get_adatas())
    if n_loaded >= 2:
        lines.append(f"{n_loaded} files loaded. Use `merge_samples` to merge, then `cross_stage_comparison`.")
    elif n_loaded == 1:
        lines.append("1 file loaded. Ready for analysis.")
    return "\n".join(lines)


def tool_get_overview() -> str:
    """Report basic stats. Multi-file aware."""
    if not has_data():
        return "No data loaded."
    adatas = get_adatas()
    primary = get_adata()
    if len(adatas) == 1:
        adata = primary
        lines = [f"## Dataset Overview", f"- Cells/spots: **{adata.n_obs:,}**", f"- Genes: **{adata.n_vars:,}**", f"- `obs` columns: {list(adata.obs.columns[:30])}", f"- `var` columns: {list(adata.var.columns[:30])}", f"- Layers: {list(adata.layers.keys())}", f"- `obsm` keys: {list(adata.obsm.keys())}"]
        spat_keys = [k for k in adata.obsm.keys() if "spatial" in k.lower()]
        if spat_keys:
            lines.append(f"- Spatial coords shape: {adata.obsm[spat_keys[0]].shape}")
        return "\n".join(lines)
    lines = [f"## Multi-File Overview — {len(adatas)} files loaded", ""]
    for path, adata in adatas.items():
        fname = os.path.basename(path)
        stage = ""
        for tag in ["E7.5", "E7.75", "E8.0", "E8.5", "E9.0"]:
            if tag in fname:
                stage = f" [{tag}]"
                break
        lines.append(f"- **{fname}**{stage}: {adata.n_obs:,} cells x {adata.n_vars:,} genes")
    return "\n".join(lines)


def tool_get_cell_stats(obs_column: str = "pct_counts_mt", n_cells: int = 20) -> str:
    """Read real numeric values from adata.obs — zero fabrication."""
    if not has_data():
        return "No data loaded."
    adata = get_adata()
    if obs_column not in adata.obs:
        available = list(adata.obs.columns[:15])
        return f"Column `{obs_column}` not found. Available: {available}"
    vals = adata.obs[obs_column].head(n_cells)
    lines = [f"## {obs_column} — first {n_cells} cells", "", "| Cell | Value |", "|------|-------|"]
    for cell_name, val in vals.items():
        lines.append(f"| {str(cell_name)[:30]} | {float(val):.4f} |")
    lines.append("")
    lines.append(f"*Source: `adata.obs['{obs_column}']` — real data, not LLM-generated.*")
    return "\n".join(lines)
