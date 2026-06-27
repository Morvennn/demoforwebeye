"""Pydantic schemas shared across the backend and serialized over SSE."""
# Daniel Design

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["high", "med", "low"]


class DimensionScore(BaseModel):
    """A single scored dimension (0-100) with an explanatory comment."""

    score: int = Field(..., ge=0, le=100)
    comment: str


class Finding(BaseModel):
    severity: Severity
    point: str


class Recommendation(BaseModel):
    priority: Severity
    suggestion: str


class RepoMeta(BaseModel):
    owner: str
    repo: str
    url: str
    description: str | None = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    default_branch: str = "main"
    pushed_at: str | None = None
    license: str | None = None
    languages: dict[str, int] = Field(default_factory=dict)
    has_contributing: bool = False


class AgentReport(BaseModel):
    """Structured output produced by Agent A (code_audit) or B (product_value)."""

    agent: str
    dimensions: dict[str, DimensionScore]
    findings: list[Finding] = Field(default_factory=list)
    summary: str


class JudgeReport(BaseModel):
    """Structured output produced by Agent C (judge)."""

    agent: str = "judge"
    final_score: int = Field(..., ge=0, le=100)
    weighting: str
    applied_weights: dict[str, float]
    dimension_scores: dict[str, int]
    strengths: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    verdict: str


class FinalReport(BaseModel):
    """Consolidated object emitted as the final `report` event (for download)."""

    meta: RepoMeta
    code_audit: AgentReport
    product_value: AgentReport
    judge: JudgeReport
