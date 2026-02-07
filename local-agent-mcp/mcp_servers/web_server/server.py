#!/usr/bin/env python3
"""MCP server exposing web tools (search, fetch, extract, chunk, cache)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports resolve when run via stdio
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_servers.web_server import tools as web_tools

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
server = Server("mcp-web")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description=(
                "Search the web via a local SearXNG instance. "
                "Returns a list of {title, url, snippet} results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Max results to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="fetch_url",
            description=(
                "Fetch a web page by URL. Uses disk cache when available. "
                "Returns {url, content, content_type, from_cache}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to check the disk cache first (default true)",
                        "default": True,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="extract_text",
            description=(
                "Extract readable text from raw HTML using readability heuristics. "
                "Returns {title, text, url}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "html": {"type": "string", "description": "Raw HTML content"},
                    "url": {"type": "string", "description": "Source URL (metadata)", "default": ""},
                },
                "required": ["html"],
            },
        ),
        Tool(
            name="chunk_text",
            description=(
                "Split plain text into overlapping word-based chunks for embedding. "
                "Returns list of {chunk_id, text, url, title, char_start, char_end}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Plain text to chunk"},
                    "chunk_size": {
                        "type": "integer",
                        "description": "Words per chunk (default 512)",
                        "default": 512,
                    },
                    "overlap": {
                        "type": "integer",
                        "description": "Overlap in words (default 64)",
                        "default": 64,
                    },
                    "url": {"type": "string", "description": "Source URL (metadata)", "default": ""},
                    "title": {"type": "string", "description": "Document title (metadata)", "default": ""},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="clear_cache",
            description="Remove all entries from the disk cache.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="cache_status",
            description="Check if a specific URL is currently cached.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to check"},
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "web_search":
            result = await web_tools.web_search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 5),
            )
        elif name == "fetch_url":
            result = await web_tools.fetch_url(
                url=arguments["url"],
                use_cache=arguments.get("use_cache", True),
            )
        elif name == "extract_text":
            result = web_tools.extract_text(
                html=arguments["html"],
                url=arguments.get("url", ""),
            )
        elif name == "chunk_text":
            result = web_tools.chunk_text(
                text=arguments["text"],
                chunk_size=arguments.get("chunk_size", 512),
                overlap=arguments.get("overlap", 64),
                url=arguments.get("url", ""),
                title=arguments.get("title", ""),
            )
        elif name == "clear_cache":
            result = web_tools.clear_cache()
        elif name == "cache_status":
            result = web_tools.cache_status(url=arguments["url"])
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
