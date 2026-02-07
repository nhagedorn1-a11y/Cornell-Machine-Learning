#!/usr/bin/env python3
"""Smoke test: verify MCP servers start and tools are callable."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def test_web_server() -> bool:
    """Test that mcp-web starts, lists tools, and can chunk text."""
    print("Testing mcp-web server...")
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_servers" / "web_server" / "server.py")],
    )

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List tools
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                print(f"  Tools: {tool_names}")

                expected = {"web_search", "fetch_url", "extract_text", "chunk_text", "clear_cache", "cache_status"}
                missing = expected - set(tool_names)
                if missing:
                    print(f"  FAIL: Missing tools: {missing}")
                    return False

                # Test chunk_text
                result = await session.call_tool("chunk_text", {
                    "text": "The quick brown fox jumps over the lazy dog. " * 100,
                    "chunk_size": 50,
                    "overlap": 10,
                    "url": "https://example.com",
                    "title": "Test Document",
                })

                text_parts = [b.text for b in result.content if hasattr(b, "text")]
                data = json.loads("".join(text_parts))
                print(f"  chunk_text returned {len(data)} chunks")

                if not isinstance(data, list) or len(data) == 0:
                    print("  FAIL: chunk_text returned no chunks")
                    return False

                print("  OK: mcp-web server works")
                return True

    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False


async def test_rag_server() -> bool:
    """Test that mcp-rag starts, lists tools, and can upsert+query."""
    print("Testing mcp-rag server...")
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_servers" / "rag_server" / "server.py")],
    )

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List tools
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                print(f"  Tools: {tool_names}")

                expected = {"rag_upsert", "rag_query", "rag_count", "rag_clear"}
                missing = expected - set(tool_names)
                if missing:
                    print(f"  FAIL: Missing tools: {missing}")
                    return False

                # Clear index for clean test
                await session.call_tool("rag_clear", {})

                # Upsert test chunks
                chunks = [
                    {"chunk_id": "test_1", "text": "Python is a programming language created by Guido van Rossum.", "url": "https://python.org", "title": "Python"},
                    {"chunk_id": "test_2", "text": "FAISS is a library for efficient similarity search developed by Facebook AI.", "url": "https://faiss.ai", "title": "FAISS"},
                ]
                result = await session.call_tool("rag_upsert", {"chunks": chunks})
                data = json.loads("".join(b.text for b in result.content if hasattr(b, "text")))
                print(f"  Upserted: {data}")

                if data.get("added") != 2:
                    print(f"  FAIL: Expected 2 added, got {data.get('added')}")
                    return False

                # Query
                result = await session.call_tool("rag_query", {"query": "Who created Python?", "top_k": 2})
                data = json.loads("".join(b.text for b in result.content if hasattr(b, "text")))
                results = data.get("results", [])
                print(f"  Query returned {len(results)} results")

                if not results:
                    print("  FAIL: Query returned no results")
                    return False

                # The Python chunk should be the top result
                top_text = results[0].get("text", "")
                if "Python" not in top_text and "Guido" not in top_text:
                    print(f"  WARNING: Top result may not be relevant: {top_text[:80]}")

                # Clean up
                await session.call_tool("rag_clear", {})

                print("  OK: mcp-rag server works")
                return True

    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False


async def main() -> None:
    print("=" * 60)
    print("MCP Server Tool Tests")
    print("=" * 60)

    web_ok = await test_web_server()
    print()
    rag_ok = await test_rag_server()
    print()

    if web_ok and rag_ok:
        print("All MCP tests passed.")
    else:
        failures = []
        if not web_ok:
            failures.append("mcp-web")
        if not rag_ok:
            failures.append("mcp-rag")
        print(f"FAILED: {', '.join(failures)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
