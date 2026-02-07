"""Core web tools: search, fetch, extract, chunk."""

from __future__ import annotations

import re
import textwrap
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDocument

from .cache import DiskCache

_FETCH_TIMEOUT = 20.0
_MAX_CONTENT_LENGTH = 500_000  # ~500 KB text limit

_cache = DiskCache()


def configure_cache(cache_dir: str = "data/cache", max_age_hours: float = 24.0) -> None:
    """Reconfigure the module-level cache."""
    global _cache
    _cache = DiskCache(cache_dir=cache_dir, max_age_hours=max_age_hours)


async def web_search(query: str, searxng_url: str = "http://localhost:8080", max_results: int = 5) -> list[dict]:
    """Search via a local SearXNG instance. Returns list of {title, url, snippet}.

    If SearXNG is unreachable, returns an empty list (graceful degradation).
    """
    try:
        async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT) as client:
            resp = await client.get(
                f"{searxng_url}/search",
                params={"q": query, "format": "json", "categories": "general"},
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException, Exception):
        return []

    results: list[dict] = []
    for r in data.get("results", [])[:max_results]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
        })
    return results


async def fetch_url(url: str, use_cache: bool = True) -> dict:
    """Fetch a URL and return {url, content, content_type, from_cache}.

    Checks disk cache first. Stores successful fetches.
    """
    if use_cache:
        cached = _cache.get(url)
        if cached is not None:
            return {
                "url": url,
                "content": cached["content"],
                "content_type": cached.get("content_type", "text/html"),
                "from_cache": True,
            }

    headers = {
        "User-Agent": "LocalAgentMCP/1.0 (research bot; +https://github.com/local-agent-mcp)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        return {"url": url, "content": "", "content_type": "", "error": str(exc), "from_cache": False}

    content_type = resp.headers.get("content-type", "text/html")
    text = resp.text[:_MAX_CONTENT_LENGTH]

    _cache.put(url, text, content_type)
    return {"url": url, "content": text, "content_type": content_type, "from_cache": False}


def extract_text(html: str, url: str = "") -> dict:
    """Extract readable text from HTML using readability + BeautifulSoup.

    Returns {title, text, url}.
    """
    if not html.strip():
        return {"title": "", "text": "", "url": url}

    try:
        doc = ReadabilityDocument(html)
        title = doc.title() or ""
        summary_html = doc.summary()
    except Exception:
        title = ""
        summary_html = html

    soup = BeautifulSoup(summary_html, "lxml")

    # Remove scripts, styles, navs
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse whitespace runs
    text = re.sub(r"\n{3,}", "\n\n", text)

    return {"title": title, "text": text, "url": url}


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    url: str = "",
    title: str = "",
) -> list[dict]:
    """Split text into overlapping word-based chunks.

    Returns list of {chunk_id, text, url, title, char_start, char_end}.
    """
    if not text.strip():
        return []

    words = text.split()
    chunks: list[dict] = []
    idx = 0
    chunk_id = 0

    while idx < len(words):
        end = min(idx + chunk_size, len(words))
        chunk_words = words[idx:end]
        chunk_text_str = " ".join(chunk_words)

        # Approximate char positions
        char_start = len(" ".join(words[:idx]))
        char_end = char_start + len(chunk_text_str)

        chunks.append({
            "chunk_id": f"{urlparse(url).netloc or 'local'}_{chunk_id}",
            "text": chunk_text_str,
            "url": url,
            "title": title,
            "char_start": char_start,
            "char_end": char_end,
        })
        chunk_id += 1

        if end >= len(words):
            break
        idx = end - overlap

    return chunks


def clear_cache() -> dict:
    """Clear the disk cache. Returns {removed: int}."""
    removed = _cache.clear()
    return {"removed": removed}


def cache_status(url: str) -> dict:
    """Check if a URL is in the cache."""
    return {"url": url, "cached": _cache.has(url)}
