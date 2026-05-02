"""mcp-changelog MCP server.

Three tools for AI coding agents that need to upgrade safely:

  - get_changelog(ecosystem, package, from_version, to_version)
      Returns markdown of every release between two versions, BREAKING lines surfaced.

  - get_migration_guide(ecosystem, package, version)
      Returns MIGRATING.md / UPGRADING.md / CHANGELOG.md content from the package's repo.

  - analyze_upgrade(ecosystem, package, from_version, to_version, code)
      Pure-regex scan of `code` against the breaking-changes symbols mined from release notes.
      Returns "what will break" report with line numbers.

Sources: npm registry, PyPI JSON API, GitHub Releases — all free, no auth required.
GITHUB_TOKEN env var bumps the rate limit if you have it.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from . import sources, version, analyze

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ImportError:
    print(
        "mcp-changelog requires the 'mcp' package. Install with:\n"
        "  pip install mcp-changelog        (PyPI)\n"
        "  uvx mcp-changelog                (no install, ephemeral)\n",
        file=sys.stderr,
    )
    raise

mcp = FastMCP("mcp-changelog")


def _between(versions: list[str], lo: str, hi: str) -> list[str]:
    """All versions strictly > lo and <= hi, ordered ascending."""
    out = [v for v in versions if version.cmp(v, lo) > 0 and version.cmp(v, hi) <= 0]
    out.sort(key=version.parse)
    return out


@mcp.tool()
def get_changelog(
    ecosystem: str,
    package: str,
    from_version: str,
    to_version: str,
) -> str:
    """Diff package versions. Returns markdown of every release between (exclusive) from_version
    and (inclusive) to_version, with BREAKING / REMOVED / DEPRECATED lines surfaced at the top.

    ecosystem: 'npm', 'pypi', or 'github' (in which case `package` is 'owner/repo')
    """
    repo = sources.resolve_repo(ecosystem, package)
    if not repo:
        return f"# Could not resolve repo for `{package}` in `{ecosystem}`\n\n" \
               f"Package not found, no GitHub link, or registry unreachable."

    releases = sources.gh_releases(repo)
    if not releases:
        return f"# No releases found for `{package}` ({repo})\n\n" \
               f"GitHub Releases empty or rate-limited. Set GITHUB_TOKEN to raise the limit."

    # Filter releases by version
    matching = [
        r for r in releases
        if r["tag_name"] and version.cmp(version.normalize(r["tag_name"]), from_version) > 0
        and version.cmp(version.normalize(r["tag_name"]), to_version) <= 0
    ]
    if not matching:
        return f"# No releases between `{from_version}` and `{to_version}` for `{package}`\n\n" \
               f"Verify both versions exist; check `https://github.com/{repo}/releases` directly."

    matching.sort(key=lambda r: version.parse(version.normalize(r["tag_name"])))

    # Collect all breaking lines across releases
    all_breaking: list[tuple[str, str]] = []
    sections: list[str] = []
    for rel in matching:
        breaking = analyze.extract_breaking_lines(rel["body"])
        for b in breaking:
            all_breaking.append((rel["tag_name"], b))
        sections.append(
            f"## {rel['name']}  \n_({rel['published_at']})_\n\n{rel['body'].strip() or '_(no notes)_'}"
        )

    out = [f"# `{package}` changelog: {from_version} -> {to_version}\n",
           f"_Source: https://github.com/{repo}/releases_\n"]
    if all_breaking:
        out.append("## BREAKING CHANGES (across all versions)\n")
        for tag, line in all_breaking:
            out.append(f"- **`{tag}`** — {line}")
        out.append("")
    out.append("---\n")
    out.extend(sections)
    return "\n".join(out)


@mcp.tool()
def get_migration_guide(ecosystem: str, package: str, version_tag: Optional[str] = None) -> str:
    """Fetch MIGRATING.md / UPGRADING.md / CHANGELOG.md from the package's GitHub repo.

    Returns first match found. Optional version_tag scopes to a tagged ref (e.g. 'v18.0.0').
    """
    repo = sources.resolve_repo(ecosystem, package)
    if not repo:
        return f"Could not resolve repo for `{package}` in `{ecosystem}`."

    candidates = [
        "MIGRATING.md", "MIGRATION.md", "UPGRADING.md", "UPGRADE.md",
        "docs/MIGRATING.md", "docs/migration.md", "docs/upgrade.md",
        "CHANGELOG.md", "HISTORY.md", "RELEASES.md",
    ]
    body = sources.gh_get_file(repo, candidates, ref=version_tag)
    if not body:
        return f"No migration/changelog file found in `{repo}` " \
               f"(checked: {', '.join(candidates)})."

    return f"# Migration / changelog from `{repo}`\n\n{body}"


@mcp.tool()
def analyze_upgrade(
    ecosystem: str,
    package: str,
    from_version: str,
    to_version: str,
    code: str,
) -> dict:
    """Scan `code` for symbols that appear in breaking-change notes between two versions.

    Returns:
      {
        "package": "...",
        "from_version": "...",
        "to_version": "...",
        "breaking_symbols": ["foo.bar", "Baz", ...],
        "affected_lines": [{"symbol": "foo", "line": 12, "code": "..."}, ...],
        "summary": "N affected lines across M symbols"
      }
    """
    repo = sources.resolve_repo(ecosystem, package)
    if not repo:
        return {"error": f"Could not resolve repo for {package} in {ecosystem}"}

    releases = sources.gh_releases(repo)
    matching = [
        r for r in releases
        if r["tag_name"] and version.cmp(version.normalize(r["tag_name"]), from_version) > 0
        and version.cmp(version.normalize(r["tag_name"]), to_version) <= 0
    ]
    if not matching:
        return {
            "package": package,
            "from_version": from_version,
            "to_version": to_version,
            "breaking_symbols": [],
            "affected_lines": [],
            "summary": "No releases in range — nothing to analyze.",
        }

    breaking_text = "\n".join(
        line for r in matching for line in analyze.extract_breaking_lines(r["body"])
    )
    symbols = analyze.extract_symbols(breaking_text)
    affected = analyze.find_affected(code, symbols)

    return {
        "package": package,
        "from_version": from_version,
        "to_version": to_version,
        "breaking_symbols": sorted(symbols),
        "affected_lines": affected,
        "summary": f"{len(affected)} affected line(s) across {len(set(h['symbol'] for h in affected))} symbol(s)",
    }


def main() -> None:
    """Entry point for `mcp-changelog` console script and `uvx mcp-changelog`."""
    mcp.run()


if __name__ == "__main__":
    main()
