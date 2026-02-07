"""Client for LM Studio's OpenAI-compatible API.

Handles chat completions with retry logic and streaming support.
No paid APIs required - communicates only with the local LM Studio server.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class LMStudioClient:
    """Async client for LM Studio's /v1/chat/completions endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "nemotron-nano-30b",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout_seconds

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request and return the assistant message.

        Args:
            messages: List of {role, content} dicts.
            temperature: Override default temperature.
            max_tokens: Override default max_tokens.

        Returns:
            The assistant's reply text.

        Raises:
            httpx.HTTPStatusError: On 4xx/5xx responses.
            httpx.ConnectError: If LM Studio is unreachable after retries.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            resp.raise_for_status()

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    async def health_check(self) -> dict[str, Any]:
        """Check if LM Studio is reachable and return model info."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/models")
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("id", "unknown") for m in data.get("data", [])]
                return {"status": "ok", "models": models}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}
