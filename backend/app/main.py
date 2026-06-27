"""FastAPI app — SSE endpoint for repo analysis + CORS + health check."""
# Daniel Design

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import get_settings
from .github import GitHubError, GitHubRateLimit, RepoNotFound, parse_repo_url
from .pipeline import analyze

app = FastAPI(title="Repo Health Check API", version="0.1.0")


def _origins(raw: str) -> list[str]:
    raw = (raw or "*").strip()
    return ["*"] if raw == "*" else [o.strip() for o in raw.split(",") if o.strip()]


_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(_settings.cors_origin),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


@app.get("/api/analyze")
async def analyze_endpoint(repo_url: str = Query(..., description="GitHub repository URL")):
    # Validate the URL synchronously — bad input returns HTTP 400 before streaming.
    try:
        parse_repo_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def stream() -> AsyncIterator[str]:
        try:
            async for evt in analyze(repo_url):
                yield sse(evt["event"], evt["data"])
        except RepoNotFound as e:
            yield sse("error", {"message": str(e), "code": "not_found"})
        except GitHubRateLimit as e:
            yield sse("error", {"message": str(e), "code": "rate_limit"})
        except GitHubError as e:
            yield sse("error", {"message": str(e), "code": "github_error"})
        except Exception as e:  # noqa: BLE001 — last-resort SSE error
            yield sse("error", {"message": f"{type(e).__name__}: {e}"})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
