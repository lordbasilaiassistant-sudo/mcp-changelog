# mcp-changelog

> MCP server that diffs package versions and surfaces what will break in your code — for AI coding agents that need to upgrade safely.

When Claude Code, Cursor, or any agentic-coding tool runs `npm outdated` or `pip list --outdated`, it sees 12 packages behind and faces a choice: blindly bump and break the build, or burn 30k tokens reading release notes one-by-one. **Most agents pick "blindly bump."**

This MCP server gives them a third option: **structured diff between version A and B, with the actual breaking changes pulled from the package's release notes, plus a regex scan of your code to flag what will break.**

No LLM in the loop — pure HTTP + regex. Cached locally. Works on Windows, macOS, Linux. Free.

## Tools

| Tool | What it does |
|---|---|
| `get_changelog(ecosystem, package, from_version, to_version)` | Returns markdown of every release between two versions, **BREAKING / REMOVED / DEPRECATED** lines surfaced at the top. |
| `get_migration_guide(ecosystem, package, version_tag?)` | Fetches `MIGRATING.md` / `UPGRADING.md` / `CHANGELOG.md` from the package's GitHub repo. |
| `analyze_upgrade(ecosystem, package, from_version, to_version, code)` | Scans your code for symbols mentioned in breaking notes. Returns `{"affected_lines": [{symbol, line, code}, ...]}` so the agent knows exactly where to look. |

Supported ecosystems: `npm`, `pypi`, `github` (`package` = `"owner/repo"` for github).

## Install

### `uvx` (no install, ephemeral)
```bash
uvx mcp-changelog
```

### PyPI
```bash
pip install mcp-changelog
mcp-changelog
```

### npm wrapper (shells out to uvx under the hood)
```bash
npx mcp-changelog
```

## Wire into Claude Code

`~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "changelog": {
      "command": "uvx",
      "args": ["mcp-changelog"]
    }
  }
}
```

Then in Claude Code:
> "Before bumping react from 18.2 to 19.0 in this file, use the changelog MCP to check what breaks."

Claude calls `analyze_upgrade("npm", "react", "18.2.0", "19.0.0", <file>)` and gets back the exact lines that need attention.

## Wire into Cursor / Continue / any MCP-aware agent

Same `command` + `args`. The MCP protocol is universal.

## Optional: GitHub token

GitHub's unauthenticated API is 60 requests/hour. Plenty for occasional use, but if you're hammering it, set:
```bash
export GITHUB_TOKEN=ghp_yourtoken   # 5000 req/hr
```

## Why this exists

I'm Anthony Snider — autistic+ADHD father of 6, building autonomous AI tools because I can't people. Every time I let an agent upgrade my dependencies, I'd find out 30 minutes later it had silently introduced 3 breaking changes I didn't notice. Every. Time.

So I built this. Free, MIT, runs locally.

## Support the project

If this saves you a debugging session, consider [sponsoring on GitHub](https://github.com/sponsors/lordbasilaiassistant-sudo). Donations keep the lights on so I can keep shipping free dev tools.

## License

MIT.
