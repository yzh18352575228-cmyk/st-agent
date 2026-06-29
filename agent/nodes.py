"""LangGraph nodes — each node is a pure function: (state) -> dict of state updates."""

import json, logging, base64, io, re
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .state import AgentState
from .tools import TOOL_REGISTRY, get_tool_descriptions, execute_tool
from .memory.working_memory import get_adata_snapshot, format_snapshot_for_prompt, mark_step_completed
from .memory.sliding_window import SlidingWindowMemory
from .memory.procedures import apply_procedures
from .memory.quality_rules import get_rule
from .memory.figure_store import save_figures_to_disk
from .skills.definitions import get_skill_descriptions
from .skills.executor import skill_to_plan

_sliding_window = SlidingWindowMemory(k=999)

try:
    from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL
except ImportError:
    import os
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M1")

logger = logging.getLogger(__name__)
_llm: ChatOpenAI | None = None
_minimax_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, model=DEEPSEEK_MODEL, temperature=0.0, max_tokens=2048)
    return _llm


def _get_minimax() -> ChatOpenAI | None:
    global _minimax_llm
    if not MINIMAX_API_KEY or MINIMAX_API_KEY.startswith("your-"):
        return None
    if _minimax_llm is None:
        _minimax_llm = ChatOpenAI(api_key=MINIMAX_API_KEY, base_url=MINIMAX_BASE_URL, model=MINIMAX_MODEL, temperature=0.0, max_tokens=1024)
    return _minimax_llm


PLANNER_SYSTEM = """你是一个空间转录组分析规划器。根据用户指令，只执行明确要求的分析步骤。
## 核心原则：只做用户明确要求的
- "加载数据" -> 只跑 load_data
- "加载并跑QC" -> load_data + run_qc
- "跑全流程" -> load_data + get_overview + run_qc + run_preprocess + run_clustering + plot_spatial_clusters + run_marker_analysis
- 追问/闲聊/确认状态 -> 返回 []

## 输出格式
只输出 JSON 数组: [{"tool": "...", "args": {...}, "reason": "..."}]

## Skill 调用
用 skill 字段: [{"skill": "basic_pipeline", "args": {}, "reason": "..."}]

## 数据状态感知
- 已完成步骤中的工具 = 不需要再跑，除非用户明确要求重做
- PCA=否但要求聚类 -> 先插入 run_preprocess
- 空间坐标=否 -> 不规划任何空间工具
"""

INTERPRETER_SYSTEM = """你是空间转录组与生物信息学专家。用中文回复，markdown格式。不要编造生物学结论。"""


def planner_node(state: AgentState) -> dict[str, Any]:
    user_msg = state["messages"][-1].content if state["messages"] else ""
    snapshot = get_adata_snapshot()
    RERUN_KEYWORDS = ["重新", "重做", "换参数", "再来一次", "换个分辨率", "换个阈值"]
    VIEW_KEYWORDS = ["看看", "再看", "展示一下", "显示", "图在哪"]
    is_rerun = any(kw in user_msg for kw in RERUN_KEYWORDS)
    is_view = any(kw in user_msg for kw in VIEW_KEYWORDS)

    if is_rerun:
        for kw, tool_name in [("qc", "run_qc"), ("聚类", "run_clustering"), ("预处理", "run_preprocess"), ("marker", "run_marker_analysis"), ("富集", "run_enrichment_analysis")]:
            if kw in user_msg or kw.lower() in user_msg.lower():
                args = {}
                mg = re.search(r'min_genes[=: ]*(\d+)', user_msg)
                if mg: args["min_genes"] = int(mg.group(1))
                mm = re.search(r'max_mito_pct[=: ]*(\d+)', user_msg)
                if mm: args["max_mito_pct"] = float(mm.group(1))
                if "kegg" in user_msg.lower(): args["db"] = "KEGG_2021_Mouse"
                elif "go" in user_msg.lower(): args["db"] = "GO_Biological_Process_2023"
                plan = [{"tool": tool_name, "args": args, "reason": f"用户要求重新执行 {tool_name}"}]
                if snapshot.get("loaded"):
                    plan, _ = apply_procedures(plan, snapshot)
                return {"data_path": state.get("data_path"), "plan": plan, "step_idx": 0, "error": None, "error_count": 0, "step_error": False, "last_step": None, "results": {}, "figures": {}, "turn_count": state.get("turn_count", 0) + 1, "applied_procedures": []}

    if is_view and not is_rerun:
        from agent.tools.store import get_cached_figures, has_cached_figures
        snap = get_adata_snapshot()
        cached_hits = [t for t in snap.get("completed_steps", []) if has_cached_figures(t)]
        if cached_hits:
            return {"data_path": state.get("data_path"), "plan": [], "step_idx": 0, "error": None, "error_count": 0, "step_error": False, "last_step": None, "results": {}, "figures": {}, "turn_count": state.get("turn_count", 0) + 1, "applied_procedures": []}

    SKILL_KEYWORDS = {"基础分析流程": "basic_pipeline", "基础流程": "basic_pipeline", "扩展分析": "extended_analysis", "聚类解释": "cluster_interpretation", "生成报告": "report_generation", "跨阶段对比": "cross_stage_pipeline"}
    for kw, skill_name in SKILL_KEYWORDS.items():
        if kw in user_msg:
            skill_plan, err = skill_to_plan(skill_name, {})
            if not err and skill_plan:
                return {"data_path": state.get("data_path"), "plan": skill_plan, "step_idx": 0, "error": None, "error_count": 0, "step_error": False, "last_step": None, "results": {}, "figures": {}, "turn_count": state.get("turn_count", 0) + 1, "applied_procedures": []}

    data_path = state.get("data_path")
    if not data_path:
        m = re.search(r"([/\w.-]+\.h5ad)", user_msg)
        data_path = m.group(1) if m else None

    snapshot = get_adata_snapshot()
    _dp = state.get("data_path")
    if _dp and not snapshot.get("loaded", False) and ("加载" in user_msg or "上传" in user_msg):
        return {"data_path": _dp, "plan": [{"tool": "load_data", "args": {"file_path": _dp}, "reason": "用户已上传文件"}], "step_idx": 0, "error": None, "error_count": 0, "step_error": False, "last_step": None, "results": {}, "figures": {}, "turn_count": state.get("turn_count", 0) + 1, "applied_procedures": []}

    dynamic_system = PLANNER_SYSTEM.format(tool_descriptions=get_tool_descriptions(), skill_descriptions=get_skill_descriptions()) + "\n" + format_snapshot_for_prompt(snapshot)
    prev_results = state.get("results", {})
    if prev_results and snapshot.get("completed_steps"):
        dynamic_system += "\n## 上一轮刚刚完成\n"
        for step_name in snapshot["completed_steps"][-5:]:
            short = str(prev_results.get(step_name, ""))[:120]
            dynamic_system += f"- `{step_name}` 已完成: {short}\n"

    raw_messages = list(state["messages"])
    llm = _get_llm()
    history_text = ""
    for m in raw_messages[-20:]:
        role = getattr(m, "type", "?")
        content = getattr(m, "content", "")
        if content:
            prefix = "用户" if role == "human" else "助手"
            history_text += f"[{prefix}]: {content[:500]}\n"

    full_context = dynamic_system + f"\n\n## 对话历史\n{history_text}\n\n用户当前问题: {user_msg}\n数据路径: {data_path or '未指定'}\n请输出 JSON plan:"
    response = llm.invoke([HumanMessage(content=full_context)])
    new_turn = state.get("turn_count", 0) + 1
    raw = response.content.strip()
    plan = None
    try:
        if "```" in raw:
            parts = raw.split("```json")
            raw_clean = parts[-1].split("```")[0].strip() if len(parts) > 1 else raw.split("```")[1].split("```")[0].strip()
            plan = json.loads(raw_clean)
        else:
            plan = json.loads(raw)
    except json.JSONDecodeError:
        try:
            lb, rb = raw.find("["), raw.rfind("]")
            if lb >= 0 and rb > lb:
                plan = json.loads(raw[lb:rb + 1])
        except json.JSONDecodeError:
            plan = []
    if plan is None:
        plan = []
    if isinstance(plan, dict):
        plan = [plan]
    expanded_plan = []
    for step in plan:
        if "skill" in step:
            skill_plan, err = skill_to_plan(step["skill"], step.get("args"))
            if not err and skill_plan:
                expanded_plan.extend(skill_plan)
        else:
            expanded_plan.append(step)
    plan = expanded_plan
    applied_rules = []
    if plan:
        snapshot_proc = get_adata_snapshot()
        plan, applied_rules = apply_procedures(list(plan), snapshot_proc)
    completed_tools = set(snapshot.get("completed_steps", []))
    NEGATIONS = ["不想", "不做", "别做", "先不做", "暂时不做", "不要做", "不用做", "不需要做", "先别", "暂时别"]
    if not plan and user_msg and snapshot.get("loaded") and not any(neg in user_msg for neg in NEGATIONS):
        ANALYSIS_KEYWORDS = {"聚类": ["run_preprocess", "run_clustering"], "marker": ["run_marker_analysis"], "富集": ["run_enrichment_analysis"], "通讯": ["run_cell_communication"], "空间域": ["run_spatial_domain"], "空间分布": ["plot_spatial_clusters"], "变异基因": ["run_svg_analysis"], "svg": ["run_svg_analysis"], "邻域": ["run_neighborhood_analysis"], "注释": ["run_knowledge_annotation"], "报告": ["run_generate_report"], "qc": ["run_qc"], "kegg": ["run_enrichment_analysis"], "go": ["run_enrichment_analysis"], "预处理": ["run_preprocess"]}
        kw_lower_map = {k.lower(): tools for k, tools in ANALYSIS_KEYWORDS.items()}
        needed = []
        for kw, tools in kw_lower_map.items():
            if kw in user_msg.lower():
                for t in tools:
                    if t not in completed_tools:
                        needed.append({"tool": t, "args": {}, "reason": f"[自动补全] {kw}"})
        plan = needed
    if completed_tools and plan and not is_rerun:
        plan = [s for s in plan if s.get("tool") not in completed_tools]
    return {"data_path": data_path, "plan": plan, "step_idx": 0, "error": None, "error_count": 0, "step_error": False, "last_step": None, "results": {}, "figures": {}, "turn_count": new_turn, "applied_procedures": applied_rules}


def executor_node(state: AgentState) -> dict[str, Any]:
    plan = state.get("plan", [])
    step_idx = state.get("step_idx", 0)
    if step_idx >= len(plan):
        return {"step_error": True, "error": "No more steps."}
    step = plan[step_idx]
    tool_name = step["tool"]
    args = dict(step.get("args", {}))
    for user_key, tool_key in [("n_hvg", "n_hvg"), ("resolution", "resolution"), ("n_pcs", "n_pcs")]:
        if state.get(user_key) is not None and tool_key not in args:
            args[tool_key] = state[user_key]
    if tool_name == "load_data" and "file_path" not in args and state.get("data_path"):
        args["file_path"] = state["data_path"]
    result = execute_tool(tool_name, args)
    if isinstance(result, dict):
        summary, figures = result.get("summary", ""), result.get("figures", {})
    else:
        summary, figures = str(result), {}
    is_error = isinstance(summary, str) and summary.startswith("❌")
    new_results = {tool_name: summary}
    new_figures = {}
    for k, v in figures.items():
        key = f"{tool_name}_{k}" if not k.startswith(tool_name) else k
        new_figures[key] = v
    if not is_error:
        mark_step_completed(tool_name)
    if figures:
        try:
            saved = save_figures_to_disk(tool_name, figures)
            for p in saved:
                from agent.tools.store import cache_figure
                cache_figure(tool_name, p)
        except Exception:
            pass
    return {"results": new_results, "figures": new_figures, "step_idx": step_idx + 1, "step_error": is_error, "last_step": tool_name, "error": summary if is_error else None}


def checker_node(state: AgentState) -> dict[str, Any]:
    last_tool = state.get("last_step")
    if not last_tool or state.get("step_error", False):
        return {"step_error": False, "quality_log": [f"{last_tool}: executor error" if state.get("step_error") else ""] if state.get("step_error") else []}
    rule = get_rule(last_tool)
    if rule is None:
        return {"step_error": False, "quality_log": [f"{last_tool}: no quality rule, passed"]}
    snapshot = get_adata_snapshot()
    tool_result = state.get("results", {}).get(last_tool, "")
    passed, reason = rule.check(snapshot, str(tool_result))
    return {"step_error": not passed, "quality_log": [f"{last_tool}: {'passed' if passed else reason}"]}


def error_handler_node(state: AgentState) -> dict[str, Any]:
    return {"error_count": state.get("error_count", 0) + 1, "step_error": False, "error": f"Step {state.get('last_step', '?')} failed. Skipping."}


def interpreter_node(state: AgentState) -> dict[str, Any]:
    results = state.get("results", {})
    figures = state.get("figures", {})
    error = state.get("error")
    messages = state.get("messages", [])
    user_msg = messages[-1].content if messages else ""
    llm = _get_llm()
    prev_user_msg = ""
    if any(kw in user_msg for kw in ["上个问题", "上一个问题", "上上个问题", "上上上个问题"]):
        for m in reversed(list(messages[:-1])):
            if getattr(m, "type", "") == "human":
                prev_user_msg = getattr(m, "content", "")[:300]
                break
    if prev_user_msg and any(kw in user_msg for kw in ["上个问题", "上一个问题"]):
        count = 3 if "上上上个" in user_msg else (2 if "上上个" in user_msg else 1)
        if count > 1:
            found = [getattr(m, "content", "")[:200] for m in reversed(list(messages[:-1])) if getattr(m, "type", "") == "human"]
            if len(found) >= count:
                return {"final_answer": f"您上{'上'*(count-1)}个问题是：**{found[count-1]}**"}
            return {"final_answer": f"对话中只有 {len(found)} 条用户消息。"}
        return {"final_answer": f"您上一个问题是：**{prev_user_msg}**"}
    executed = list(results.keys())
    summary = "\n\n".join(f"### {k}\n{v}" for k, v in results.items())
    prompt = f"用户当前问题：{user_msg}\n\n已执行工具：{', '.join(executed) or '(无)'}\n{summary[:3000]}\n\n" + (f"错误：{error}\n\n" if error else "") + "请简洁回答用户问题。不要编造数据。"
    response = llm.invoke([SystemMessage(content=INTERPRETER_SYSTEM), HumanMessage(content=prompt)])
    text_answer = response.content.strip()
    turn = state.get("turn_count", 0)
    text_answer = f"[对话轮次: {turn}]\n\n{text_answer}"
    return {"final_answer": text_answer}
