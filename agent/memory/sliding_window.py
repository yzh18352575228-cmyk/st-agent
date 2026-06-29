"""Sliding window memory — prevents token explosion from infinite chat history."""

from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage


class SlidingWindowMemory:
    """Manages sliding-window compression of conversation history."""

    def __init__(self, k: int = 8) -> None:
        self.k = k

    def should_compress(self, messages: list[Any]) -> bool:
        return len(messages) > self.k

    def compress(self, messages: list[Any], llm: Any) -> list[Any]:
        if len(messages) <= self.k:
            return messages
        old = messages[: -self.k]
        recent = messages[-self.k :]
        old_text_parts = []
        for m in old:
            role = getattr(m, "type", "unknown")
            content = getattr(m, "content", "")
            if isinstance(content, str) and content.strip():
                old_text_parts.append(f"[{role}]: {content.strip()}")
        old_text = "\n".join(old_text_parts)
        if not old_text.strip():
            return recent
        summary_prompt = HumanMessage(content=(
            "请将以下对话历史压缩为不超过5句话的中文摘要，重点保留：已加载的数据集、已完成的分析步骤、用户关注的基因/参数、发现的关键结论。不要编造内容，只总结已有信息。\n\n对话历史：\n" + old_text))
        try:
            response = llm.invoke([summary_prompt])
            summary = response.content.strip()
        except Exception:
            return messages
        return [SystemMessage(content=f"[历史摘要]\n{summary}")] + recent
