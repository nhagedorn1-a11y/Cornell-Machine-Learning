"""Integration tests for the complete triage pipeline."""

import pytest
import uuid

from arbiter_triage.models import (
    DataContext,
    ErrorResponse,
    TriageRequest,
    TriageResponse,
)
from arbiter_triage.pipeline import TriagePipeline


@pytest.fixture
async def pipeline():
    p = TriagePipeline()
    await p.initialize()
    yield p
    await p.shutdown()


def make_request(query: str, **kwargs) -> TriageRequest:
    return TriageRequest(
        request_id=str(uuid.uuid4()),
        session_id=kwargs.get("session_id", str(uuid.uuid4())),
        user_id=kwargs.get("user_id", "test-user"),
        query=query,
        data_context=DataContext(),
        vertical_pack=kwargs.get("vertical_pack", "GENERIC"),
        air_gap_mode=kwargs.get("air_gap_mode", False),
    )


# ── GREEN classification ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_green_classification_simple_query(pipeline):
    """A simple definitional query with no sensitive content should be GREEN."""
    req = make_request("What is a balance sheet?")
    resp = await pipeline.process(req)

    assert isinstance(resp, TriageResponse)
    assert resp.lane == "GREEN", (
        f"Expected GREEN for a simple definitional query, got {resp.lane}"
    )


# ── RED classification — hard rules ───────────────────────────────────


@pytest.mark.asyncio
async def test_red_classification_covenant_headroom(pipeline):
    """'covenant headroom' triggers an ALWAYS_RED pattern."""
    req = make_request("What is our covenant headroom?")
    resp = await pipeline.process(req)

    assert isinstance(resp, TriageResponse)
    assert resp.lane == "RED", (
        f"Expected RED for covenant headroom query, got {resp.lane}"
    )
    assert resp.hard_rule_fired is True


@pytest.mark.asyncio
async def test_red_classification_10k_filing(pipeline):
    """'10-K filing' triggers an ALWAYS_RED pattern."""
    req = make_request("Review the 10-K filing")
    resp = await pipeline.process(req)

    assert isinstance(resp, TriageResponse)
    assert resp.lane == "RED", (
        f"Expected RED for 10-K filing query, got {resp.lane}"
    )
    assert resp.hard_rule_fired is True


# ── Air-gap mode ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_air_gap_mode_forces_zero_exposure(pipeline):
    """When air_gap_mode is True the exposure score must be 0."""
    req = make_request(
        "Analyze the complex multi-step dependency between revenue forecasts",
        air_gap_mode=True,
    )
    resp = await pipeline.process(req)

    assert isinstance(resp, TriageResponse)
    assert resp.exposure_score == 0.0, (
        f"Exposure score must be 0 in air-gap mode, got {resp.exposure_score}"
    )


# ── Session context elevation ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_context_elevation(pipeline):
    """After many high-sensitivity queries a benign query should be elevated."""
    session_id = str(uuid.uuid4())

    # Send 10 queries that trigger ALWAYS_RED (high sensitivity)
    for _ in range(10):
        red_req = make_request(
            "What is our covenant headroom under the credit facility?",
            session_id=session_id,
        )
        red_resp = await pipeline.process(red_req)
        assert isinstance(red_resp, TriageResponse)
        assert red_resp.lane == "RED"

    # Now send a benign query on the same session
    benign_req = make_request(
        "What is a balance sheet?",
        session_id=session_id,
    )
    benign_resp = await pipeline.process(benign_req)

    assert isinstance(benign_resp, TriageResponse)
    # Context should elevate the lane above GREEN
    assert benign_resp.lane in ("AMBER", "RED"), (
        f"Expected context elevation to AMBER or RED, got {benign_resp.lane}"
    )
    assert benign_resp.context_elevated is True


# ── Response structure invariants ─────────────────────────────────────


@pytest.mark.asyncio
async def test_every_response_has_record_id(pipeline):
    """Every TriageResponse must carry a non-empty record_id."""
    req = make_request("What is a balance sheet?")
    resp = await pipeline.process(req)

    assert isinstance(resp, TriageResponse)
    assert resp.record_id, "record_id must be non-empty"
    # Verify it looks like a UUID
    uuid.UUID(resp.record_id)  # raises ValueError if not valid UUID


@pytest.mark.asyncio
async def test_stage_times_ms_populated(pipeline):
    """stage_times_ms should contain timing data for executed stages."""
    req = make_request("What is a balance sheet?")
    resp = await pipeline.process(req)

    assert isinstance(resp, TriageResponse)
    assert isinstance(resp.stage_times_ms, dict)
    assert len(resp.stage_times_ms) > 0, "stage_times_ms should not be empty"

    expected_stages = {
        "tokenization",
        "entity_extraction",
        "sensitivity_scoring",
        "exposure_scoring",
    }
    for stage_name in expected_stages:
        assert stage_name in resp.stage_times_ms, (
            f"Missing stage timing for {stage_name}"
        )
        assert isinstance(resp.stage_times_ms[stage_name], (int, float))


# ── Error handling ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_error_responses_are_red(pipeline):
    """ErrorResponse must always assign the RED lane."""
    # Force an error by patching the tokenizer to fail
    from unittest.mock import AsyncMock, patch

    failing_tokenizer = AsyncMock(
        return_value=__import__(
            "arbiter_triage.models", fromlist=["StageResult"]
        ).StageResult(
            stage_name="tokenizer",
            error="Forced failure for testing",
        ),
    )

    with patch("arbiter_triage.pipeline.tokenize", failing_tokenizer):
        req = make_request("This should cause an error")
        resp = await pipeline.process(req)

    assert isinstance(resp, ErrorResponse)
    assert resp.lane == "RED"
    assert resp.error is True
    assert resp.record_id  # must still have a record_id


@pytest.mark.asyncio
async def test_empty_query_returns_valid_response(pipeline):
    """An empty query should still produce a valid response with a lane assignment."""
    req = make_request("")
    resp = await pipeline.process(req)

    # Must always return a response with a lane
    if isinstance(resp, ErrorResponse):
        assert resp.lane == "RED"
        assert resp.error is True
    elif isinstance(resp, TriageResponse):
        assert resp.lane in ("GREEN", "AMBER", "RED")
        assert resp.record_id  # Always has a record
