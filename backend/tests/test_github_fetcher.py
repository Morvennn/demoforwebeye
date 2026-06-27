# Daniel Design
import base64
from urllib.parse import unquote

import httpx
import pytest
import respx

from app.github import GitHubError, RepoFetcher, RepoNotFound

API = "https://api.github.com"

META = {
    "html_url": "https://github.com/o/r",
    "description": "a test repo",
    "stargazers_count": 42,
    "forks_count": 7,
    "open_issues_count": 3,
    "default_branch": "main",
    "license": {"spdx_id": "MIT"},
    "pushed_at": "2025-01-01T00:00:00Z",
}
LANGS = {"Python": 9000, "HTML": 1000}
TREE = {
    "tree": [
        {"path": "main.py", "type": "blob", "size": 500},
        {"path": "README.md", "type": "blob", "size": 100},
        {"path": "requirements.txt", "type": "blob", "size": 12},
        {"path": ".github/CONTRIBUTING.md", "type": "blob", "size": 20},
        {"path": "pkg", "type": "tree"},
    ]
}


def _readme() -> dict:
    return {"content": base64.b64encode(b"# Title\n\nSome readme body.").decode(), "encoding": "base64"}


def _contents_handler(request: httpx.Request) -> httpx.Response:
    path = unquote(request.url.path.rsplit("/contents/", 1)[1])
    body = f"# content of {path}"
    return httpx.Response(200, json={"content": base64.b64encode(body.encode()).decode(), "encoding": "base64"})


@respx.mock
async def test_fetch_all_happy_path():
    respx.get(f"{API}/repos/o/r").mock(return_value=httpx.Response(200, json=META))
    respx.get(f"{API}/repos/o/r/languages").mock(return_value=httpx.Response(200, json=LANGS))
    respx.get(f"{API}/repos/o/r/readme").mock(return_value=httpx.Response(200, json=_readme()))
    respx.get(url__startswith=f"{API}/repos/o/r/git/trees/").mock(return_value=httpx.Response(200, json=TREE))
    respx.get(url__startswith=f"{API}/repos/o/r/contents/").mock(side_effect=_contents_handler)

    async with RepoFetcher() as fetcher:
        data = await fetcher.fetch_all("o", "r")

    assert data.meta.stars == 42
    assert data.meta.license == "MIT"
    assert data.meta.has_contributing is True
    assert data.meta.languages["Python"] == 9000
    assert data.readme.startswith("# Title")
    # manifests first, then largest code file
    assert set(data.key_files) == {"requirements.txt", "main.py"}
    assert "main.py" in data.tree


@respx.mock
async def test_fetch_all_repo_not_found():
    respx.get(url__startswith=f"{API}/repos/o/r").mock(return_value=httpx.Response(404, json={"message": "Not Found"}))
    async with RepoFetcher() as fetcher:
        with pytest.raises(RepoNotFound):
            await fetcher.fetch_all("o", "r")


@respx.mock
async def test_fetch_all_rate_limit():
    respx.get(url__startswith=f"{API}/repos/o/r").mock(
        return_value=httpx.Response(403, json={"message": "API rate limit exceeded"})
    )
    async with RepoFetcher() as fetcher:
        with pytest.raises(GitHubError):
            await fetcher.fetch_all("o", "r")
