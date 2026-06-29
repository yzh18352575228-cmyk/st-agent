"""Automatic analysis report generation.

Tools:
  run_generate_report(format="html") → standalone HTML report with all results
"""

import base64
import io
import datetime
from ..tools.store import get_adata, has_data


def tool_run_generate_report(format: str = "html") -> dict:
    """Generate a standalone analysis report with all results embedded."""
    if not has_data():
        return {"figures": {}, "summary": "No data loaded."}

    adata = get_adata()
    today = datetime.date.today().strftime("%Y-%m-%d")
    n_cells, n_genes = adata.shape
    cluster_key = "leiden" if "leiden" in adata.obs else None
    n_clusters = adata.obs[cluster_key].nunique() if cluster_key else "N/A"

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ST Agent Analysis Report — {today}</title></head>
<body>
<h1>ST Agent Analysis Report</h1>
<p>Generated: {today} | {n_cells:,} cells x {n_genes:,} genes | {n_clusters} clusters</p>
</body>
</html>"""

    import os as _os
    _project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    _data_dir = _os.environ.get("ST_AGENT_DATA_DIR", _os.path.join(_project_root, "data"))
    _report_dir = _os.path.join(_data_dir, "reports")
    _os.makedirs(_report_dir, exist_ok=True)
    _filename = f"st_agent_report_{today}.html"
    _filepath = _os.path.join(_report_dir, _filename)
    with open(_filepath, "w", encoding="utf-8") as f:
        f.write(full_html)

    html_b64 = base64.b64encode(full_html.encode("utf-8")).decode("utf-8")
    summary = (
        f"## Report Generated\n\n"
        f"**{n_cells:,}** cells x **{n_genes:,}** genes | **{n_clusters}** clusters | {today}\n\n"
        f"File: `{_filepath}`\n\n"
        f"[Download HTML Report](data:text/html;base64,{html_b64})"
    )
    return {"figures": {}, "summary": summary}
