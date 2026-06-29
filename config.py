"""Central configuration — loaded from .env file."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── DeepSeek ─────────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ── MiniMax (multi-modal chart reader) ───────────────────
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M1")

# ── App ─────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("ST_AGENT_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
DEFAULT_H5AD_PATH = os.getenv("DEFAULT_H5AD_PATH", "./data/sample.h5ad")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Analysis defaults ───────────────────────────────────
DEFAULT_N_HVG = int(os.getenv("DEFAULT_N_HVG", "2000"))
DEFAULT_N_PCS = int(os.getenv("DEFAULT_N_PCS", "30"))
DEFAULT_RESOLUTION = float(os.getenv("DEFAULT_RESOLUTION", "1.0"))
DEFAULT_MIN_GENES = int(os.getenv("DEFAULT_MIN_GENES", "200"))
DEFAULT_MIN_CELLS = int(os.getenv("DEFAULT_MIN_CELLS", "3"))
DEFAULT_MITO_PCT = float(os.getenv("DEFAULT_MITO_PCT", "20"))
