"""Stage 1 -- Tokenizer: split a query into analyzable units.

Budget targets:
    target   5 ms
    hard    15 ms
"""

from __future__ import annotations

import re
import time
from typing import Any

from arbiter_triage.models import StageResult

# Pre-compiled pattern: split on whitespace and common punctuation while
# preserving meaningful tokens (e.g. dollar amounts, percentages, decimals).
_SPLIT_RE = re.compile(
    r"""
    (?:                         # non-capturing group for delimiters
        \s+                     # whitespace runs
      | (?<=[a-zA-Z])(?=[({])   # letter followed by opening bracket
      | (?<=[})])(?=[a-zA-Z])   # closing bracket followed by letter
      | [,;:!?\[\]{}()\"""'`]   # punctuation chars (consumed as delimiter)
    )
    """,
    re.VERBOSE,
)

# Matches tokens that are purely numeric (int / float / currency / percentage).
_NUMERIC_RE = re.compile(
    r"^[+\-]?\$?\d[\d,]*\.?\d*%?$"
)

_HARD_LIMIT_MS = 15.0


async def tokenize(query: str) -> StageResult:
    """Tokenize *query* into a list of string tokens.

    Returns a :class:`StageResult` with ``stage_name="tokenizer"`` whose
    ``data`` dict contains:

    * ``tokens`` -- list[str]
    * ``token_count`` -- int
    * ``numerical_token_count`` -- int
    * ``numerical_token_ratio`` -- float  (0.0 when no tokens)
    """
    start = time.perf_counter()
    try:
        # ---- core tokenization ----
        raw_tokens = _SPLIT_RE.split(query)
        tokens: list[str] = [t for t in raw_tokens if t and not t.isspace()]

        token_count = len(tokens)
        numerical_token_count = sum(1 for t in tokens if _NUMERIC_RE.match(t))
        numerical_token_ratio = (
            numerical_token_count / token_count if token_count > 0 else 0.0
        )

        elapsed_ms = (time.perf_counter() - start) * 1_000

        return StageResult(
            stage_name="tokenizer",
            data={
                "tokens": tokens,
                "token_count": token_count,
                "numerical_token_count": numerical_token_count,
                "numerical_token_ratio": round(numerical_token_ratio, 6),
            },
            elapsed_ms=round(elapsed_ms, 3),
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1_000
        return StageResult(
            stage_name="tokenizer",
            data={
                "tokens": [],
                "token_count": 0,
                "numerical_token_count": 0,
                "numerical_token_ratio": 0.0,
            },
            elapsed_ms=round(elapsed_ms, 3),
            error=f"tokenizer failed: {exc}",
        )
