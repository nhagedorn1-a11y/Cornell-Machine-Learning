"""MCP client orchestrator: routes user prompts through MCP tools and LM Studio.

Flow:
  1. Parse the user prompt for intent (web search, URL ingest, or plain question)
  2. Call MCP tools to gather evidence
  3. Build a context pack with sources
  4. Call Nemotron via LM Studio with citation rules
  5. Return {reply, sources, debug} JSON
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .lmstudio_client import LMStudioClient
from .prompts import build_evidence_prompt, SYSTEM_NO_EVIDENCE, SYSTEM_INGEST_CONFIRM

logger = logging.getLogger("orchestrator")

# Regex for URLs in user input
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# Default retrieval trigger words
_DEFAULT_TRIGGERS = [
    "latest", "new developments", "what's new", "today",
    "this week", "update", "recent", "current", "now",
    "breaking", "just released",
]


class Orchestrator:
    """Central coordinator: MCP client + routing + LM Studio calls."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

        # LM Studio client
        lm_cfg = config.get("lmstudio", {})
        self.llm = LMStudioClient(
            base_url=lm_cfg.get("base_url", "http://localhost:1234/v1"),
            model=lm_cfg.get("model", "nemotron-nano-30b"),
            max_tokens=lm_cfg.get("max_tokens", 2048),
            temperature=lm_cfg.get("temperature", 0.3),
            timeout_seconds=lm_cfg.get("timeout_seconds", 120),
        )

        # MCP server configs
        mcp_cfg = config.get("mcp_servers", {})
        self._web_server_params = self._build_server_params(mcp_cfg.get("web", {}))
        self._rag_server_params = self._build_server_params(mcp_cfg.get("rag", {}))

        # SearXNG config
        searx_cfg = config.get("searxng", {})
        self.searxng_enabled: bool = searx_cfg.get("enabled", False)
        self.searxng_url: str = searx_cfg.get("base_url", "http://localhost:8080")
        self.searxng_max_results: int = searx_cfg.get("max_results", 5)

        # Retrieval triggers
        self.triggers: list[str] = config.get("retrieval_triggers", _DEFAULT_TRIGGERS)

        # RAG top_k
        faiss_cfg = config.get("faiss", {})
        self.top_k: int = faiss_cfg.get("top_k", 5)

    @staticmethod
    def _build_server_params(cfg: dict) -> StdioServerParameters:
        command = cfg.get("command", sys.executable)
        args = cfg.get("args", [])
        return StdioServerParameters(command=command, args=args)

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------
    def _detect_urls(self, prompt: str) -> list[str]:
        return _URL_RE.findall(prompt)

    def _needs_web_search(self, prompt: str) -> bool:
        lower = prompt.lower()
        return any(t in lower for t in self.triggers)

    # ------------------------------------------------------------------
    # MCP tool calls
    # ------------------------------------------------------------------
    async def _call_mcp_tool(
        self,
        server_params: StdioServerParameters,
        tool_name: str,
        arguments: dict,
    ) -> Any:
        """Spawn an MCP server via stdio, call one tool, return parsed JSON."""
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                # Extract text from result content
                text_parts = []
                for block in result.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                raw = "".join(text_parts)
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"raw": raw}

    async def _web_search(self, query: str) -> list[dict]:
        return await self._call_mcp_tool(
            self._web_server_params,
            "web_search",
            {"query": query, "max_results": self.searxng_max_results},
        )

    async def _fetch_url(self, url: str) -> dict:
        return await self._call_mcp_tool(
            self._web_server_params,
            "fetch_url",
            {"url": url},
        )

    async def _extract_text(self, html: str, url: str = "") -> dict:
        return await self._call_mcp_tool(
            self._web_server_params,
            "extract_text",
            {"html": html, "url": url},
        )

    async def _chunk_text(self, text: str, url: str = "", title: str = "") -> list[dict]:
        return await self._call_mcp_tool(
            self._web_server_params,
            "chunk_text",
            {"text": text, "url": url, "title": title},
        )

    async def _rag_upsert(self, chunks: list[dict]) -> dict:
        return await self._call_mcp_tool(
            self._rag_server_params,
            "rag_upsert",
            {"chunks": chunks},
        )

    async def _rag_query(self, query: str, top_k: int = 5) -> dict:
        return await self._call_mcp_tool(
            self._rag_server_params,
            "rag_query",
            {"query": query, "top_k": top_k},
        )

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------
    async def _ingest_url(self, url: str, debug: list[dict]) -> dict:
        """Fetch → extract → chunk → upsert for a single URL.
        Returns {url, title, chunks_added} or {url, error}.
        """
        debug.append({"tool": "fetch_url", "args": {"url": url}})
        fetch_result = await self._fetch_url(url)

        if fetch_result.get("error"):
            return {"url": url, "error": fetch_result["error"]}

        html = fetch_result.get("content", "")
        if not html.strip():
            return {"url": url, "error": "Empty content"}

        debug.append({"tool": "extract_text", "args": {"url": url}})
        extracted = await self._extract_text(html, url)
        text = extracted.get("text", "")
        title = extracted.get("title", "")

        if not text.strip():
            return {"url": url, "error": "No readable text extracted"}

        debug.append({"tool": "chunk_text", "args": {"url": url, "title": title}})
        chunks = await self._chunk_text(text, url, title)

        if not chunks:
            return {"url": url, "error": "No chunks produced"}

        debug.append({"tool": "rag_upsert", "args": {"num_chunks": len(chunks)}})
        upsert_result = await self._rag_upsert(chunks)

        return {
            "url": url,
            "title": title,
            "chunks_added": upsert_result.get("added", 0),
        }

    async def _search_and_ingest(self, query: str, debug: list[dict]) -> list[dict]:
        """Web search → fetch top results → ingest. Returns ingest summaries."""
        debug.append({"tool": "web_search", "args": {"query": query}})
        search_results = await self._web_search(query)

        if not search_results:
            debug.append({"note": "web_search returned no results (SearXNG may be offline)"})
            return []

        ingest_tasks = []
        for sr in search_results:
            url = sr.get("url", "")
            if url:
                ingest_tasks.append(self._ingest_url(url, debug))

        if not ingest_tasks:
            return []

        return await asyncio.gather(*ingest_tasks)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def process(self, prompt: str) -> dict[str, Any]:
        """Process a user prompt end-to-end.

        Returns:
            {
                "reply": str,
                "sources": list[dict],
                "debug": list[dict],
            }
        """
        debug: list[dict] = []
        urls_in_prompt = self._detect_urls(prompt)
        needs_search = self._needs_web_search(prompt) and self.searxng_enabled

        # Step 1: Ingest any URLs found in the prompt
        ingest_summaries: list[dict] = []
        if urls_in_prompt:
            debug.append({"stage": "url_ingestion", "urls": urls_in_prompt})
            tasks = [self._ingest_url(u, debug) for u in urls_in_prompt]
            ingest_summaries = await asyncio.gather(*tasks)

        # Step 2: Web search if triggered
        search_summaries: list[dict] = []
        if needs_search:
            debug.append({"stage": "web_search", "query": prompt})
            search_summaries = await self._search_and_ingest(prompt, debug)
            if isinstance(search_summaries, list):
                ingest_summaries.extend(search_summaries)

        # Step 3: Always query RAG for evidence
        debug.append({"tool": "rag_query", "args": {"query": prompt, "top_k": self.top_k}})
        rag_result = await self._rag_query(prompt, self.top_k)
        evidence_items = rag_result.get("results", [])
        debug.append({"rag_results_count": len(evidence_items)})

        # Step 4: Build prompt for LLM
        system_prompt, sources_json = build_evidence_prompt(evidence_items)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        # Step 5: Call LM Studio
        debug.append({"stage": "llm_call", "model": self.llm.model})
        try:
            reply = await self.llm.chat(messages)
        except Exception as exc:
            reply = f"Error calling LM Studio: {exc}"
            debug.append({"error": str(exc)})

        sources = json.loads(sources_json)

        return {
            "reply": reply,
            "sources": sources,
            "debug": debug,
        }

    async def health(self) -> dict[str, Any]:
        """Check system health: LM Studio connectivity + MCP server availability."""
        lm_health = await self.llm.health_check()

        # Quick MCP test: try listing tools
        web_ok = False
        rag_ok = False
        try:
            async with stdio_client(self._web_server_params) as (r, w):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    web_ok = len(tools.tools) > 0
        except Exception as exc:
            logger.warning("mcp-web health check failed: %s", exc)

        try:
            async with stdio_client(self._rag_server_params) as (r, w):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    rag_ok = len(tools.tools) > 0
        except Exception as exc:
            logger.warning("mcp-rag health check failed: %s", exc)

        return {
            "lmstudio": lm_health,
            "mcp_web": "ok" if web_ok else "error",
            "mcp_rag": "ok" if rag_ok else "error",
            "searxng_enabled": self.searxng_enabled,
        }
