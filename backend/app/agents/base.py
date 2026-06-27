"""Shared agent base + scoring anchors injected into every system prompt."""
# Daniel Design

from abc import ABC, abstractmethod
from typing import Any

from ..llm import DeltaCallback, LLMClient

# Unified 0-100 anchors — written into every agent's system prompt and used to
# drive the frontend color bands (red / orange / green / highlight).
ANCHORS = """\
评分锚点（所有维度与总分统一使用 0-100 分制）：
- 0-50（红 · 不及格）：存在严重问题，无法正常运行或无文档
- 51-75（橙 · 及格）：勉强可用，存在明显工程化或文档短板
- 76-90（绿 · 优秀）：结构清晰，易于上手，维护良好
- 91-100（高亮 · 极品）：行业标杆级开源工程，几无瑕疵"""

JSON_ONLY = "严格只输出一个 JSON 对象，不要输出任何额外文字、解释或 markdown 代码块。"


class BaseAgent(ABC):
    """An agent = a system prompt + a user-prompt builder + an LLM call.

    Subclasses set ``name`` (machine id) and ``label`` (Chinese display name)
    and implement ``system_prompt`` / ``user_prompt``. ``run`` streams the LLM
    output and returns the parsed JSON dict.
    """

    name: str = ""
    label: str = ""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def user_prompt(self, context: dict[str, Any]) -> str:
        ...

    async def run(
        self,
        context: dict[str, Any],
        on_delta: DeltaCallback | None = None,
    ) -> dict[str, Any]:
        return await self.llm.stream_json(
            self.system_prompt(),
            self.user_prompt(context),
            on_delta=on_delta,
        )
