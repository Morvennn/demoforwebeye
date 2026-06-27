"""Multi-agent orchestration: parallel A+B, then C, streamed as SSE events."""
# Daniel Design

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from .agents import CodeAuditAgent, JudgeAgent, ProductValueAgent
from .github import RepoFetcher, parse_repo_url
from .llm import LLMClient
from .models import AgentReport, JudgeReport, RepoMeta

# A phase spec: (agent, context, done_event_name, result_model)
Spec = tuple[Any, dict[str, Any], str, type]


def _meta_summary(meta: RepoMeta) -> dict[str, Any]:
    top_lang = max(meta.languages, key=meta.languages.get) if meta.languages else None
    return {
        "仓库": f"{meta.owner}/{meta.repo}",
        "描述": meta.description or "（无描述）",
        "Star": meta.stars,
        "Fork": meta.forks,
        "Open Issues": meta.open_issues,
        "主语言": top_lang or "（未知）",
        "语言分布": meta.languages,
        "默认分支": meta.default_branch,
        "最近推送": meta.pushed_at,
        "License": meta.license or "未声明",
        "贡献指南": "有" if meta.has_contributing else "无",
    }


async def _run_phase(specs: list[Spec]) -> AsyncIterator[dict[str, Any]]:
    """Run several agents concurrently, yielding their SSE events as they emit.

    Uses a queue so multiple agents' token streams interleave into one stream.
    Each spec runs as a task that emits agent_start / agent_delta / done, or a
    ``_failed`` sentinel. Raises ``RuntimeError`` if any agent in the phase fails.
    """
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def run_one(agent: Any, ctx: dict[str, Any], done_event: str, model_cls: type) -> None:
        await queue.put({"event": "agent_start", "data": {"agent": agent.name, "label": agent.label}})

        async def on_delta(delta: str, _name: str = agent.name) -> None:
            await queue.put({"event": "agent_delta", "data": {"agent": _name, "delta": delta}})

        try:
            raw = await agent.run(ctx, on_delta=on_delta)
            report = model_cls(**raw)
            await queue.put({"event": done_event, "data": {"agent": agent.name, "report": report.model_dump()}})
        except Exception as e:  # noqa: BLE001 — surfaced as a phase failure
            await queue.put({"event": "_failed", "data": {"agent": agent.name, "error": f"{type(e).__name__}: {e}"}})

    tasks = [asyncio.create_task(run_one(*spec)) for spec in specs]
    terminals = 0
    failure: dict[str, Any] | None = None
    try:
        while terminals < len(specs):
            evt = await queue.get()
            ev = evt["event"]
            if ev in ("agent_done", "judge_done"):
                terminals += 1
                yield evt
            elif ev == "_failed":
                terminals += 1
                failure = evt["data"]
            else:
                yield evt  # agent_start / agent_delta
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    if failure:
        raise RuntimeError(f"Agent {failure['agent']} 失败：{failure['error']}")


async def analyze(repo_url: str, llm: LLMClient | None = None) -> AsyncIterator[dict[str, Any]]:
    """Run the full A → (B parallel) → C pipeline, yielding SSE event dicts.

    Raises ``ValueError`` for a malformed URL (caller maps to HTTP 400) and
    ``GitHubError`` subclasses for fetch failures (caller maps to error events).
    """
    llm = llm or LLMClient()
    owner, repo = parse_repo_url(repo_url)
    repo_full = f"{owner}/{repo}"

    async with RepoFetcher() as fetcher:
        data = await fetcher.fetch_all(owner, repo)

    yield {"event": "meta", "data": data.meta.model_dump()}

    # Phase 1: A (code audit) and B (product value) in parallel.
    ab_specs: list[Spec] = [
        (
            CodeAuditAgent(llm),
            {"repo_full": repo_full, "tree": data.tree, "key_files": data.key_files, "languages": data.meta.languages},
            "agent_done",
            AgentReport,
        ),
        (
            ProductValueAgent(llm),
            {"repo_full": repo_full, "readme": data.readme, "meta_summary": _meta_summary(data.meta)},
            "agent_done",
            AgentReport,
        ),
    ]
    reports: dict[str, dict[str, Any]] = {}
    async for evt in _run_phase(ab_specs):
        if evt["event"] == "agent_done":
            reports[evt["data"]["agent"]] = evt["data"]["report"]
        yield evt

    # Phase 2: C (judge) consumes A and B.
    c_spec: Spec = (
        JudgeAgent(llm),
        {
            "repo_full": repo_full,
            "code_audit": reports["code_audit"],
            "product_value": reports["product_value"],
            "meta_summary": _meta_summary(data.meta),
        },
        "judge_done",
        JudgeReport,
    )
    judge_report: dict[str, Any] = {}
    async for evt in _run_phase([c_spec]):
        if evt["event"] == "judge_done":
            judge_report = evt["data"]["report"]
        yield evt

    yield {
        "event": "report",
        "data": {
            "meta": data.meta.model_dump(),
            "code_audit": reports["code_audit"],
            "product_value": reports["product_value"],
            "judge": judge_report,
        },
    }
