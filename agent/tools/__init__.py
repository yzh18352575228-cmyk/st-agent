"""Tool registry — map tool name to callable, with signatures for the LLM."""

from ..tools.data_tools import tool_load_data, tool_get_overview
from ..tools.qc_tools import tool_run_qc
from ..tools.preprocess_tools import tool_run_preprocess
from ..tools.cluster_tools import tool_run_clustering
from ..tools.viz_tools import tool_plot_spatial_clusters, tool_plot_spatial_gene
from ..tools.marker_tools import tool_run_marker_analysis
from ..tools.neighbor_tools import tool_run_neighborhood_analysis
from ..tools.svg_tools import tool_run_svg_analysis
from ..tools.communication_tools import tool_run_cell_communication
from ..tools.enrichment_tools import tool_run_enrichment_analysis
from ..tools.slice_tools import tool_detect_slices, tool_run_multislice_comparison
from ..tools.knowledge_tools import tool_run_knowledge_annotation
from ..tools.literature_tools import tool_run_literature_search
from ..tools.multi_tools import tool_merge_samples, tool_cross_stage_comparison
from ..tools.data_tools import tool_load_multiple, tool_get_cell_stats
from ..tools.spatial_domain_tools import tool_run_spatial_domain
from ..tools.report_tools import tool_run_generate_report
from ..tools.store import get_cached_figures as _get_cached_figs

TOOL_REGISTRY: dict[str, dict] = {
    "load_data": {
        "fn": tool_load_data,
        "sig": "load_data(file_path: str) → str",
        "desc": "Load .h5ad spatial transcriptomics file. Required first step.",
    },
    "get_overview": {
        "fn": tool_get_overview,
        "sig": "get_overview() → str",
        "desc": "Print dataset dimensions, obs/var/layers/obsm keys overview.",
    },
    "get_cell_stats": {
        "fn": tool_get_cell_stats,
        "sig": "get_cell_stats(obs_column='pct_counts_mt', n_cells=20) → str",
        "desc": "Read real cell-level metrics from data (e.g. mito%, gene counts). Returns real values table — no fabrication.",
    },
    "run_qc": {
        "fn": tool_run_qc,
        "sig": "run_qc(min_genes=200, min_cells=3, max_mito_pct=20.0) → str",
        "desc": "Filter cells/genes, generate QC violin+scatter+hist figures.",
    },
    "run_preprocess": {
        "fn": tool_run_preprocess,
        "sig": "run_preprocess(n_hvg=2000, n_pcs=30) → str",
        "desc": "Normalize, log1p, HVG, scale, PCA. Generates HVG scatter + elbow plot.",
    },
    "run_clustering": {
        "fn": tool_run_clustering,
        "sig": "run_clustering(resolution=1.0, n_neighbors=15) → str",
        "desc": "Build UMAP, run Leiden clustering. Generates UMAP plot + cluster sizes.",
    },
    "plot_spatial_clusters": {
        "fn": tool_plot_spatial_clusters,
        "sig": "plot_spatial_clusters(cluster_key='leiden') → str",
        "desc": "Plot cell/spot positions colored by cluster assignment.",
    },
    "plot_spatial_gene": {
        "fn": tool_plot_spatial_gene,
        "sig": "plot_spatial_gene(gene_name: str) → str",
        "desc": "Plot cell/spot positions colored by expression of given gene.",
    },
    "run_marker_analysis": {
        "fn": tool_run_marker_analysis,
        "sig": "run_marker_analysis(cluster_key='leiden', n_genes=10, method='wilcoxon') → str",
        "desc": "Rank marker genes per cluster. Generates dotplot + ranked gene table.",
    },
    "run_neighborhood_analysis": {
        "fn": tool_run_neighborhood_analysis,
        "sig": "run_neighborhood_analysis(cluster_key='leiden', n_rings=1) → str",
        "desc": "Spatial neighbors graph + cluster co-localization enrichment heatmap + connectivity degree plot.",
    },
    "run_svg_analysis": {
        "fn": tool_run_svg_analysis,
        "sig": "run_svg_analysis(n_top=50) → str",
        "desc": "Identify spatially variable genes (Moran's I). Generates histogram, top SVG table, spatial plots.",
    },
    "run_cell_communication": {
        "fn": tool_run_cell_communication,
        "sig": "run_cell_communication(cluster_key='leiden', n_perms=200, alpha=0.05) → str",
        "desc": "Infer ligand-receptor cell communication between clusters (squidpy ligrec + OmniPath). Generates LR heatmap + top pairs.",
    },
    "run_enrichment_analysis": {
        "fn": tool_run_enrichment_analysis,
        "sig": "run_enrichment_analysis(cluster_key='leiden', n_genes=30, db='GO_Biological_Process_2023') → str",
        "desc": "GO/KEGG/Reactome enrichment on marker genes via Enrichr API. Generates bar charts per cluster.",
    },
    "detect_slices": {
        "fn": tool_detect_slices,
        "sig": "detect_slices() → str",
        "desc": "Auto-detect multi-slice/multi-sample columns in the dataset. Reports available slice keys for comparison.",
    },
    "run_multislice_comparison": {
        "fn": tool_run_multislice_comparison,
        "sig": "run_multislice_comparison(slice_key=None) → str",
        "desc": "Compare cluster composition, UMAP, and cell counts across slices/samples/timepoints. Auto-detects slice key.",
    },
    "run_knowledge_annotation": {
        "fn": tool_run_knowledge_annotation,
        "sig": "run_knowledge_annotation(gene_list=None, cluster_key='leiden', species='mouse') → str",
        "desc": "Annotate marker genes with GO functions, pathways, and summaries from MyGene.info. Provides biological context.",
    },
    "run_literature_search": {
        "fn": tool_run_literature_search,
        "sig": "run_literature_search(query_genes=None, topic=None, n_papers=10) → str",
        "desc": "Search PubMed for spatial transcriptomics papers related to marker genes or a topic. Returns paper titles, journals, links.",
    },
    "load_multiple": {
        "fn": tool_load_multiple,
        "sig": "load_multiple(glob_pattern='./data/*.h5ad', file_paths=None) → str",
        "desc": "Load multiple .h5ad files via glob pattern. Shows per-file summary and detects stages. First step for multi-sample analysis.",
    },
    "merge_samples": {
        "fn": tool_merge_samples,
        "sig": "merge_samples(batch_correct=False) → str",
        "desc": "Merge all loaded .h5ad files into one dataset with sample/stage labels. Required before cross_stage_comparison.",
    },
    "cross_stage_comparison": {
        "fn": tool_cross_stage_comparison,
        "sig": "cross_stage_comparison(cluster_key='leiden', stage_key='stage', resolution=1.0) → str",
        "desc": "Compare clusters across developmental stages. Joint UMAP + composition bar + stage×cluster heatmap.",
    },
    "run_spatial_domain": {
        "fn": tool_run_spatial_domain,
        "sig": "run_spatial_domain(n_domains=None, resolution=1.0) → str",
        "desc": "Detect anatomically coherent spatial domains via graph-based Leiden on spatial neighbors. Generates domain map + sizes.",
    },
    "run_generate_report": {
        "fn": tool_run_generate_report,
        "sig": "run_generate_report(format='html') → str",
        "desc": "Generate a standalone HTML analysis report with all results and embedded figures. Downloadable as single .html file.",
    },
    "get_cached_figures": {
        "fn": lambda tool_name=None: str(_get_cached_figs(tool_name)),
        "sig": "get_cached_figures(tool_name=None) → str",
        "desc": "Return cached figure paths from previous analyses. Use when user says 'show me the figure again' to avoid re-computation.",
    },
}


def get_tool_descriptions() -> str:
    """Return formatted tool descriptions for the LLM system prompt."""
    lines = []
    for name, meta in TOOL_REGISTRY.items():
        lines.append(f"- **{name}**({meta['sig']}) — {meta['desc']}")
    return "\n".join(lines)


def execute_tool(name: str, args: dict):
    """Look up and execute a tool by name. Returns str or dict with figures."""
    if name not in TOOL_REGISTRY:
        return f"❌ Unknown tool: `{name}`. Available: {list(TOOL_REGISTRY.keys())}"
    fn = TOOL_REGISTRY[name]["fn"]
    try:
        return fn(**args)
    except Exception as e:
        return f"❌ Tool `{name}` raised error: {e}"
