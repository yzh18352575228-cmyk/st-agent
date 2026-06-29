"""Streamlit frontend for the spatial transcriptomics analysis agent.

Launch:  streamlit run app.py
"""

import sys, os, tempfile, atexit, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_IS_WSL = sys.platform == "win32" and os.path.dirname(os.path.abspath(__file__)).startswith("\\\\")
if _IS_WSL:
    _UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "st_agent_uploads")
else:
    _UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _cleanup_uploads():
    if _IS_WSL and os.path.isdir(_UPLOAD_DIR):
        shutil.rmtree(_UPLOAD_DIR, ignore_errors=True)


atexit.register(_cleanup_uploads)

import streamlit as st
import plotly.graph_objects as go
import logging

from agent.graph import run_agent
from agent.tools import TOOL_REGISTRY

T = {
    "en": {
        "page_title": "Spatial Transcriptomics Agent",
        "sidebar_title": "ST Agent",
        "upload_label": "Upload .h5ad file",
        "path_label": "Or enter file path:",
        "settings_header": "Settings",
        "tools_header": "Tools",
        "reset_btn": "Reset",
        "main_title": "Spatial Transcriptomics Analysis Agent",
        "chat_placeholder": "e.g. 'Load data and run full QC + clustering pipeline'",
        "figures_header": "Figures",
        "interpretation_header": "Interpretation",
        "lang_label": "Language / 语言",
    },
    "zh": {
        "page_title": "空间转录组分析 Agent",
        "sidebar_title": "空转分析",
        "upload_label": "上传 .h5ad 文件",
        "path_label": "或输入文件路径：",
        "settings_header": "参数设置",
        "tools_header": "可用工具",
        "reset_btn": "重置",
        "main_title": "空间转录组分析 Agent",
        "chat_placeholder": "例如：加载数据并运行完整的 QC 和聚类流程",
        "figures_header": "分析图表",
        "interpretation_header": "结果解读",
        "lang_label": "语言 / Language",
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "zh")
    return T.get(lang, T["zh"]).get(key, key)


def fig_download_buttons(fig, name: str, key: str):
    col1, col2, _ = st.columns([1, 1, 6])
    try:
        png_bytes = fig.to_image(format="png", scale=2, width=1200, height=700)
        col1.download_button(label="PNG", data=png_bytes, file_name=f"{name}.png", mime="image/png", key=f"dl_png_{key}")
    except Exception:
        col1.caption("PNG unavailable")
    html_bytes = fig.to_html(include_plotlyjs="cdn").encode("utf-8")
    col2.download_button(label="HTML", data=html_bytes, file_name=f"{name}.html", mime="text/html", key=f"dl_html_{key}")


st.set_page_config(page_title="ST Agent", page_icon="🧬", layout="wide")

DEFAULTS = {"messages": [], "data_path": "", "running": False, "lang": "zh", "show_tools": False}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.sidebar:
    st.title(t("sidebar_title"))
    lang_choice = st.radio(t("lang_label"), options=["zh", "en"],
        format_func=lambda x: "中文" if x == "zh" else "English",
        index=0 if st.session_state.lang == "zh" else 1, horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    st.subheader("Data")
    uploaded = st.file_uploader(t("upload_label"), type=["h5ad"])
    if uploaded:
        os.makedirs(_UPLOAD_DIR, exist_ok=True)
        save_path = os.path.join(_UPLOAD_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.data_path = save_path

    data_path_manual = st.text_input(t("path_label"))
    if data_path_manual and os.path.exists(data_path_manual):
        st.session_state.data_path = data_path_manual

    st.subheader(t("settings_header"))
    st.number_input("HVG count", 500, 5000, 2000, 100, key="cfg_hvg")
    st.slider("Leiden resolution", 0.1, 3.0, 1.0, 0.1, key="cfg_res")
    st.number_input("PCs", 10, 100, 30, 5, key="cfg_pcs")

    if st.button(t("reset_btn"), use_container_width=True):
        for k in DEFAULTS:
            if k != "lang":
                st.session_state[k] = DEFAULTS[k]
        st.rerun()

st.title(t("main_title"))

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "figures" in msg and msg["figures"] and msg.get("is_current"):
            for name, fig_data in msg["figures"].items():
                fig = fig_data if isinstance(fig_data, go.Figure) else go.Figure(fig_data) if isinstance(fig_data, dict) else None
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"hist_{msg.get('id','')}_{name}")
                    fig_download_buttons(fig, name, f"hist_{msg.get('id','')}_{name}")

skill_cols = st.columns(5)
_skill_shortcuts = [("基础流程", "跑基础分析流程"), ("扩展分析", "跑扩展分析"), ("聚类解释", "解释聚类结果"), ("生成报告", "生成分析报告"), ("跨阶段", "跨阶段对比分析")]
for i, (label, cmd) in enumerate(_skill_shortcuts):
    if skill_cols[i].button(label, use_container_width=True, key=f"skill_btn_{i}"):
        st.session_state["skill_shortcut"] = cmd

_trigger = st.session_state.pop("skill_shortcut", None)
prompt = st.chat_input(t("chat_placeholder"))
if not prompt and _trigger:
    prompt = _trigger

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            prev_results, prev_figures = {}, {}
            for m in st.session_state.messages:
                if m["role"] == "assistant" and "results" in m:
                    prev_results.update(m["results"])
                if m["role"] == "assistant" and "figures" in m:
                    prev_figures.update(m["figures"])

            state = run_agent(
                prompt, data_path=st.session_state.get("data_path", ""),
                prev_results=prev_results, prev_figures=prev_figures,
                conversation_history=list(st.session_state.messages), prev_turn_count=0,
            )

            results = state.get("results", {})
            figures = state.get("figures", {})
            final = state.get("final_answer", "")

            actual_figs = {}
            for tool_name in results:
                prefix = tool_name + "_"
                for fk, fv in figures.items():
                    if fk.startswith(prefix):
                        actual_figs[fk] = fv

            if actual_figs:
                st.subheader(t("figures_header"))
                cols = st.columns(min(len(actual_figs), 2))
                for i, (name, fig) in enumerate(actual_figs.items()):
                    with cols[i % 2]:
                        if isinstance(fig, go.Figure):
                            st.plotly_chart(fig, use_container_width=True, key=f"main_{name}")
                            fig_download_buttons(fig, name, f"main_{name}")

            if final:
                st.markdown(f"### {t('interpretation_header')}")
                st.markdown(final)

            for prev_msg in st.session_state.messages:
                if prev_msg.get("role") == "assistant":
                    prev_msg["is_current"] = False
            st.session_state.messages.append({
                "role": "assistant", "content": final,
                "figures": {k: (v.to_dict() if isinstance(v, go.Figure) else v) for k, v in actual_figs.items()},
                "is_current": True, "id": str(len(st.session_state.messages)),
            })
        except Exception as e:
            st.error(f"Agent error: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Agent error: {e}"})
        finally:
            st.rerun()
