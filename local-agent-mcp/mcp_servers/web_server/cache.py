"""Disk-based cache for fetched web pages, keyed by URL hash."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Optional


class DiskCache:
    """Simple file-system cache. Each entry is a JSON file named by the SHA-256
    of the URL containing {url, fetched_at, content, content_type}."""

    def __init__(self, cache_dir: str = "data/cache", max_age_hours: float = 24.0) -> None:
        self.cache_dir = pathlib.Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_seconds = max_age_hours * 3600

    @staticmethod
    def _url_hash(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _path_for(self, url: str) -> pathlib.Path:
        return self.cache_dir / f"{self._url_hash(url)}.json"

    def get(self, url: str) -> Optional[dict]:
        """Return cached entry or None if missing / expired."""
        path = self._path_for(url)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        age = time.time() - data.get("fetched_at", 0)
        if age > self.max_age_seconds:
            path.unlink(missing_ok=True)
            return None
        return data

    def put(self, url: str, content: str, content_type: str = "text/html") -> dict:
        """Store content for *url* and return the entry dict."""
        entry = {
            "url": url,
            "fetched_at": time.time(),
            "content": content,
            "content_type": content_type,
        }
        path = self._path_for(url)
        path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        return entry

    def has(self, url: str) -> bool:
        return self.get(url) is not None

    def clear(self) -> int:
        """Remove all cached files. Returns count removed."""
        removed = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink(missing_ok=True)
            removed += 1
        return removed
