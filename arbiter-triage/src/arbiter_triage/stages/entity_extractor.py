"""Stage 2 -- Entity Extractor: detect entities, PII, and domain-specific terms.

Budget targets:
    target  40 ms
    hard    80 ms

Supports spaCy NER when available; degrades gracefully to regex-only extraction.
Presidio integration is optional and wrapped defensively.
"""

from __future__ import annotations

import re
import time
from typing import Any

from arbiter_triage.models import StageResult

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# PII patterns
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
_PHONE_RE = re.compile(
    r"(?<!\d)"
    r"(?:\+?1[\s.\-]?)?"
    r"(?:\(?\d{3}\)?[\s.\-]?)"
    r"\d{3}[\s.\-]?\d{4}"
    r"(?!\d)"
)
_SSN_RE = re.compile(
    r"\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b"
)

# Financial patterns
_DOLLAR_RE = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d{1,2})?"
    r"(?:\s?(?:million|billion|trillion|mn|bn|tn|MM|M|B|T|k|K))?"
    , re.IGNORECASE,
)
_PERCENTAGE_RE = re.compile(
    r"\b\d+(?:\.\d+)?%"
)
_RATIO_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:x|X|:\s?\d+(?:\.\d+)?)\b"
)

# Regulatory markers -- SEC filing types and common regulatory references
_SEC_FILING_RE = re.compile(
    r"\b(?:10-K|10-Q|8-K|S-1|S-3|S-4|S-11|Form\s?4|Form\s?3"
    r"|Form\s?D|DEF\s?14A|13[FDG]|SC\s?13[DG]|144|20-F|6-K"
    r"|N-1A|N-CSR|NPORT|proxy\s?statement)\b",
    re.IGNORECASE,
)

# Contract references
_SECTION_REF_RE = re.compile(
    r"\b(?:Section|Clause|Article)\s+\d+(?:\.\d+)*\b", re.IGNORECASE
)
_AGREEMENT_ID_RE = re.compile(
    r"\b(?:Agreement|Contract)\s*(?:#|No\.?|ID:?)\s*[A-Z0-9\-]+\b",
    re.IGNORECASE,
)

# Covenant / credit terms (case-insensitive phrases)
_COVENANT_TERMS = re.compile(
    r"\b(?:"
    r"leverage\s+ratio|interest\s+coverage(?:\s+ratio)?"
    r"|debt\s+covenant|financial\s+covenant"
    r"|debt[\-\s]to[\-\s](?:equity|ebitda|capital)"
    r"|fixed[\-\s]charge\s+coverage"
    r"|current\s+ratio|net\s+worth\s+requirement"
    r"|minimum\s+liquidity|maximum\s+leverage"
    r"|coverage\s+ratio"
    r")\b",
    re.IGNORECASE,
)

# Credit instruments
_CREDIT_INSTRUMENT_RE = re.compile(
    r"\b(?:"
    r"revolving\s+credit|term\s+loan|credit\s+facility"
    r"|senior\s+(?:secured|unsecured)\s+(?:notes?|bonds?|debt)"
    r"|subordinated\s+(?:notes?|debt)"
    r"|convertible\s+(?:notes?|bonds?)"
    r"|credit\s+default\s+swap|CDS"
    r"|collateralized\s+(?:loan|debt)\s+obligation|CLO|CDO"
    r"|syndicated\s+loan|bridge\s+loan"
    r"|letter\s+of\s+credit"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Optional spaCy loader
# ---------------------------------------------------------------------------

_spacy_nlp: Any = None
_spacy_attempted: bool = False


def _load_spacy() -> Any | None:
    """Try to load a spaCy model; return None on failure."""
    global _spacy_nlp, _spacy_attempted  # noqa: PLW0603
    if _spacy_attempted:
        return _spacy_nlp
    _spacy_attempted = True
    try:
        import spacy  # type: ignore[import-untyped]

        for model_name in ("en_core_web_sm", "en_core_web_md", "en_core_web_lg"):
            try:
                _spacy_nlp = spacy.load(model_name, disable=["parser", "lemmatizer"])
                return _spacy_nlp
            except OSError:
                continue
    except ImportError:
        pass
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _regex_extract_pii(query: str) -> list[dict[str, str]]:
    """Return PII entity dicts found via regex."""
    results: list[dict[str, str]] = []
    for m in _EMAIL_RE.finditer(query):
        results.append({"type": "PII_EMAIL", "value": m.group()})
    for m in _PHONE_RE.finditer(query):
        results.append({"type": "PII_PHONE", "value": m.group().strip()})
    for m in _SSN_RE.finditer(query):
        results.append({"type": "PII_SSN", "value": m.group()})
    return results


def _regex_extract_financial(query: str) -> list[dict[str, str]]:
    """Return financial figure entities found via regex."""
    results: list[dict[str, str]] = []
    for m in _DOLLAR_RE.finditer(query):
        results.append({"type": "FINANCIAL_FIGURE", "value": m.group()})
    for m in _PERCENTAGE_RE.finditer(query):
        results.append({"type": "FINANCIAL_FIGURE", "value": m.group()})
    for m in _RATIO_RE.finditer(query):
        results.append({"type": "FINANCIAL_FIGURE", "value": m.group()})
    return results


def _regex_extract_regulatory(query: str) -> list[dict[str, str]]:
    """Return regulatory marker entities."""
    results: list[dict[str, str]] = []
    for m in _SEC_FILING_RE.finditer(query):
        results.append({"type": "REGULATORY_MARKER", "value": m.group()})
    return results


def _regex_extract_contract(query: str) -> list[dict[str, str]]:
    """Return contract / section references."""
    results: list[dict[str, str]] = []
    for m in _SECTION_REF_RE.finditer(query):
        results.append({"type": "CONTRACT_REFERENCE", "value": m.group()})
    for m in _AGREEMENT_ID_RE.finditer(query):
        results.append({"type": "CONTRACT_REFERENCE", "value": m.group()})
    return results


def _regex_extract_covenants(query: str) -> list[dict[str, str]]:
    """Return covenant term entities."""
    results: list[dict[str, str]] = []
    for m in _COVENANT_TERMS.finditer(query):
        results.append({"type": "COVENANT_TERM", "value": m.group()})
    return results


def _regex_extract_credit_instruments(query: str) -> list[dict[str, str]]:
    """Return credit instrument entities."""
    results: list[dict[str, str]] = []
    for m in _CREDIT_INSTRUMENT_RE.finditer(query):
        results.append({"type": "CREDIT_INSTRUMENT", "value": m.group()})
    return results


def _spacy_extract(
    nlp: Any, query: str,
) -> tuple[list[dict[str, str]], list[str]]:
    """Run spaCy NER and return (entities, named_entities)."""
    entities: list[dict[str, str]] = []
    named_entities: list[str] = []
    doc = nlp(query)
    for ent in doc.ents:
        label = ent.label_
        text = ent.text.strip()
        if not text:
            continue
        # Map spaCy labels to our taxonomy
        if label in ("PERSON", "ORG"):
            entities.append({"type": "COUNTERPARTY_NAME", "value": text})
            named_entities.append(text)
        elif label == "MONEY":
            entities.append({"type": "FINANCIAL_FIGURE", "value": text})
        elif label == "LAW":
            entities.append({"type": "REGULATORY_MARKER", "value": text})
        elif label in ("GPE", "LOC", "NORP", "FAC", "EVENT"):
            named_entities.append(text)
        elif label in ("CARDINAL", "QUANTITY", "PERCENT", "ORDINAL"):
            entities.append({"type": "FINANCIAL_FIGURE", "value": text})
    return entities, named_entities


def _match_customer_entities(
    tokens: list[str],
    query: str,
    registry: set[str],
) -> list[dict[str, str]]:
    """Match tokens against a customer-supplied entity registry."""
    results: list[dict[str, str]] = []
    query_lower = query.lower()
    for entity in registry:
        if entity.lower() in query_lower:
            results.append({"type": "COUNTERPARTY_NAME", "value": entity})
    return results


def _extract_data_source_refs(query: str) -> list[str]:
    """Heuristically detect data source references in the query."""
    refs: list[str] = []
    # Common patterns: table names, file paths, URLs, database references
    table_re = re.compile(
        r"\b(?:table|view|schema|database|db)\s*[:\s]\s*[\w.]+", re.IGNORECASE
    )
    for m in table_re.finditer(query):
        refs.append(m.group().strip())
    url_re = re.compile(r"https?://\S+")
    for m in url_re.finditer(query):
        refs.append(m.group())
    return refs


def _deduplicate_entities(
    entities: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Remove duplicate (type, value) pairs while preserving order."""
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for ent in entities:
        key = (ent["type"], ent["value"])
        if key not in seen:
            seen.add(key)
            deduped.append(ent)
    return deduped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def extract_entities(
    tokens: list[str],
    query: str,
    vertical_pack: str,
    customer_entity_registry: set[str] | None = None,
) -> StageResult:
    """Extract entities from a query and its tokens.

    Returns a :class:`StageResult` with ``stage_name="entity_extractor"``
    whose ``data`` dict contains:

    * ``entities_detected`` -- list[dict] with keys ``type`` and ``value``
    * ``pii_types_detected`` -- list[str] of PII type labels found
    * ``named_entities`` -- list[str] of person/org/location names
    * ``data_source_references`` -- list[str]
    """
    start = time.perf_counter()
    try:
        all_entities: list[dict[str, str]] = []
        named_entities: list[str] = []

        # -- PII detection (always regex; Presidio is optional) --
        pii_entities = _regex_extract_pii(query)
        all_entities.extend(pii_entities)

        # Optional Presidio augmentation
        try:
            from presidio_analyzer import AnalyzerEngine  # type: ignore[import-untyped]

            analyzer = AnalyzerEngine()
            presidio_results = analyzer.analyze(
                text=query, language="en",
                entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"],
            )
            for r in presidio_results:
                value = query[r.start : r.end]
                etype = {
                    "EMAIL_ADDRESS": "PII_EMAIL",
                    "PHONE_NUMBER": "PII_PHONE",
                    "US_SSN": "PII_SSN",
                }.get(r.entity_type, f"PII_{r.entity_type}")
                all_entities.append({"type": etype, "value": value})
        except Exception:  # noqa: BLE001
            pass  # Presidio not available; regex results suffice

        # -- Financial figures --
        all_entities.extend(_regex_extract_financial(query))

        # -- Regulatory markers --
        all_entities.extend(_regex_extract_regulatory(query))

        # -- Contract references --
        all_entities.extend(_regex_extract_contract(query))

        # -- Covenant terms --
        all_entities.extend(_regex_extract_covenants(query))

        # -- Credit instruments --
        all_entities.extend(_regex_extract_credit_instruments(query))

        # -- spaCy NER (optional) --
        nlp = _load_spacy()
        if nlp is not None:
            try:
                spacy_ents, spacy_names = _spacy_extract(nlp, query)
                all_entities.extend(spacy_ents)
                named_entities.extend(spacy_names)
            except Exception:  # noqa: BLE001
                pass  # degrade gracefully

        # -- Customer entity registry --
        if customer_entity_registry:
            all_entities.extend(
                _match_customer_entities(tokens, query, customer_entity_registry)
            )

        # -- Data source references --
        data_source_refs = _extract_data_source_refs(query)

        # -- Deduplicate --
        all_entities = _deduplicate_entities(all_entities)

        # Derive PII types detected
        pii_types_detected: list[str] = sorted(
            {e["type"] for e in all_entities if e["type"].startswith("PII_")}
        )

        # Derive unique named entities
        named_entities = sorted(set(named_entities))

        elapsed_ms = (time.perf_counter() - start) * 1_000

        return StageResult(
            stage_name="entity_extractor",
            data={
                "entities_detected": all_entities,
                "pii_types_detected": pii_types_detected,
                "named_entities": named_entities,
                "data_source_references": data_source_refs,
            },
            elapsed_ms=round(elapsed_ms, 3),
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1_000
        return StageResult(
            stage_name="entity_extractor",
            data={
                "entities_detected": [],
                "pii_types_detected": [],
                "named_entities": [],
                "data_source_references": [],
            },
            elapsed_ms=round(elapsed_ms, 3),
            error=f"entity_extractor failed: {exc}",
        )
