"""Per-ecosystem source fetchers. Each returns:
  - resolve_repo(package) -> "owner/repo" | None     (so we can hit GitHub Releases)
  - list_versions(package) -> list[str]
"""
from __future__ import annotations

import re
from typing import Optional

import httpx

from .cache import get as cache_get, put as cache_put

GITHUB_RE = re.compile(r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:[/#?]|$)", re.I)


def _http_get(url: str, timeout: float = 12.0) -> Optional[str]:
    cached = cache_get(url)
    if cached is not None:
        return cached
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={
            "User-Agent": "mcp-changelog/0.1",
            "Accept": "application/json",
        })
        r.raise_for_status()
    except Exception:
        return None
    body = r.text
    cache_put(url, body)
    return body


def _parse_github_url(url: str) -> Optional[str]:
    if not url:
        return None
    m = GITHUB_RE.search(url)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}"


# ---------- npm ----------

def npm_resolve_repo(package: str) -> Optional[str]:
    body = _http_get(f"https://registry.npmjs.org/{package}")
    if not body:
        return None
    try:
        import json
        data = json.loads(body)
    except Exception:
        return None
    repo = data.get("repository") or {}
    if isinstance(repo, dict):
        return _parse_github_url(repo.get("url", ""))
    if isinstance(repo, str):
        return _parse_github_url(repo)
    return None


def npm_list_versions(package: str) -> list[str]:
    body = _http_get(f"https://registry.npmjs.org/{package}")
    if not body:
        return []
    try:
        import json
        data = json.loads(body)
    except Exception:
        return []
    return list((data.get("versions") or {}).keys())


# ---------- PyPI ----------

def pypi_resolve_repo(package: str) -> Optional[str]:
    body = _http_get(f"https://pypi.org/pypi/{package}/json")
    if not body:
        return None
    try:
        import json
        data = json.loads(body)
    except Exception:
        return None
    info = data.get("info") or {}
    urls = info.get("project_urls") or {}
    candidates = list(urls.values()) + [info.get("home_page", ""), info.get("project_url", "")]
    for u in candidates:
        repo = _parse_github_url(u or "")
        if repo:
            return repo
    return None


def pypi_list_versions(package: str) -> list[str]:
    body = _http_get(f"https://pypi.org/pypi/{package}/json")
    if not body:
        return []
    try:
        import json
        data = json.loads(body)
    except Exception:
        return []
    return list((data.get("releases") or {}).keys())


# ---------- GitHub Releases ----------

def gh_releases(repo: str, max_pages: int = 5) -> list[dict]:
    """Returns list of {tag_name, name, body, published_at}."""
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
        body = _http_get(url)
        if not body:
            break
        try:
            import json
            data = json.loads(body)
        except Exception:
            break
        if not isinstance(data, list) or not data:
            break
        for rel in data:
            out.append({
                "tag_name": rel.get("tag_name", ""),
                "name": rel.get("name", "") or rel.get("tag_name", ""),
                "body": rel.get("body", "") or "",
                "published_at": rel.get("published_at", ""),
            })
        if len(data) < 100:
            break
    return out


def gh_get_file(repo: str, paths: list[str], ref: Optional[str] = None) -> Optional[str]:
    """Try each path; return first hit. Uses raw.githubusercontent."""
    for branch in ([ref] if ref else ["main", "master"]):
        for path in paths:
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
            body = _http_get(url)
            if body and "<!DOCTYPE" not in body[:200]:  # raw returns 404 HTML otherwise
                return body
    return None


# ---------- registry router ----------

def resolve_repo(ecosystem: str, package: str) -> Optional[str]:
    eco = ecosystem.lower()
    if eco == "npm":
        return npm_resolve_repo(package)
    if eco in ("pypi", "py", "python"):
        return pypi_resolve_repo(package)
    if eco == "github":
        return package  # already owner/repo
    return None


def list_versions(ecosystem: str, package: str) -> list[str]:
    eco = ecosystem.lower()
    if eco == "npm":
        return npm_list_versions(package)
    if eco in ("pypi", "py", "python"):
        return pypi_list_versions(package)
    return []
