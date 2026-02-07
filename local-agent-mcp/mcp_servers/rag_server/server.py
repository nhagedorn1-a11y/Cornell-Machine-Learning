#!/usr/bin/env python3
"""MCP server exposing RAG tools (embed, upsert, query, clear)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_servers.rag_server.faiss_store import FaissStore

# ---------------------------------------------------------------------------
# Singleton store
# ---------------------------------------------------------------------------
_store: FaissStore | None = None


def _get_store() -> FaissStore:
    global _store
    if _store is None:
        _store = FaissStore()
    return _store


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
server = Server("mcp-rag")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="rag_upsert",
            description=(
                "Embed and store text chunks in the FAISS index. "
                "Each chunk needs chunk_id and text; url and title are optional metadata. "
                "Returns {added, total}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chunks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "string"},
                                "text": {"type": "string"},
                                "url": {"type": "string", "default": ""},
                                "title": {"type": "string", "default": ""},
                            },
                            "required": ["chunk_id", "text"],
                        },
                        "description": "List of text chunks to embed and store",
                    },
                },
                "required": ["chunks"],
            },
        ),
        Tool(
            name="rag_query",
            description=(
                "Query the FAISS index with a natural-language question. "
                "Returns the top-k most similar chunks with metadata and similarity scores."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language query"},
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="rag_count",
            description="Return the number of chunks currently stored in the FAISS index.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="rag_clear",
            description="Clear the entire FAISS index and metadata. Use with caution.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    store = _get_store()
    try:
        if name == "rag_upsert":
            result = store.upsert(arguments["chunks"])
        elif name == "rag_query":
            results = store.query(
                query_text=arguments["query"],
                top_k=arguments.get("top_k", 5),
            )
            result = {"query": arguments["query"], "results": results}
        elif name == "rag_count":
            result = {"total": store.count()}
        elif name == "rag_clear":
            result = store.clear()
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
