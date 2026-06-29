"""Figure archive — saves every generated figure to disk for MiniMax re-reading.

Directory: {DATA_DIR}/figures/{tool_name}_{figure_name}.png
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.environ.get("ST_AGENT_DATA_DIR", os.path.join(_PROJECT_ROOT, "data"))
FIGURE_DIR = os.path.join(DATA_DIR, "figures")


def save_figures_to_disk(tool_name: str, figures: dict) -> list[str]:
    """Save all figures from a tool execution to disk. Returns list of saved paths."""
    import plotly.graph_objects as go
    os.makedirs(FIGURE_DIR, exist_ok=True)
    saved: list[str] = []
    for fig_name, fig in figures.items():
        try:
            if isinstance(fig, go.Figure):
                pass
            elif isinstance(fig, dict):
                fig = go.Figure(fig)
            else:
                continue
            safe_name = fig_name.replace("/", "_").replace("\\", "_")
            ts = datetime.now().strftime("%H%M%S")
            path = os.path.join(FIGURE_DIR, f"{tool_name}_{safe_name}_{ts}.png")
            fig.write_image(path, format="png", scale=1.5, width=900, height=500)
            saved.append(path)
        except Exception as e:
            logger.warning("Failed to save figure %s/%s: %s", tool_name, fig_name, e)
    return saved


def list_saved_figures() -> list[str]:
    """List all saved figure paths."""
    if not os.path.isdir(FIGURE_DIR):
        return []
    return sorted(
        [os.path.join(FIGURE_DIR, f) for f in os.listdir(FIGURE_DIR) if f.endswith(".png")],
        key=os.path.getmtime, reverse=True,
    )


def get_figures_for_tool(tool_name: str) -> list[str]:
    """Get saved figure paths for a specific tool."""
    all_figs = list_saved_figures()
    return [f for f in all_figs if tool_name in os.path.basename(f)]
