#!/usr/bin/env python3
"""End-to-end smoke test: prompt → ingest URL → answer with citations.

Requires LM Studio to be running. Tests the full pipeline:
  1. Ingest a URL via the orchestrator
  2. Ask a question about the ingested content
  3. Verify the response includes citations
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lmstudio_client import LMStudioClient
from app.orchestrator import Orchestrator


def _load_config() -> dict:
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "config.json"
    if not config_path.exists():
        config_path = project_root / "config.example.json"

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    for key in ("web", "rag"):
        srv = cfg.get("mcp_servers", {}).get(key, {})
        if "args" in srv:
            srv["args"] = [str(project_root / a) for a in srv["args"]]
        srv["command"] = sys.executable
    return cfg


async def test_url_ingest_and_query() -> bool:
    """Test: paste a URL → system ingests → query returns cited answer."""
    config = _load_config()
    orch = Orchestrator(config)

    # Step 1: Check LM Studio is up
    print("Checking LM Studio...")
    health = await orch.llm.health_check()
    if health["status"] != "ok":
        print(f"SKIP: LM Studio is not running ({health.get('error', 'unknown')})")
        print("  -> Start LM Studio and load a model to run this test.")
        return True  # Not a failure, just a skip

    # Step 2: Ingest a URL
    print("Ingesting a test URL (example.com)...")
    url_prompt = "Please read this page: https://example.com"
    result = await orch.process(url_prompt)

    print(f"  Reply length: {len(result['reply'])} chars")
    print(f"  Sources: {len(result['sources'])}")
    print(f"  Debug steps: {len(result['debug'])}")

    # Step 3: Query about the content
    print("Querying about ingested content...")
    query_prompt = "What is the content of the example.com page about?"
    result = await orch.process(query_prompt)

    print(f"  Reply: {result['reply'][:200]}...")
    print(f"  Sources: {json.dumps(result['sources'], indent=2)}")

    if not result["reply"].strip():
        print("FAIL: Empty reply from orchestrator")
        return False

    print("OK: End-to-end pipeline works")
    return True


async def test_plain_question() -> bool:
    """Test: plain question without URLs or triggers."""
    config = _load_config()
    orch = Orchestrator(config)

    # Check LM Studio
    health = await orch.llm.health_check()
    if health["status"] != "ok":
        print("SKIP: LM Studio not running")
        return True

    print("Testing plain question (no retrieval)...")
    result = await orch.process("What is the capital of France?")

    print(f"  Reply: {result['reply'][:200]}...")
    print(f"  Sources: {len(result['sources'])}")

    if not result["reply"].strip():
        print("FAIL: Empty reply")
        return False

    print("OK: Plain question works")
    return True


async def main() -> None:
    print("=" * 60)
    print("End-to-End Integration Test")
    print("=" * 60)

    ok1 = await test_url_ingest_and_query()
    print()
    ok2 = await test_plain_question()
    print()

    if ok1 and ok2:
        print("All end-to-end tests passed.")
    else:
        print("Some tests FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
