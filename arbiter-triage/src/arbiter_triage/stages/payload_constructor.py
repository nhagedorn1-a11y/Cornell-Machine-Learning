"""Stage 8 -- Payload Constructor: build sanitized frontier payload for AMBER/RED queries.

Budget targets:
    target  50 ms
    hard   100 ms
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Awaitable

from arbiter_triage.models import FrontierPayload, StageResult

# ---------------------------------------------------------------------------
# Redaction patterns (pre-compiled)
# ---------------------------------------------------------------------------

# PII patterns
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)
_PHONE_RE = re.compile(
    r"(?<!\d)"                       # not preceded by digit
    r"(?:\+?1[\s\-.]?)?"            # optional country code
    r"(?:\(?\d{3}\)?[\s\-.]?)"      # area code
    r"\d{3}[\s\-.]?"                # exchange
    r"\d{4}"                         # subscriber
    r"(?!\d)"                        # not followed by digit
)
_SSN_RE = re.compile(
    r"\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b"
)

# Financial figures: dollar amounts, numbers with currency context
_DOLLAR_RE = re.compile(
    r"\$\s?\d[\d,]*\.?\d*\s?(?:[BMKbmk](?:illion|illion)?)?"
    r"|\b\d[\d,]*\.?\d*\s?(?:dollars|USD|usd|cents)\b",
    re.IGNORECASE,
)
_FIGURE_RE = re.compile(
    r"\b\d[\d,]*\.?\d*\s?(?:million|billion|thousand|percent|%|bps|basis\s+points)\b",
    re.IGNORECASE,
)

# Sensitive terms
_SENSITIVE_TERMS = [
    "covenant", "merger", "acquisition", "takeover", "buyout",
    "insider", "material non-public", "MNPI", "confidential",
    "proprietary", "trade secret", "classified", "embargo",
    "blackout", "restricted list", "wall crossing", "pre-announcement",
    "earnings", "guidance", "forecast", "projection",
]
_SENSITIVE_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in _SENSITIVE_TERMS) + r")\b",
    re.IGNORECASE,
)

_HARD_LIMIT_MS = 100.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _redact_pii(text: str, pii_types: list[str]) -> tuple[str, list[dict[str, str]]]:
    """Replace PII patterns, returning sanitized text and redaction log."""
    redactions: list[dict[str, str]] = []

    def _log_and_replace(match: re.Match, label: str) -> str:
        redactions.append({"original": match.group(), "replaced_with": label})
        return label

    # Always redact emails, phones, SSNs regardless of pii_types — they are
    # universally sensitive.  The pii_types list is used for generic fallback.
    text = _EMAIL_RE.sub(lambda m: _log_and_replace(m, "[REDACTED_EMAIL]"), text)
    text = _SSN_RE.sub(lambda m: _log_and_replace(m, "[REDACTED_SSN]"), text)
    text = _PHONE_RE.sub(lambda m: _log_and_replace(m, "[REDACTED_PHONE]"), text)

    # Generic PII markers from upstream stages (names, addresses, etc.)
    for pii_type in pii_types:
        normalized = pii_type.upper().strip()
        if normalized not in ("EMAIL", "PHONE", "SSN"):
            # These are already handled by regex; skip duplicates
            pass  # placeholder — entity redaction covers named PII below

    return text, redactions


def _redact_financial(text: str, redactions: list[dict[str, str]]) -> str:
    """Replace dollar amounts and numeric figures with [FIGURE]."""
    def _log(match: re.Match) -> str:
        redactions.append({"original": match.group(), "replaced_with": "[FIGURE]"})
        return "[FIGURE]"

    text = _DOLLAR_RE.sub(_log, text)
    text = _FIGURE_RE.sub(_log, text)
    return text


def _redact_entities(
    text: str,
    entities: dict[str, Any],
    redactions: list[dict[str, str]],
) -> str:
    """Replace named entities from the entity registry with [ENTITY]."""
    # entities dict may have keys like "persons", "organizations", "locations"
    # each mapping to a list of entity strings.
    all_entity_names: list[str] = []
    for _category, names in entities.items():
        if isinstance(names, (list, set, tuple)):
            all_entity_names.extend(str(n) for n in names)
        elif isinstance(names, str):
            all_entity_names.append(names)

    # Sort by length descending so longer names are replaced first
    all_entity_names.sort(key=len, reverse=True)

    for name in all_entity_names:
        if not name.strip():
            continue
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        if pattern.search(text):
            redactions.append({"original": name, "replaced_with": "[ENTITY]"})
            text = pattern.sub("[ENTITY]", text)

    return text


def _redact_sensitive_terms(
    text: str,
    redactions: list[dict[str, str]],
) -> str:
    """Replace sensitive terms with [REDACTED]."""
    def _log(match: re.Match) -> str:
        redactions.append({"original": match.group(), "replaced_with": "[REDACTED]"})
        return "[REDACTED]"

    text = _SENSITIVE_RE.sub(_log, text)
    return text


def _abstract_intent(sanitized_text: str) -> str:
    """Create a brief intent summary from the sanitized text."""
    # Strip redaction placeholders for a cleaner summary seed
    cleaned = re.sub(r"\[(?:REDACTED\w*|FIGURE|ENTITY)\]", "", sanitized_text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Take the first sentence or first 120 characters as the intent summary
    sentences = re.split(r"[.!?]", cleaned)
    first_sentence = sentences[0].strip() if sentences else cleaned
    if len(first_sentence) > 120:
        first_sentence = first_sentence[:117] + "..."
    return f"User intent: {first_sentence}" if first_sentence else "User intent: unspecified"


def _rescore_sensitivity(sanitized_text: str) -> float:
    """Simplified re-scoring: count remaining sensitive indicators.

    Returns a score 0-100 representing residual sensitivity.
    """
    score = 0.0

    # Check for any surviving sensitive terms
    remaining_terms = _SENSITIVE_RE.findall(sanitized_text)
    score += len(remaining_terms) * 10.0

    # Check for surviving PII-like patterns
    if _EMAIL_RE.search(sanitized_text):
        score += 15.0
    if _SSN_RE.search(sanitized_text):
        score += 20.0
    if _PHONE_RE.search(sanitized_text):
        score += 10.0

    # Check for surviving financial figures
    if _DOLLAR_RE.search(sanitized_text):
        score += 10.0
    if _FIGURE_RE.search(sanitized_text):
        score += 5.0

    return min(score, 100.0)


# ---------------------------------------------------------------------------
# Main stage entry point
# ---------------------------------------------------------------------------

async def construct_payload(
    query: str,
    entities: dict[str, Any],
    pii_types: list[str],
    lane: str,
    sensitivity_scorer_func: Callable[[str], Awaitable[float]] | None = None,
) -> StageResult:
    """Build a sanitized frontier payload for AMBER/RED queries.

    For GREEN queries, returns an empty StageResult with payload=None.

    Returns a :class:`StageResult` with ``stage_name="payload_constructor"``
    whose ``data`` dict contains:

    * ``payload``          -- dict (FrontierPayload as dict) or None
    * ``abort``            -- bool
    * ``escalate_to_red``  -- bool
    """
    start = time.perf_counter()
    try:
        # GREEN queries need no frontier payload
        if lane == "GREEN":
            elapsed_ms = (time.perf_counter() - start) * 1_000
            return StageResult(
                stage_name="payload_constructor",
                data={
                    "payload": None,
                    "abort": False,
                    "escalate_to_red": False,
                },
                elapsed_ms=round(elapsed_ms, 3),
            )

        # ---- Sanitization pipeline ----
        redactions: list[dict[str, str]] = []

        # Step 1: Redact PII
        sanitized, pii_redactions = _redact_pii(query, pii_types)
        redactions.extend(pii_redactions)

        # Step 2: Redact financial figures
        sanitized = _redact_financial(sanitized, redactions)

        # Step 3: Redact named entities from registry
        sanitized = _redact_entities(sanitized, entities, redactions)

        # Step 4: Redact sensitive terms
        sanitized = _redact_sensitive_terms(sanitized, redactions)

        # Step 5: Abstract — create intent summary
        intent_summary = _abstract_intent(sanitized)

        # Step 6: Validate — re-score the sanitized payload
        if sensitivity_scorer_func is not None:
            residual_score = await sensitivity_scorer_func(sanitized)
        else:
            residual_score = _rescore_sensitivity(sanitized)

        abort = False
        escalate_to_red = False
        if residual_score > 15:
            abort = True
            escalate_to_red = True

        # Step 7: Construct FrontierPayload
        payload = FrontierPayload(
            sanitized_content=sanitized,
            redacted_fields=redactions,
            original_intent=intent_summary,
            sensitivity_after_sanitization=round(residual_score, 2),
        )
        payload.compute_hash()

        # Serialize to dict for StageResult
        payload_dict = {
            "payload_id": payload.payload_id,
            "sanitized_content": payload.sanitized_content,
            "redacted_fields": payload.redacted_fields,
            "original_intent": payload.original_intent,
            "sensitivity_after_sanitization": payload.sensitivity_after_sanitization,
            "payload_hash": payload.payload_hash,
            "constructed_at": payload.constructed_at.isoformat(),
            "approved_by": payload.approved_by,
            "approved_at": payload.approved_at,
        }

        elapsed_ms = (time.perf_counter() - start) * 1_000

        return StageResult(
            stage_name="payload_constructor",
            data={
                "payload": payload_dict,
                "abort": abort,
                "escalate_to_red": escalate_to_red,
            },
            elapsed_ms=round(elapsed_ms, 3),
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1_000
        return StageResult(
            stage_name="payload_constructor",
            data={
                "payload": None,
                "abort": True,
                "escalate_to_red": True,
            },
            elapsed_ms=round(elapsed_ms, 3),
            error=f"payload_constructor failed: {exc}",
        )
