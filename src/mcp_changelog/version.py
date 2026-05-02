"""Version comparison without external deps. Handles SemVer-ish + PEP440-ish."""
from __future__ import annotations

import re

VERSION_PART_RE = re.compile(r"(\d+)|([a-zA-Z]+)")


def normalize(v: str) -> str:
    v = v.strip()
    if v.startswith(("v", "V")):
        v = v[1:]
    return v


def parse(v: str) -> tuple:
    """Parse a version string into a comparable tuple. Best-effort SemVer.

    Returns (release_parts, pre_release_marker, pre_release_parts)
    where pre_release_marker = 1 for stable release, 0 for pre-release.
    Tuple comparison: (1, ...) > (0, ...), so 1.0.0 > 1.0.0-rc.1 (correct SemVer).
    """
    v = normalize(v)
    # split off pre-release / build metadata
    main, _, pre = v.partition("-")
    main = main.partition("+")[0]   # drop build metadata
    pre = pre.partition("+")[0]

    release_parts: list = []
    for chunk in main.split("."):
        if not chunk:
            continue
        for m in VERSION_PART_RE.finditer(chunk):
            num, letters = m.groups()
            if num is not None:
                release_parts.append((0, int(num)))
            else:
                release_parts.append((-1, letters.lower()))

    pre_marker = 1 if not pre else 0   # 1 = stable; 0 = pre-release (sorts lower)

    pre_parts: list = []
    if pre:
        for chunk in pre.split("."):
            for m in VERSION_PART_RE.finditer(chunk):
                num, letters = m.groups()
                if num is not None:
                    pre_parts.append((1, int(num)))   # numeric pre-release id
                else:
                    pre_parts.append((0, letters.lower()))   # alphanumeric pre-release id
    return (tuple(release_parts), pre_marker, tuple(pre_parts))


def cmp(a: str, b: str) -> int:
    pa, pb = parse(a), parse(b)
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def in_range(v: str, lo: str, hi: str, *, inclusive_lo: bool = False, inclusive_hi: bool = True) -> bool:
    """Is v between lo and hi?"""
    cl = cmp(v, lo)
    ch = cmp(v, hi)
    if cl < 0 or (cl == 0 and not inclusive_lo):
        return False
    if ch > 0 or (ch == 0 and not inclusive_hi):
        return False
    return True
