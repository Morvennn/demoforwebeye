"""Pipeline test with a fake LLM + fake fetcher (no network, no API key)."""
# Daniel Design

import app.pipeline
from app.github import RepoData
from app.models import RepoMeta
from app.pipeline import analyze

CODE = {
    "agent": "code_audit",
    "dimensions": {
        "structure": {"score": 80, "comment": "清晰"},
        "code_health_and_security": {"score": 70, "comment": "无明显硬编码"},
        "engineering": {"score": 60, "comment": "缺测试"},
    },
    "findings": [{"severity": "med", "point": "没有测试目录"}],
    "summary": "代码结构清晰，工程化不足。",
}
PRODUCT = {
    "agent": "product_value",
    "dimensions": {
        "docs_and_usability": {"score": 85, "comment": "Quick Start 完整"},
        "practical_value": {"score": 80, "comment": "实用"},
        "oss_activity": {"score": 75, "comment": "活跃"},
    },
    "findings": [],
    "summary": "文档优秀，社区活跃。",
}
JUDGE = {
    "agent": "judge",
    "final_score": 78,
    "weighting": "基础 50/50，标准软件项目。",
    "applied_weights": {"code": 0.5, "product": 0.5},
    "dimension_scores": {
        "structure": 80, "code_health_and_security": 70, "engineering": 60,
        "docs_and_usability": 85, "practical_value": 80, "oss_activity": 75,
    },
    "strengths": ["README 写得好", "结构清晰"],
    "recommendations": [{"priority": "med", "suggestion": "补充单元测试"}],
    "verdict": "不错的项目，工程化可加强。",
}


class FakeFetcher:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def fetch_all(self, owner, repo):
        return RepoData(
            meta=RepoMeta(owner=owner, repo=repo, url=f"https://github.com/{owner}/{repo}", stars=10),
            readme="# Fake README\n\nA repo.",
            tree=["main.py", "requirements.txt", "README.md"],
            key_files={"main.py": "print('hi')"},
        )


class FakeLLM:
    def __init__(self):
        self.calls = 0

    async def stream_json(self, system, user, on_delta=None):
        self.calls += 1
        # Judge prompt mentions both other agents, so detect it first.
        if "总分裁判" in system:
            resp = JUDGE
        elif "代码审计" in system:
            resp = CODE
        else:
            resp = PRODUCT
        if on_delta:
            await on_delta("…")
        return resp


async def test_pipeline_event_sequence(monkeypatch):
    monkeypatch.setattr(app.pipeline, "RepoFetcher", FakeFetcher)
    llm = FakeLLM()

    events = [e async for e in analyze("https://github.com/o/r", llm=llm)]
    types = [e["event"] for e in events]

    # Meta first, report last.
    assert types[0] == "meta"
    assert types[-1] == "report"

    # A and B both complete (agent_done x2); C emits judge_done.
    assert types.count("agent_start") == 3  # A, B, C
    assert types.count("agent_done") == 2  # A, B
    assert "judge_done" in types
    assert types.index("judge_done") < types.index("report")

    # Token streaming happened for all three agents.
    assert types.count("agent_delta") >= 3
    assert llm.calls == 3

    # Final report carries the full consolidated payload.
    report = events[-1]["data"]
    assert report["judge"]["final_score"] == 78
    assert report["code_audit"]["agent"] == "code_audit"
    assert report["product_value"]["agent"] == "product_value"
    assert report["meta"]["owner"] == "o"
