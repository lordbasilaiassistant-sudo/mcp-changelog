# Publish runbook — mcp-changelog

Everything is built and ready. When you have 30 seconds awake, run these.

## 1. PyPI publish (gates everything else)

```powershell
# one-time: mint a token at https://pypi.org/manage/account/token/
# scope to "Project: mcp-changelog" after first upload, "Entire account" for first one
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-AgEIcHlwa..."   # paste your token here

py -m pip install --quiet twine
py -m twine upload dist/*
```

Verify after a minute:
```powershell
py -m pip install mcp-changelog
mcp-changelog --help
```

If the name `mcp-changelog` is taken on PyPI, rename in `pyproject.toml` to `mcp-version-diff` or similar and re-build with `py -m build`.

## 2. npm wrapper (after PyPI is live)

```powershell
cd "C:\Users\drlor\OneDrive\Desktop\mcp-changelog\npm"
npm login                # one-time, opens browser
npm publish --access public
```

(npm wrapper folder will be created next session — it's a tiny shim that shells out to `uvx mcp-changelog`.)

## 3. Submit to MCP awesome-lists (only after PyPI works)

Five PRs, ~10 min each. README install one-liner is `pip install mcp-changelog` or `uvx mcp-changelog`.

```
https://github.com/punkpeye/awesome-mcp-servers
https://github.com/wong2/awesome-mcp-servers
https://github.com/TensorBlock/awesome-mcp-servers
https://github.com/appcypher/awesome-mcp-servers
https://github.com/modelcontextprotocol/registry
```

For each: fork, add a one-line entry under "Developer Tools" or "Package Management" alphabetically, PR.

Sample entry:
```markdown
- [mcp-changelog](https://github.com/lordbasilaiassistant-sudo/mcp-changelog) - Diffs package versions and surfaces breaking changes for AI coding agents. Pure regex, no LLM. Supports npm, PyPI, GitHub.
```

## 4. Healthcare wrapper for the May 11 hackathon

Separate repo: `mcp-fhir` or `mcp-rxnorm`. Reuse the `sources.py` + `cache.py` patterns. One tool: `check_drug_interactions(drugs: list[str])` hitting the free RxNorm or OpenFDA API. Submit to https://agents-assemble.devpost.com/ before May 11 11pm EDT.

## What's already live

- Repo: https://github.com/lordbasilaiassistant-sudo/mcp-changelog
- Tag: v0.1.0
- Local install works: `py -m pip install -e "C:\Users\drlor\OneDrive\Desktop\mcp-changelog"`
- 11/11 tests passing
- Live demo proven against react 18.2.0 → 19.0.0 (caught ReactDOM.render removal)
