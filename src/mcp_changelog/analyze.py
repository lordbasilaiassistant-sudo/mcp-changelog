"""Pure-regex 'what breaks in your code' analyzer. No LLM."""
from __future__ import annotations

import re
from typing import Iterable

# Patterns that surface breaking changes from release notes.
BREAKING_LINE_RE = re.compile(
    r"^[\s\-*•]*"
    r"(?:\*\*)?"
    r"(?:\[?(?:BREAKING|BREAK|REMOVED|DEPRECATED|MIGRATION)(?: CHANGE| API)?\]?)"
    r"(?:\*\*)?"
    r"[:\s\-]",
    re.IGNORECASE | re.MULTILINE,
)

# Crude API-symbol extractor from breaking lines: identifiers like .foo, foo(), Foo.bar
SYMBOL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*(?:\(|\b)")
NOISE_WORDS = {
    "and", "or", "the", "a", "an", "to", "of", "for", "in", "on", "by", "with",
    "from", "this", "that", "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "do", "does", "did", "will", "would", "should", "could",
    "may", "might", "must", "can", "now", "no", "longer", "default", "previously",
    "removed", "deprecated", "migration", "breaking", "change", "api", "renamed",
    "moved", "split", "merged", "added", "fixed", "changed", "see", "use", "call",
    "we", "you", "they", "it", "if", "when", "while", "after", "before", "since",
    "all", "any", "some", "each", "every", "as", "instead",
}


def extract_breaking_lines(release_body: str) -> list[str]:
    lines = []
    for line in release_body.splitlines():
        if BREAKING_LINE_RE.match(line):
            lines.append(line.strip())
    # also catch "## Breaking Changes" sections — capture next 30 lines until next ##
    in_section = False
    section_lines: list[str] = []
    for line in release_body.splitlines():
        if re.match(r"^\s*#{2,4}\s*(breaking|removals?|deprecat|migration)", line, re.I):
            in_section = True
            continue
        if in_section:
            if re.match(r"^\s*#{2,4}\s+", line):
                in_section = False
                continue
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                section_lines.append(stripped)
    return lines + section_lines


def extract_symbols(text: str) -> set[str]:
    out: set[str] = set()
    for m in SYMBOL_RE.finditer(text):
        sym = m.group(1)
        head = sym.split(".")[0].lower()
        if head in NOISE_WORDS:
            continue
        if len(head) < 3:
            continue
        out.add(sym)
    return out


def find_affected(code: str, symbols: Iterable[str]) -> list[dict]:
    """For each symbol from breaking notes, find lines in code that reference it."""
    hits: list[dict] = []
    code_lines = code.splitlines()
    for sym in symbols:
        # match the LAST segment as identifier (handles `obj.foo` matching just `foo`)
        leaf = sym.split(".")[-1]
        pat = re.compile(r"\b" + re.escape(leaf) + r"\b")
        for i, line in enumerate(code_lines, start=1):
            if pat.search(line):
                hits.append({"symbol": sym, "line": i, "code": line.strip()[:200]})
    return hits
