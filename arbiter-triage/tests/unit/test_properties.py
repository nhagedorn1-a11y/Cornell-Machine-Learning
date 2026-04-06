"""Property-based tests using Hypothesis."""
import pytest
import random
from hypothesis import given, strategies as st, settings


@pytest.mark.asyncio
@given(query=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))))
@settings(max_examples=30, deadline=None)
async def test_sensitivity_score_bounded(query):
    from arbiter_triage.stages.tokenizer import tokenize
    from arbiter_triage.stages.entity_extractor import extract_entities
    from arbiter_triage.stages.sensitivity_scorer import score_sensitivity

    tok = await tokenize(query)
    tokens = tok.data.get("tokens", [])
    ratio = tok.data.get("numerical_token_ratio", 0)
    ents = await extract_entities(tokens, query, "GENERIC")
    result = await score_sensitivity(query, tokens, ents.data, ratio, "GENERIC")
    score = result.data.get("sensitivity_score", 0)
    assert 0 <= score <= 100


@pytest.mark.asyncio
@given(query=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))))
@settings(max_examples=30, deadline=None)
async def test_exposure_score_bounded(query):
    from arbiter_triage.stages.tokenizer import tokenize
    from arbiter_triage.stages.exposure_scorer import score_exposure

    tok = await tokenize(query)
    tokens = tok.data.get("tokens", [])
    count = tok.data.get("token_count", 0)
    result = await score_exposure(query, tokens, count)
    score = result.data.get("exposure_score", 0)
    assert 0 <= score <= 100


@pytest.mark.asyncio
@given(query=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))))
@settings(max_examples=30, deadline=None)
async def test_exposure_airgap_zero(query):
    from arbiter_triage.stages.tokenizer import tokenize
    from arbiter_triage.stages.exposure_scorer import score_exposure

    tok = await tokenize(query)
    tokens = tok.data.get("tokens", [])
    count = tok.data.get("token_count", 0)
    result = await score_exposure(query, tokens, count, air_gap_mode=True)
    score = result.data.get("exposure_score", 0)
    assert score == 0.0


@pytest.mark.asyncio
async def test_hard_red_always_red():
    """Hard RED rules always produce RED regardless of anything else."""
    from arbiter_triage.stages.rule_engine import evaluate_rules

    red_queries = [
        "What is our debt covenant?",
        "Review the acquisition details",
        "Check the 10-K filing",
        "This is material non-public information",
        "Access the board minutes",
        "Review the credit facility",
        "Start due diligence",
    ]
    for query in red_queries:
        tokens = query.lower().split()
        result = await evaluate_rules(query, tokens, {}, 0, [], [], len(tokens))
        assert result.data["hard_rule_fired"] is True, f"RED rule should fire for: {query}"
        assert result.data["lane_override"] == "RED", f"Lane should be RED for: {query}"


@pytest.mark.asyncio
async def test_matrix_always_valid_lane():
    """Matrix evaluation always returns GREEN, AMBER, or RED."""
    from arbiter_triage.stages.matrix_evaluator import evaluate_matrix

    for _ in range(100):
        s = random.uniform(0, 100)
        e = random.uniform(0, 100)
        result = await evaluate_matrix(s, e)
        assert result.data["lane"] in ("GREEN", "AMBER", "RED")


@pytest.mark.asyncio
async def test_context_accumulation_bounded():
    """Cumulative sensitivity stays bounded in [0, 100]."""
    from arbiter_triage.stages.session_context import SessionContextManager

    mgr = SessionContextManager()
    await mgr.get_or_create_session("test", "user")
    for _ in range(100):
        score = random.uniform(0, 100)
        session = await mgr.update_session("test", score, [], [], "GREEN")
        assert 0 <= session.cumulative_sensitivity <= 100


@pytest.mark.asyncio
async def test_decision_record_always_has_id():
    """Decision records always have non-empty record_id."""
    from arbiter_triage.models import TriageDecisionRecord
    record = TriageDecisionRecord()
    assert record.record_id
    assert len(record.record_id) > 0


@pytest.mark.asyncio
async def test_sanitized_payload_bounded():
    """Sanitized payload sensitivity must be <= 15 or abort."""
    from arbiter_triage.stages.payload_constructor import construct_payload

    result = await construct_payload(
        "Send $5M to john@acme.com regarding the covenant breach",
        {"entities_detected": [{"type": "PII_EMAIL", "value": "john@acme.com"}]},
        ["PII_EMAIL"],
        "RED",
    )
    payload = result.data.get("payload")
    if payload and not result.data.get("abort"):
        assert payload.get("sensitivity_after_sanitization", 0) <= 15
