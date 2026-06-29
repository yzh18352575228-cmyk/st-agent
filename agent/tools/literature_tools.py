"""Literature retrieval via PubMed NCBI API."""

import json
from ..tools.store import get_adata, has_data


def tool_run_literature_search(query_genes: list[str] = None, topic: str = None, n_papers: int = 10) -> str:
    if query_genes is None and topic is None and has_data():
        adata = get_adata()
        if "rank_genes_groups" in adata.uns:
            query_genes = list(adata.uns["rank_genes_groups"]["names"]["0"][:5])
    query = topic or " ".join(query_genes[:5]) if query_genes else "spatial transcriptomics"
    import requests
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        r = requests.get(search_url, params={"db": "pubmed", "term": query, "retmax": n_papers, "retmode": "json"}, timeout=10)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return f"No PubMed results found for: {query}"
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        r2 = requests.get(summary_url, params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"}, timeout=10)
        results = r2.json().get("result", {})
        lines = [f"## PubMed Search: {query}", ""]
        for pid in ids:
            info = results.get(pid, {})
            title = info.get("title", "?")
            source = info.get("source", "?")
            pubdate = info.get("pubdate", "?")
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
            lines.append(f"- **{title}** — *{source}* ({pubdate}) [PubMed]({url})")
        return "\n".join(lines)
    except Exception as e:
        return f"PubMed search failed: {e}"
