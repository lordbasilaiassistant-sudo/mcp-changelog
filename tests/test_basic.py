"""Smoke tests. Hit real registries — skip if offline.

Run:  pytest tests/ -v
"""
from __future__ import annotations

import pytest

from mcp_changelog import sources, version, analyze


# ---------- version.py ----------

def test_version_normalize():
    assert version.normalize("v1.2.3") == "1.2.3"
    assert version.normalize("V1.2.3") == "1.2.3"
    assert version.normalize("1.2.3") == "1.2.3"


def test_version_cmp_basic():
    assert version.cmp("1.2.3", "1.2.4") == -1
    assert version.cmp("2.0.0", "1.99.99") == 1
    assert version.cmp("1.0.0", "1.0.0") == 0


def test_version_cmp_pre_release():
    assert version.cmp("1.0.0-rc.1", "1.0.0") == -1
    assert version.cmp("1.0.0-alpha", "1.0.0-beta") == -1


def test_version_cmp_v_prefix():
    assert version.cmp("v18.2.0", "v18.3.0") == -1


# ---------- analyze.py ----------

def test_extract_breaking_lines_inline():
    text = """Some change here.
- BREAKING: removed `oldFunction`
* BREAKING CHANGE: renamed Foo to Bar
- Just a normal bullet
- DEPRECATED: useLegacy is gone
"""
    lines = analyze.extract_breaking_lines(text)
    assert any("oldFunction" in l for l in lines)
    assert any("Foo to Bar" in l for l in lines)
    assert any("useLegacy" in l for l in lines)


def test_extract_breaking_lines_section():
    text = """## What's New
Some new features

## Breaking Changes
- The `setState` callback no longer fires synchronously
- Removed `componentWillMount`

## Bug Fixes
- something
"""
    lines = analyze.extract_breaking_lines(text)
    assert any("setState" in l for l in lines)
    assert any("componentWillMount" in l for l in lines)


def test_extract_symbols_filters_noise():
    text = "BREAKING: the deprecated api was removed and renamed to newApi"
    syms = analyze.extract_symbols(text)
    # noise-words filtered
    assert "the" not in syms
    assert "and" not in syms
    # real symbols kept
    assert any("newApi" in s or s == "newApi" for s in syms)


def test_find_affected_basic():
    code = """import React from 'react'
const x = oldFunction()
console.log(newApi.foo())
"""
    hits = analyze.find_affected(code, ["oldFunction", "newApi.foo"])
    syms = {h["symbol"] for h in hits}
    assert "oldFunction" in syms
    assert "newApi.foo" in syms


# ---------- sources.py ----------

def _online() -> bool:
    """Quick connectivity check."""
    import httpx
    try:
        httpx.get("https://registry.npmjs.org/", timeout=3)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _online(), reason="offline")
def test_npm_resolve_repo_real():
    repo = sources.npm_resolve_repo("react")
    # react's repo is facebook/react (or similar)
    assert repo is not None
    assert "/" in repo


@pytest.mark.skipif(not _online(), reason="offline")
def test_pypi_resolve_repo_real():
    repo = sources.pypi_resolve_repo("requests")
    assert repo is not None
    assert "/" in repo


@pytest.mark.skipif(not _online(), reason="offline")
def test_npm_list_versions_has_known_version():
    versions = sources.npm_list_versions("react")
    assert "18.2.0" in versions
