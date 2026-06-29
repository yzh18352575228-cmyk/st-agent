# 🧬 Spatial Transcriptomics Analysis Agent

A LangGraph-based agent for spatial transcriptomics data analysis. Natural language input → automatic pipeline planning → tool execution → interactive Plotly charts + AI interpretation. Supports **GSE278603** (mouse embryo Stereo-seq, E7.5–E8.0).

Course project for **Computational Biology** (Spring 2026), Southeast University.

## Quick Start

```bash
conda env create -f environment.yml
conda activate st_agent
cp .env.example .env  # edit with your API keys
streamlit run app.py
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent** | LangGraph (StateGraph + conditional edges) |
| **LLM** | DeepSeek-V4 (OpenAI-compatible API) |
| **Spatial** | Scanpy, Squidpy, AnnData |
| **Frontend** | Streamlit + Plotly |

## License

Academic use — Southeast University, Spring 2026.