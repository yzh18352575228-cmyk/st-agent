"""Biological knowledge annotation via MyGene.info API."""

import json
import numpy as np
import pandas as pd
from ..tools.store import get_adata, has_data


def tool_run_knowledge_annotation(gene_list: list[str] = None, cluster_key: str = "leiden", n_genes: int = 10, species: str = "mouse") -> str:
    if not has_data():
        return "No data loaded."
    adata = get_adata()
    if gene_list is None:
        if "rank_genes_groups" not in adata.uns:
            return "No marker genes found. Run run_marker_analysis first."
        gene_list = []
        for c in sorted(adata.obs[cluster_key].unique())[:3]:
            gene_list.extend(list(adata.uns["rank_genes_groups"]["names"][c][:n_genes]))
        gene_list = list(set(gene_list))[:30]
    if not gene_list:
        return "No genes to annotate."
    import requests
    results = []
    for gene in gene_list[:15]:
        try:
            r = requests.post("https://mygene.info/v3/query", json={"q": gene, "species": species, "fields": "name,symbol,go,summary"}, timeout=10)
            data = r.json()
            if data.get("hits"):
                hit = data["hits"][0]
                results.append(f"- **{gene}**: {hit.get('name', 'N/A')} — {hit.get('summary', 'No summary')[:100]}")
        except Exception:
            results.append(f"- **{gene}**: (annotation unavailable)")
    return "## Gene Knowledge Annotation\n\n" + "\n".join(results) if results else "No annotations found."
