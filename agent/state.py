"""Agent state — the shared memory across all LangGraph nodes.

Uses a TypedDict with Annotated reducers so state grows monotonically
(no node can delete another node's work).
"""

import operator
from typing import Annotated, TypedDict, Any, Optional, Sequence
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


def _merge_dicts(a: dict[str, Any], b: dict[str, Any] | None) -> dict[str, Any]:
    """Reducer: shallow-merge right into left. `results` and `figures` both use this."""
    if b is None:
        return a
    return {**a, **b}


class AgentState(TypedDict):
    """Shared state flowing through the graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    data_path: Optional[str]
    plan: list[dict[str, Any]]
    step_idx: int
    results: Annotated[dict[str, Any], _merge_dicts]
    figures: Annotated[dict[str, Any], _merge_dicts]
    error: Optional[str]
    error_count: int
    step_error: bool
    last_step: Optional[str]
    final_answer: Optional[str]
    n_hvg: Optional[int]
    resolution: Optional[float]
    gene_names: Optional[list[str]]
    turn_count: int
    applied_procedures: list[str]
    retry_count: Annotated[dict[str, int], _merge_dicts]
    quality_log: Annotated[list[str], operator.add]
