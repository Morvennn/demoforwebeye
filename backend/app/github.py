"""Fetch repository data via the GitHub REST API (no git clone)."""
# Daniel Design

import base64
import re
from dataclasses import dataclass, field

import httpx

from .config import get_settings
from .models import RepoMeta

GITHUB_API = "https://api.github.com"

# Extensions considered "source code" for picking representative files.
CODE_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go",
    ".rs", ".c", ".h", ".cpp", ".cc", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".scala", ".clj", ".ex", ".exs", ".erl", ".lua", ".r", ".dart", ".vue", ".svelte",
}
# Manifests / configs that are cheap signal for engineering quality.
MANIFEST_NAMES = {
    "package.json", "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "Pipfile", "poetry.lock", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "build.gradle.kts", "Gemfile", "composer.json", "Dockerfile", "Makefile",
    "tsconfig.json", ".eslintrc", ".eslintrc.json", ".pre-commit-config.yaml",
}


class GitHubError(Exception):
    pass


class RepoNotFound(GitHubError):
    pass


class GitHubRateLimit(GitHubError):
    pass


def parse_repo_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL.

    Accepts https://github.com/o/r, with optional .git, trailing path
    (/tree/main/...), query, or a bare github.com/o/r form.
    Raises ``ValueError`` if it doesn't look like a GitHub repo URL.
    """
    url = (url or "").strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?(?:/|$|\?|#)", url)
    if not m:
        raise ValueError(f"Not a valid GitHub repository URL: {url!r}")
    owner, repo = m.group(1), m.group(2)
    if owner.lower() in {"orgs", "users"}:
        raise ValueError(f"Not a valid GitHub repository URL: {url!r}")
    return owner, repo


@dataclass
class RepoData:
    meta: RepoMeta
    readme: str | None
    tree: list[str] = field(default_factory=list)
    key_files: dict[str, str] = field(default_factory=dict)


class RepoFetcher:
    """Async GitHub API client. Pass an ``httpx.AsyncClient`` (e.g. a respx-mocked
    one) for tests; otherwise it creates and owns its own."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "repo-health-check",
        }
        token = get_settings().github_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._owns = client is None
        self._client = client or httpx.AsyncClient(headers=headers, timeout=30.0)

    async def __aenter__(self) -> "RepoFetcher":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns:
            await self._client.aclose()

    async def _get(self, path: str) -> httpx.Response:
        resp = await self._client.get(f"{GITHUB_API}{path}")
        if resp.status_code == 404:
            raise RepoNotFound(f"Not found: {path}")
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise GitHubRateLimit("GitHub API rate limit exceeded (set GITHUB_TOKEN).")
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GitHubError(f"GitHub API error {resp.status_code} for {path}") from exc
        return resp

    async def fetch_all(self, owner: str, repo: str) -> RepoData:
        meta = await self._fetch_meta(owner, repo)
        readme, tree_items = await _gather(
            self._fetch_readme(owner, repo),
            self._fetch_tree(owner, repo, meta.default_branch),
        )
        meta.has_contributing = _has_contributing(tree_items)
        key_files = await self._fetch_key_files(owner, repo, tree_items)
        tree = [p["path"] for p in tree_items if p.get("type") == "blob"]
        return RepoData(meta=meta, readme=readme, tree=tree, key_files=key_files)

    async def _fetch_meta(self, owner: str, repo: str) -> RepoMeta:
        data = (await self._get(f"/repos/{owner}/{repo}")).json()
        license_name = (data.get("license") or {}).get("spdx_id") or (data.get("license") or {}).get("name")
        langs = (await self._get(f"/repos/{owner}/{repo}/languages")).json()
        return RepoMeta(
            owner=owner,
            repo=repo,
            url=data.get("html_url", f"https://github.com/{owner}/{repo}"),
            description=data.get("description"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            default_branch=data.get("default_branch", "main"),
            pushed_at=data.get("pushed_at"),
            license=license_name,
            languages=dict(langs),
        )

    async def _fetch_readme(self, owner: str, repo: str) -> str | None:
        resp = await self._get(f"/repos/{owner}/{repo}/readme")
        data = resp.json()
        content = data.get("content") or ""
        encoding = data.get("encoding", "base64")
        if encoding == "base64":
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:
                return None
        return content or None

    async def _fetch_tree(self, owner: str, repo: str, branch: str) -> list[dict]:
        resp = await self._get(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        data = resp.json()
        return [t for t in data.get("tree", []) if t.get("type") in {"blob", "tree"}]

    async def _fetch_key_files(
        self, owner: str, repo: str, tree_items: list[dict]
    ) -> dict[str, str]:
        settings = get_settings()
        picks = _select_key_files(tree_items, settings.max_key_files)
        out: dict[str, str] = {}
        for path in picks:
            try:
                resp = await self._get(f"/repos/{owner}/{repo}/contents/{path}")
            except GitHubError:
                continue
            data = resp.json()
            content = data.get("content") or ""
            if data.get("encoding") == "base64":
                try:
                    text = base64.b64decode(content).decode("utf-8", errors="replace")
                except Exception:
                    continue
            else:
                text = content
            out[path] = text[: settings.max_file_chars]
        return out


def _select_key_files(tree_items: list[dict], limit: int) -> list[str]:
    """Pick up to ``limit`` representative files: manifests first, then the
    largest source files by size."""
    blobs = [t for t in tree_items if t.get("type") == "blob"]
    picked: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name not in seen and len(picked) < limit:
            seen.add(name)
            picked.append(name)

    # Manifests/configs first.
    for b in blobs:
        if b["path"].rsplit("/", 1)[-1] in MANIFEST_NAMES:
            add(b["path"])
    # Then largest source files.
    code = [b for b in blobs if "." in b["path"] and b["path"].rsplit(".", 1)[-1] and ("." + b["path"].rsplit(".", 1)[-1].lower()) in CODE_EXT]
    for b in sorted(code, key=lambda x: x.get("size", 0), reverse=True):
        if len(picked) >= limit:
            break
        add(b["path"])
    return picked


def _has_contributing(tree_items: list[dict]) -> bool:
    return any(
        re.search(r"^(\.)?github/.*contributing", p["path"], re.IGNORECASE)
        or p["path"].lower().startswith("contributing")
        for p in tree_items
        if p.get("type") == "blob"
    )


async def _gather(*coros):
    """Like asyncio.gather but local to avoid a top-level import cycle."""
    import asyncio

    return await asyncio.gather(*coros)
