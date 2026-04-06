"""Stage 5: Hard rule evaluation for the Arbiter Triage Engine.

Evaluates ALWAYS_RED, ALWAYS_GREEN, and pre-approved template rules
to determine if a hard lane override should be applied.
"""

from __future__ import annotations

import hashlib
import re

from arbiter_triage.models import StageResult

# ---------------------------------------------------------------------------
# ALWAYS_RED compiled patterns
# ---------------------------------------------------------------------------
_ALWAYS_RED_RAW = [
    r'\b(covenant|debt\s+covenant|financial\s+covenant|leverage\s+ratio|interest\s+coverage)\b',
    r'\b(credit\s+facility|revolving\s+credit|term\s+loan|debt\s+agreement)\b',
    r'\b(covenant\s+headroom|covenant\s+breach|covenant\s+waiver)\b',
    r'\b(acquisition|merger|target\s+company|deal\s+value|letter\s+of\s+intent|LOI)\b',
    r'\b(due\s+diligence|data\s+room|NDA|non-disclosure)\b',
    r'\b(10-K|10-Q|8-K|proxy\s+statement|S-1|Form\s+4)\b',
    r'\b(material\s+non-public|MNPI|insider\s+information)\b',
    r'\b(board\s+resolution|board\s+minutes|executive\s+compensation|CEO\s+package)\b',
]

ALWAYS_RED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in _ALWAYS_RED_RAW
]

ALWAYS_RED_ENTITY_TYPES: list[str] = [
    'CREDIT_AGREEMENT',
    'REGULATORY_FILING',
    'MNPI_MARKER',
    'COVENANT_THRESHOLD',
]

# ---------------------------------------------------------------------------
# ALWAYS_GREEN compiled pattern
# ---------------------------------------------------------------------------
ALWAYS_GREEN_PATTERN: re.Pattern[str] = re.compile(
    r'^(what\s+is|explain|define|how\s+do(es)?\s+|what\s+are\s+the)\s+',
    re.IGNORECASE,
)


def _normalize_query(query: str) -> str:
    """Lowercase and collapse whitespace for hashing."""
    return re.sub(r'\s+', ' ', query.strip().lower())


def _query_hash(query: str) -> str:
    """SHA-256 hash of the normalized query."""
    return hashlib.sha256(_normalize_query(query).encode('utf-8')).hexdigest()


async def evaluate_rules(
    query: str,
    tokens: list[str],
    entities: dict,
    numerical_token_count: int,
    named_entities: list,
    data_source_references: list,
    token_count: int,
    pre_approved_hashes: set[str] | None = None,
) -> StageResult:
    """Evaluate hard rules and return a StageResult with any lane override.

    Evaluation order:
    1. ALWAYS_RED patterns and entity types
    2. ALWAYS_GREEN pattern + guard conditions
    3. Pre-approved template hash match
    """
    rules_evaluated: list[str] = []
    rules_fired: list[str] = []

    # ------------------------------------------------------------------
    # 1. ALWAYS_RED — pattern matching
    # ------------------------------------------------------------------
    for idx, pattern in enumerate(ALWAYS_RED_PATTERNS):
        rule_id = f"ALWAYS_RED_PATTERN_{idx}"
        rules_evaluated.append(rule_id)
        if pattern.search(query):
            rules_fired.append(rule_id)
            return StageResult(
                stage_name="rule_engine",
                data={
                    "hard_rule_fired": True,
                    "rule_type": "ALWAYS_RED",
                    "rule_id": rule_id,
                    "lane_override": "RED",
                    "rules_evaluated": rules_evaluated,
                    "rules_fired": rules_fired,
                },
            )

    # ALWAYS_RED — entity type matching
    entity_types_present: set[str] = set()
    if isinstance(entities, dict):
        for key, value in entities.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and "type" in item:
                        entity_types_present.add(item["type"])
                    elif isinstance(item, str):
                        entity_types_present.add(item)
            elif isinstance(value, str):
                entity_types_present.add(value)

    for etype in ALWAYS_RED_ENTITY_TYPES:
        rule_id = f"ALWAYS_RED_ENTITY_{etype}"
        rules_evaluated.append(rule_id)
        if etype in entity_types_present:
            rules_fired.append(rule_id)
            return StageResult(
                stage_name="rule_engine",
                data={
                    "hard_rule_fired": True,
                    "rule_type": "ALWAYS_RED",
                    "rule_id": rule_id,
                    "lane_override": "RED",
                    "rules_evaluated": rules_evaluated,
                    "rules_fired": rules_fired,
                },
            )

    # ------------------------------------------------------------------
    # 2. ALWAYS_GREEN — pattern + guard conditions
    # ------------------------------------------------------------------
    rule_id = "ALWAYS_GREEN"
    rules_evaluated.append(rule_id)

    pattern_match = ALWAYS_GREEN_PATTERN.search(query)
    no_numerical_tokens = numerical_token_count == 0
    no_named_entities = len(named_entities) == 0
    no_data_source_references = len(data_source_references) == 0
    query_length_ok = token_count <= 50

    if (
        pattern_match
        and no_numerical_tokens
        and no_named_entities
        and no_data_source_references
        and query_length_ok
    ):
        rules_fired.append(rule_id)
        return StageResult(
            stage_name="rule_engine",
            data={
                "hard_rule_fired": True,
                "rule_type": "ALWAYS_GREEN",
                "rule_id": rule_id,
                "lane_override": "GREEN",
                "rules_evaluated": rules_evaluated,
                "rules_fired": rules_fired,
            },
        )

    # ------------------------------------------------------------------
    # 3. Pre-approved template hash match
    # ------------------------------------------------------------------
    rule_id = "PRE_APPROVED_HASH"
    rules_evaluated.append(rule_id)

    if pre_approved_hashes:
        qhash = _query_hash(query)
        if qhash in pre_approved_hashes:
            rules_fired.append(rule_id)
            return StageResult(
                stage_name="rule_engine",
                data={
                    "hard_rule_fired": True,
                    "rule_type": "PRE_APPROVED",
                    "rule_id": rule_id,
                    "lane_override": "GREEN",
                    "rules_evaluated": rules_evaluated,
                    "rules_fired": rules_fired,
                },
            )

    # ------------------------------------------------------------------
    # No rule fired
    # ------------------------------------------------------------------
    return StageResult(
        stage_name="rule_engine",
        data={
            "hard_rule_fired": False,
            "rule_type": None,
            "rule_id": None,
            "lane_override": None,
            "rules_evaluated": rules_evaluated,
            "rules_fired": rules_fired,
        },
    )
