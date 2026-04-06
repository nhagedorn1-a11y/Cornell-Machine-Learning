"""Stage 4: Exposure Scorer -- scores frontier exposure requirement on a 0-100 axis.

Weighted sum of 5 sub-components covering query complexity, reasoning depth,
novel analytical framework, multi-step dependency, and local fallback quality.

Budget target: 30 ms (CPU heuristic fallback; NPU path in production).
"""

from __future__ import annotations

import re
import time
from typing import Any

from arbiter_triage.models import StageResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STAGE_NAME = "exposure_scorer"

# Component weights (must sum to 1.0)
_WEIGHTS: dict[str, float] = {
    "query_complexity": 0.30,
    "reasoning_depth": 0.25,
    "novel_analytical_framework": 0.20,
    "multi_step_dependency": 0.15,
    "local_fallback_quality": 0.10,
}

# Analytical / reasoning keywords for the reasoning depth component
_ANALYTICAL_KEYWORDS: list[str] = [
    "analyze", "analyse", "compare", "evaluate", "assess",
    "implications", "forecast", "model", "simulate", "project",
    "derive", "synthesize", "synthesise", "extrapolate", "infer",
    "correlate", "benchmark", "quantify", "optimise", "optimize",
]

# Conditional / logical structure markers for query complexity
_CONDITIONAL_WORDS: set[str] = {
    "if", "unless", "provided that", "assuming", "given that",
    "in the event", "whether", "otherwise", "alternatively",
    "however", "whereas", "while", "although", "except",
}

# Conjunction / clause-splitting tokens
_CLAUSE_SPLITTERS: re.Pattern = re.compile(
    r",\s|\band\b|\bor\b|\bbut\b|\bthen\b|\bwhile\b|\bwhereas\b",
    re.IGNORECASE,
)

# Dependency markers for multi-step scoring
_DEPENDENCY_MARKERS: list[str] = [
    "then", "after", "based on", "using the result",
    "given that", "assuming", "if...then", "once",
    "subsequently", "next", "followed by", "building on",
    "leveraging", "taking into account", "with the output",
    "dependent on", "contingent on", "prior to",
]

# Common English words for the novel-framework detector
# (a deliberately compact set; uncommon-word ratio is what matters)
_COMMON_WORDS: set[str] = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first",
    "well", "way", "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us", "is", "are", "was", "were", "been",
    "has", "had", "did", "does", "should", "may", "might", "must",
    "shall", "need", "very", "more", "much", "many", "such", "each",
    "every", "both", "few", "same", "different", "own", "still",
    "find", "here", "thing", "lot", "between", "through", "before",
    "where", "right", "too", "did", "long", "those", "under", "while",
    "last", "great", "high", "big", "small", "large", "old", "next",
    "early", "young", "important", "public", "same", "able", "data",
    "information", "report", "total", "value", "number", "part",
    "company", "system", "program", "question", "during", "against",
    "show", "per", "set", "change", "point", "help", "being", "sure",
    "without", "again", "off", "went", "got", "made", "since", "down",
}


# ---------------------------------------------------------------------------
# Sub-scoring helpers
# ---------------------------------------------------------------------------

def _score_query_complexity(query: str) -> float:
    """Heuristic complexity based on length, clause count, and conditionals."""
    length = len(query)
    # Clause count via splitting on conjunctions / commas
    clauses = _CLAUSE_SPLITTERS.split(query)
    clause_count = len(clauses)

    # Conditional logic presence
    query_lower = query.lower()
    conditional_hits = sum(
        1 for w in _CONDITIONAL_WORDS if w in query_lower
    )

    # Length component: 0-30
    if length < 40:
        length_score = 5.0
    elif length < 120:
        length_score = 15.0
    elif length < 300:
        length_score = 25.0
    else:
        length_score = 30.0

    # Clause component: 0-40
    if clause_count <= 1:
        clause_score = 5.0
    elif clause_count <= 3:
        clause_score = 20.0
    elif clause_count <= 6:
        clause_score = 30.0
    else:
        clause_score = 40.0

    # Conditional component: 0-30
    conditional_score = min(conditional_hits * 10.0, 30.0)

    return min(length_score + clause_score + conditional_score, 100.0)


def _score_reasoning_depth(query_lower: str) -> float:
    """Score based on presence of analytical / reasoning keywords."""
    hits = sum(1 for kw in _ANALYTICAL_KEYWORDS if kw in query_lower)
    if hits == 0:
        return 0.0
    if hits == 1:
        return 25.0
    if hits == 2:
        return 45.0
    if hits <= 4:
        return 65.0
    return min(65.0 + (hits - 4) * 7.0, 100.0)


def _score_novel_analytical_framework(tokens: list[str]) -> float:
    """Score based on uncommon / specialised terminology density."""
    if not tokens:
        return 0.0
    lower_tokens = [t.lower().strip(".,;:!?()[]{}\"'") for t in tokens]
    lower_tokens = [t for t in lower_tokens if t]  # drop empties
    if not lower_tokens:
        return 0.0

    uncommon_count = sum(
        1 for t in lower_tokens if t not in _COMMON_WORDS and len(t) > 2
    )
    ratio = uncommon_count / len(lower_tokens)
    # Scale: 0.0 -> 0, 0.5 -> 50, 1.0 -> 100
    return min(ratio * 100.0, 100.0)


def _score_multi_step_dependency(query_lower: str) -> float:
    """Count dependency markers; more markers = higher score."""
    hits = sum(1 for marker in _DEPENDENCY_MARKERS if marker in query_lower)
    if hits == 0:
        return 0.0
    if hits == 1:
        return 25.0
    if hits == 2:
        return 45.0
    if hits <= 4:
        return 65.0
    return min(65.0 + (hits - 4) * 7.0, 100.0)


def _score_local_fallback_quality() -> float:
    """Default moderate score -- production would use historical data."""
    return 50.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def score_exposure(
    query: str,
    tokens: list[str],
    token_count: int,
    air_gap_mode: bool = False,
) -> StageResult:
    """Compute the frontier exposure score (0-100) for a triage query.

    Parameters
    ----------
    query:
        Raw query text.
    tokens:
        Pre-tokenised query tokens from Stage 1.
    token_count:
        Total token count (may differ from ``len(tokens)`` if sub-word).
    air_gap_mode:
        When *True*, the system must never call a frontier model.  All
        component scores and the final score are set to ``0.0``.

    Returns
    -------
    StageResult
        ``data`` contains ``exposure_score`` and ``exposure_components``.
    """
    t0 = time.perf_counter()

    if air_gap_mode:
        zero_components: dict[str, float] = {k: 0.0 for k in _WEIGHTS}
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return StageResult(
            stage_name=_STAGE_NAME,
            data={
                "exposure_score": 0.0,
                "exposure_components": zero_components,
            },
            elapsed_ms=round(elapsed_ms, 3),
        )

    query_lower = query.lower()

    sub_scores: dict[str, float] = {
        "query_complexity": _score_query_complexity(query),
        "reasoning_depth": _score_reasoning_depth(query_lower),
        "novel_analytical_framework": _score_novel_analytical_framework(tokens),
        "multi_step_dependency": _score_multi_step_dependency(query_lower),
        "local_fallback_quality": _score_local_fallback_quality(),
    }

    # Weighted sum
    raw_score = sum(
        sub_scores[component] * weight
        for component, weight in _WEIGHTS.items()
    )
    exposure_score = round(min(max(raw_score, 0.0), 100.0), 2)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return StageResult(
        stage_name=_STAGE_NAME,
        data={
            "exposure_score": exposure_score,
            "exposure_components": {
                k: round(v, 2) for k, v in sub_scores.items()
            },
        },
        elapsed_ms=round(elapsed_ms, 3),
    )
