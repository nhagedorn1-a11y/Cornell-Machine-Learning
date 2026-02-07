#!/usr/bin/env python3
"""Smoke test: verify LM Studio connectivity and basic chat completion."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lmstudio_client import LMStudioClient


async def test_health() -> bool:
    """Check if LM Studio is reachable."""
    client = LMStudioClient()
    result = await client.health_check()
    print(f"Health check: {json.dumps(result, indent=2)}")
    if result["status"] != "ok":
        print("FAIL: LM Studio is not reachable.")
        print("  -> Make sure LM Studio is running with the server started.")
        print(f"  -> Expected at: {client.base_url}")
        return False
    print(f"OK: Found models: {result['models']}")
    return True


async def test_chat() -> bool:
    """Send a simple chat message and verify response."""
    client = LMStudioClient()
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Reply in one sentence."},
        {"role": "user", "content": "What is 2 + 2?"},
    ]
    try:
        reply = await client.chat(messages)
    except Exception as exc:
        print(f"FAIL: Chat request failed: {exc}")
        return False

    if not reply.strip():
        print("FAIL: Empty response from LM Studio.")
        return False

    print(f"OK: Chat response: {reply[:200]}")
    return True


async def main() -> None:
    print("=" * 60)
    print("LM Studio Connectivity Test")
    print("=" * 60)

    health_ok = await test_health()
    if not health_ok:
        sys.exit(1)

    print()
    chat_ok = await test_chat()
    if not chat_ok:
        sys.exit(1)

    print()
    print("All LM Studio tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
