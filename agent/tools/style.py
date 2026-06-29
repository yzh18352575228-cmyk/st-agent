"""Plotly shared styling — nature-figure principles.

Provides:
  BASE_LAYOUT: dict — default layout applied to every figure
  apply_style(fig): apply BASE_LAYOUT
  spatial_style(fig): apply spatial figure specifics (equal aspect)
  CLUSTER_PALETTE: list[str] — Set2 (8 colors, colorblind-friendly)
  CONTINUOUS_SCALE: str — Viridis
  DIVERGING_SCALE: str — RdBu_r
"""

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

# ── Color palettes ──────────────────────────────────────────
CLUSTER_PALETTE = px.colors.qualitative.Set2
CONTINUOUS_SCALE = "Viridis"
DIVERGING_SCALE = "RdBu_r"

ACCENT_BLUE = "#4C72B0"
ACCENT_RED = "#C44E52"
ACCENT_GREEN = "#55A868"
GRAY = "#999999"

# ── Base layout ─────────────────────────────────────────────
BASE_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "Arial, Helvetica, sans-serif", "size": 10, "color": "#111111"},
    "title": {"font": {"size": 13}},
    "paper_bgcolor": "#FFFFFF",
    "plot_bgcolor": "#FFFFFF",
    "xaxis": {"showgrid": False, "zeroline": False},
    "yaxis": {"showgrid": False, "zeroline": False},
    "margin": {"l": 40, "r": 20, "t": 50, "b": 40},
}


def apply_style(fig: go.Figure) -> go.Figure:
    """Apply BASE_LAYOUT to a figure. Returns the same figure."""
    fig.update_layout(**BASE_LAYOUT)
    return fig


def spatial_style(fig: go.Figure) -> go.Figure:
    """Apply spatial figure specifics: equal aspect ratio."""
    apply_style(fig)
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    return fig
