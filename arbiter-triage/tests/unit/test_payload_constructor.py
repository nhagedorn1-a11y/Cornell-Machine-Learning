"""Unit tests for payload construction and sanitization."""
import pytest
from arbiter_triage.stages.payload_constructor import construct_payload

@pytest.mark.asyncio
async def test_green_no_payload():
    result = await construct_payload("simple query", {}, [], "GREEN")
    assert result.data.get("payload") is None

@pytest.mark.asyncio
async def test_amber_constructs_payload():
    result = await construct_payload("Check user@email.com balance", {"entities_detected": [{"type": "PII_EMAIL", "value": "user@email.com"}]}, ["PII_EMAIL"], "AMBER")
    assert result.data.get("payload") is not None

@pytest.mark.asyncio
async def test_pii_redaction():
    result = await construct_payload("Send report to john@acme.com about $5M deal", {"entities_detected": []}, ["PII_EMAIL"], "AMBER")
    payload = result.data.get("payload", {})
    if payload:
        content = payload.get("sanitized_content", "")
        assert "john@acme.com" not in content

@pytest.mark.asyncio
async def test_financial_figure_redaction():
    result = await construct_payload("Revenue was $5,000,000 last quarter", {"entities_detected": []}, [], "AMBER")
    payload = result.data.get("payload", {})
    if payload:
        content = payload.get("sanitized_content", "")
        assert "$5,000,000" not in content

@pytest.mark.asyncio
async def test_red_constructs_payload():
    result = await construct_payload("Review the covenant terms for the $500M facility", {"entities_detected": []}, [], "RED")
    assert result.data.get("payload") is not None

@pytest.mark.asyncio
async def test_payload_has_hash():
    result = await construct_payload("Check balance details", {"entities_detected": []}, [], "AMBER")
    payload = result.data.get("payload", {})
    if payload:
        assert payload.get("payload_hash") is not None
        assert len(payload.get("payload_hash", "")) == 64  # SHA-256 hex
