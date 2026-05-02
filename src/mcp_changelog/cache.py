"""On-disk cache for HTTP responses. Cheap. Stays out of the way."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(os.path.expanduser("~/.cache/mcp-changelog"))
DEFAULT_TTL_SECONDS = 6 * 60 * 60  # 6h — package metadata moves slowly


def _key(url: str) -> Path:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.json"


def get(url: str, ttl: int = DEFAULT_TTL_SECONDS) -> str | None:
    p = _key(url)
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if time.time() - obj.get("ts", 0) > ttl:
        return None
    return obj.get("body")


def put(url: str, body: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _key(url)
    p.write_text(json.dumps({"ts": time.time(), "body": body}), encoding="utf-8")
