"""LangGraph graph definition — assembles nodes + conditional edges.

Graph topology:
    START → planner ──→ executor ⇄ checker → interpreter → END
                 │        ↑         ↑          ↓
                 │        └─ error_handler ←───┘
                 └──→ interpreter (empty plan = chat mode)
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    planner_node,
    executor_node,
    checker_node,
    error_handler_node,
    interpreter_node,
)

logger = logging.getLogger(__name__)


def route_after_planner(state: AgentState) -> Literal["executor", "interpreter"]:
    """After planner: if plan is empty, skip to interpreter (chat mode)."""
    plan = state.get("plan", [])
    if not plan:
        logger.info("Empty plan — routing to interpreter (chat mode)")
        return "interpreter"
    logger.info("Plan has %d steps — routing to executor", len(plan))
    return "executor"


def route_after_checker(state: AgentState) -> Literal["executor", "interpreter"]:
    """Conditional routing — error steps just continue to next, no retry.

    - step_error=True → executor (step_idx already past failed step, will try next)
    - not done → executor
    - done → interpreter
    """
    step_idx = state.get("step_idx", 0)
    plan = state.get("plan", [])

    if step_idx >= len(plan):
        logger.info("step_idx=%d >= len(plan)=%d, routing to interpreter", step_idx, len(plan))
        return "interpreter"

    logger.info("step %d/%d, routing to executor", step_idx + 1, len(plan))
    return "executor"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph StateGraph."""
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("checker", checker_node)
    builder.add_node("error_handler", error_handler_node)
    builder.add_node("interpreter", interpreter_node)

    # Edges
    builder.add_edge(START, "planner")

    # After planner: if plan is empty, go straight to interpreter
    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {"executor": "executor", "interpreter": "interpreter"},
    )

    builder.add_edge("executor", "checker")

    # Conditional routing from checker
    builder.add_conditional_edges(
        "checker",
        route_after_checker,
        {
            "executor": "executor",
            "interpreter": "interpreter",
        },
    )

    builder.add_edge("error_handler", "checker")
    builder.add_edge("interpreter", END)

    return builder.compile()


# Singleton compiled graph
_graph = build_graph()


def run_agent(
    user_message: str,
    data_path: str | None = None,
    prev_results: dict | None = None,
    prev_figures: dict | None = None,
    conversation_history: list[dict] | None = None,
    prev_turn_count: int = 0,
) -> dict:
    """Convenience entry: run the full graph on one user message."""
    from langchain_core.messages import HumanMessage, AIMessage

    messages = []
    if conversation_history:
        for m in conversation_history[-20:]:
            content = m.get("content", "")
            if m.get("role") == "user":
                messages.append(HumanMessage(content=content))
            elif m.get("role") == "assistant":
                messages.append(AIMessage(content=content))

    initial_state: AgentState = {
        "messages": messages,
        "data_path": data_path,
        "plan": [],
        "step_idx": 0,
        "results": prev_results or {},
        "figures": prev_figures or {},
        "error": None,
        "error_count": 0,
        "step_error": False,
        "last_step": None,
        "final_answer": None,
        "n_hvg": None,
        "resolution": None,
        "gene_names": None,
        "turn_count": prev_turn_count,
        "applied_procedures": [],
        "retry_count": {},
        "quality_log": [],
    }

    final_state = _graph.invoke(initial_state, config={"recursion_limit": 50})
    return final_state
