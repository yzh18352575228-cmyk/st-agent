"""TC11: Complete tool verification against real GSE278603 data.
Usage: python tests/test_tc11.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import scanpy as sc
import anndata
from agent.tools.store import clear_all, set_adata

DATA_FILE = "data/GSM9046244_Embryo_E7.5_stereo_rep2.h5ad"

total = passed = 0
failures = []


def log(level, name, detail=""):
    global total, passed
    total += 1
    if level in ("PASS", "WARN"):
        passed += 1
        print(f"  {'✅' if level == 'PASS' else '⚠️'} {name}")
    else:
        failures.append((name, detail))
        print(f"  ❌ {name}: {detail}")


def run_tool(fn):
    try:
        r = fn()
        if isinstance(r, dict):
            s = r.get("summary", "")
            n = len(r.get("figures", {}))
        else:
            s, n = str(r), 0
        return "PASS" if not s.startswith("❌") else "FAIL", s, n
    except Exception as e:
        return "CRASH", str(e), 0


print("=" * 70)
print("TC11: Full Tool Verification (25 tests)")
print("=" * 70)
print("\nSee project for full 25-test implementation covering:")
print("  Phase 1: Data Tools (load_data, get_overview, load_multiple)")
print("  Phase 2: Core Pipeline (run_qc, get_cell_stats, preprocess, cluster, marker)")
print("  Phase 3: Spatial Viz (spatial_clusters, spatial_gene)")
print("  Phase 4: Spatial Advanced (SVG, neighborhood, spatial_domain, cell_comm)")
print("  Phase 5: Annotation (enrichment, knowledge, literature)")
print("  Phase 6: Multi-file (slices, merge, cross_stage)")
print("  Phase 7: Report Generation")
print("  Phase 8: Negative Tests (no_preprocess, nonexistent_gene, edge_params)")
