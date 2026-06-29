"""E2E Acceptance Test — executable specification for the ST Agent.

Design philosophy:
  - Each check simulates a real user action
  - Each assertion is a quantifiable acceptance criterion
  - Run after every code change: python e2e_validate.py
  - All = feature complete. Any = keep fixing.

Usage:
  python e2e_validate.py           # full suite
  python e2e_validate.py --quick   # skip slow tools
"""

import sys, os, time, tempfile, shutil, traceback, argparse
import numpy as np
import pandas as pd
import anndata as ad

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

RESULTS = []
TMPDIR = None
DATA_PATHS = []


def check(name, fn):
    t0 = time.time()
    try:
        detail = fn()
        elapsed = time.time() - t0
        RESULTS.append(("PASS", name, f"{elapsed:.1f}s", detail or ""))
        return True
    except Exception as e:
        elapsed = time.time() - t0
        msg = str(e)[:200]
        RESULTS.append(("FAIL", name, f"{elapsed:.1f}s", msg))
        return False


def setup_fixtures():
    global TMPDIR, DATA_PATHS
    TMPDIR = tempfile.mkdtemp(prefix="st_e2e_")
    DATA_PATHS = []
    np.random.seed(42)
    stages = ["E7.5", "E7.75", "E8.0"]
    for stage in stages:
        for rep in ["rep1", "rep2"]:
            n_cells = np.random.randint(150, 250)
            n_genes = 500
            X = np.random.poisson(2, (n_cells, n_genes)).astype(np.float32)
            stage_idx = stages.index(stage)
            X[:, stage_idx * 40:(stage_idx + 1) * 40] += np.random.poisson(8, (n_cells, 40))
            gene_names = [f"Gene_{i}" for i in range(n_genes)]
            for i in range(5):
                gene_names[i] = f"mt-Gene_{i}"
            coords = np.random.randn(n_cells, 2) * 1.5 + np.array([[stage_idx * 3, 0]])
            a = ad.AnnData(X)
            a.var_names = gene_names
            a.obsm["spatial"] = coords.astype(np.float32)
            a.obs["n_genes_by_counts"] = np.random.randint(50, 300, n_cells)
            a.obs["total_counts"] = X.sum(axis=1).A1 if hasattr(X, "A1") else X.sum(axis=1)
            fname = f"GSM9046xxx_Embryo_{stage}_stereo_{rep}.h5ad"
            path = os.path.join(TMPDIR, fname)
            a.write_h5ad(path)
            DATA_PATHS.append(path)
    return f"{len(DATA_PATHS)} files (E7.5x2, E7.75x2, E8.0x2)"


# 29 acceptance steps across 7 phases
# Phase 1: Store & Loading
# Phase 2: Core Pipeline (QC, Preprocess, Cluster, Marker, Spatial)
# Phase 3: Extended Tools (Neighborhood, SVG, Slice)
# Phase 4: Multi-File (Merge, Cross-stage, Spatial Domain)
# Phase 5: Regression (Store API, Tools, Graph, Style)
# Phase 6: LLM Planner (requires API key)
# Phase 6b: Report Generation
# Phase 7: Robustness & Edge Cases
# Full implementation in the project file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()
    print("=" * 70)
    print("  ST Agent - E2E Acceptance Test Suite")
    print("=" * 70)
    print(f"Full implementation: {len(DATA_PATHS)} synthetic samples across 3 stages")
    print("Run 'python tests/e2e_validate.py' for complete 29-step verification")


if __name__ == "__main__":
    main()
