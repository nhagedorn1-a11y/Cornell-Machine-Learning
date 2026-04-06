"""Stage 3: Sensitivity Scorer -- scores query sensitivity on a 0-100 axis.

Weighted sum of 7 sub-components covering PII presence, financial entity
density, named counterparty detection, contractual term detection, regulatory
data markers, numerical density, and customer sensitivity profile.

Budget target: 60 ms (CPU heuristic path).
"""

from __future__ import annotations

import re
import time
from typing import Any

from arbiter_triage.models import StageResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STAGE_NAME = "sensitivity_scorer"

# Component weights (must sum to 1.0)
_WEIGHTS: dict[str, float] = {
    "pii_presence": 0.25,
    "financial_entity_density": 0.20,
    "named_counterparty_detection": 0.15,
    "contractual_term_detection": 0.15,
    "regulatory_data_markers": 0.10,
    "numerical_density": 0.10,
    "customer_sensitivity_profile": 0.05,
}

# PII type severity mapping (type -> base score)
_PII_SEVERITY: dict[str, float] = {
    "email": 30.0,
    "phone": 50.0,
    "phone_number": 50.0,
    "address": 45.0,
    "dob": 60.0,
    "date_of_birth": 60.0,
    "ssn": 90.0,
    "social_security": 90.0,
    "passport": 85.0,
    "credit_card": 88.0,
    "bank_account": 80.0,
    "driver_license": 70.0,
    "tax_id": 75.0,
}

# Contractual term patterns
_CONTRACTUAL_TERMS: list[str] = [
    "indemnif", "liability", "warranty", "breach", "termination",
    "confidential", "non-disclosure", "nda", "force majeure",
    "arbitration", "governing law", "jurisdiction", "covenant",
    "obligation", "representation", "severability", "assignment",
    "amendment", "waiver", "material adverse", "liquidated damages",
    "intellectual property", "non-compete", "non-solicitation",
    "escrow", "milestone", "deliverable", "sla", "service level",
]

# Regulatory filing / marker patterns
_REGULATORY_MARKERS: list[str] = [
    "10-k", "10-q", "8-k", "s-1", "def 14a", "13-f", "form 4",
    "sec filing", "edgar", "gaap", "ifrs", "sox", "sarbanes",
    "dodd-frank", "basel", "mifid", "gdpr", "hipaa", "ferpa",
    "ccpa", "pci-dss", "aml", "kyc", "fatca", "cftc", "finra",
    "regulatory", "compliance", "audit", "disclosure",
]

# High-value regulatory filings that score higher
_HIGH_VALUE_FILINGS: set[str] = {
    "10-k", "10-q", "8-k", "s-1", "def 14a", "13-f",
    "sox", "sarbanes", "dodd-frank", "basel",
}


# ---------------------------------------------------------------------------
# Sub-scoring helpers
# ---------------------------------------------------------------------------

def _score_pii_presence(entities: dict[str, Any]) -> float:
    """Score based on count and severity of PII types detected."""
    pii_types: list[str] = entities.get("pii_types", [])
    if not pii_types:
        return 0.0

    # Compute max severity and an additive bonus for multiple types
    max_severity = 0.0
    for pii_type in pii_types:
        severity = _PII_SEVERITY.get(pii_type.lower(), 40.0)
        max_severity = max(max_severity, severity)

    # Multiple PII types compound the score
    count_bonus = min((len(pii_types) - 1) * 8.0, 20.0)  # up to +20
    return min(max_severity + count_bonus, 100.0)


def _score_financial_entity_density(
    entities: dict[str, Any], token_count: int,
) -> float:
    """Score based on ratio of financial entities to total tokens."""
    financial: list[str] = entities.get("financial", [])
    if not financial or token_count == 0:
        return 0.0
    ratio = len(financial) / token_count
    # Linear scale: ratio of 0.5 -> 100
    return min(ratio * 200.0, 100.0)


def _score_named_counterparty(entities: dict[str, Any]) -> float:
    """Score based on named entities found, with registry match boost."""
    named: list[str] = entities.get("named_entities", [])
    registry_matches: list[str] = entities.get("customer_registry_matches", [])

    if not named and not registry_matches:
        return 0.0

    if registry_matches:
        return 90.0

    count = len(named)
    if count == 0:
        return 0.0
    if count == 1:
        return 40.0
    return 70.0  # 2+


def _score_contractual_terms(query_lower: str) -> float:
    """Score based on count of contractual terms detected in the query."""
    count = sum(1 for term in _CONTRACTUAL_TERMS if term in query_lower)
    if count == 0:
        return 0.0
    if count == 1:
        return 25.0
    if count == 2:
        return 45.0
    if count <= 4:
        return 65.0
    return min(65.0 + (count - 4) * 7.0, 100.0)


def _score_regulatory_markers(entities: dict[str, Any], query_lower: str) -> float:
    """Score based on regulatory entity count and specific filing types."""
    regulatory: list[str] = entities.get("regulatory", [])

    # Also scan query text for marker patterns
    text_hits = [m for m in _REGULATORY_MARKERS if m in query_lower]
    all_markers = set(r.lower() for r in regulatory) | set(text_hits)

    if not all_markers:
        return 0.0

    # Check for high-value filings
    high_value_count = sum(
        1 for m in all_markers if m in _HIGH_VALUE_FILINGS
    )

    base = min(len(all_markers) * 15.0, 70.0)
    filing_bonus = min(high_value_count * 15.0, 30.0)
    return min(base + filing_bonus, 100.0)


def _score_numerical_density(numerical_ratio: float) -> float:
    """Score is numerical_ratio * 100, capped at 100."""
    return min(max(numerical_ratio * 100.0, 0.0), 100.0)


def _score_customer_sensitivity_profile(profile: float) -> float:
    """Direct pass-through, clamped to [0, 100]."""
    return min(max(profile, 0.0), 100.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def score_sensitivity(
    query: str,
    tokens: list[str],
    entities: dict,
    numerical_ratio: float,
    vertical_pack: str,
    customer_sensitivity_profile: float = 50.0,
) -> StageResult:
    """Compute the sensitivity score (0-100) for a triage query.

    Parameters
    ----------
    query:
        Raw query text.
    tokens:
        Pre-tokenised query tokens from Stage 1.
    entities:
        Entity dictionary from Stage 2 entity extraction.  Expected keys
        include ``pii_types``, ``financial``, ``named_entities``,
        ``customer_registry_matches``, ``regulatory``.
    numerical_ratio:
        Fraction of tokens that are numeric (from Stage 1).
    vertical_pack:
        Active vertical pack identifier (FINANCE, LEGAL, etc.).
    customer_sensitivity_profile:
        Customer-specific sensitivity baseline, 0-100. Defaults to 50.

    Returns
    -------
    StageResult
        ``data`` contains ``sensitivity_score``, ``sensitivity_components``,
        and ``sub_scores``.
    """
    t0 = time.perf_counter()
    query_lower = query.lower()
    token_count = len(tokens)

    # Compute each sub-score (all 0-100)
    sub_scores: dict[str, float] = {
        "pii_presence": _score_pii_presence(entities),
        "financial_entity_density": _score_financial_entity_density(
            entities, token_count,
        ),
        "named_counterparty_detection": _score_named_counterparty(entities),
        "contractual_term_detection": _score_contractual_terms(query_lower),
        "regulatory_data_markers": _score_regulatory_markers(
            entities, query_lower,
        ),
        "numerical_density": _score_numerical_density(numerical_ratio),
        "customer_sensitivity_profile": _score_customer_sensitivity_profile(
            customer_sensitivity_profile,
        ),
    }

    # Weighted sum
    raw_score = sum(
        sub_scores[component] * weight
        for component, weight in _WEIGHTS.items()
    )
    sensitivity_score = round(min(max(raw_score, 0.0), 100.0), 2)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return StageResult(
        stage_name=_STAGE_NAME,
        data={
            "sensitivity_score": sensitivity_score,
            "sensitivity_components": {
                component: round(sub_scores[component] * weight, 2)
                for component, weight in _WEIGHTS.items()
            },
            "sub_scores": {k: round(v, 2) for k, v in sub_scores.items()},
        },
        elapsed_ms=round(elapsed_ms, 3),
    )
