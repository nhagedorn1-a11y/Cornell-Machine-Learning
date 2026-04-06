"""Unit tests for Stage 2 -- Entity Extractor."""

from __future__ import annotations

import pytest

from arbiter_triage.models import StageResult
from arbiter_triage.stages.entity_extractor import extract_entities


def _entity_types(result: StageResult) -> set[str]:
    """Helper: return the set of entity type strings from a result."""
    return {e["type"] for e in result.data["entities_detected"]}


class TestPIIDetection:
    """PII pattern matching (email, phone, SSN)."""

    @pytest.mark.asyncio
    async def test_email_detection(self):
        query = "Contact john.doe@example.com for details"
        result = await extract_entities(query.split(), query, "GENERIC")
        assert "PII_EMAIL" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_phone_detection(self):
        query = "Call me at 555-867-5309 tomorrow"
        result = await extract_entities(query.split(), query, "GENERIC")
        assert "PII_PHONE" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_ssn_detection(self):
        query = "SSN is 123-45-6789 on file"
        result = await extract_entities(query.split(), query, "GENERIC")
        assert "PII_SSN" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_pii_types_detected_list(self):
        query = "Email: a@b.com, SSN: 123-45-6789"
        result = await extract_entities(query.split(), query, "GENERIC")
        pii_types = result.data["pii_types_detected"]
        assert "PII_EMAIL" in pii_types
        assert "PII_SSN" in pii_types

    @pytest.mark.asyncio
    async def test_multiple_emails(self):
        query = "Send to alice@example.com and bob@example.org"
        result = await extract_entities(query.split(), query, "GENERIC")
        email_entities = [
            e for e in result.data["entities_detected"]
            if e["type"] == "PII_EMAIL"
        ]
        assert len(email_entities) >= 2


class TestFinancialEntityDetection:
    """Financial figure and ratio detection."""

    @pytest.mark.asyncio
    async def test_dollar_amount(self):
        query = "The deal is valued at $2,500,000"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "FINANCIAL_FIGURE" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_percentage(self):
        query = "Growth rate is 14.5% year over year"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "FINANCIAL_FIGURE" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_dollar_with_scale(self):
        query = "Revenue was $3.2 billion last quarter"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "FINANCIAL_FIGURE" in _entity_types(result)


class TestRegulatoryMarkers:
    """SEC filing and regulatory reference detection."""

    @pytest.mark.asyncio
    async def test_10k_detection(self):
        query = "Review the 10-K filing for fiscal year 2024"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "REGULATORY_MARKER" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_8k_detection(self):
        query = "An 8-K was filed yesterday"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "REGULATORY_MARKER" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_proxy_statement(self):
        query = "The proxy statement includes executive compensation"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "REGULATORY_MARKER" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_form4_detection(self):
        query = "Check Form 4 filings from last week"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "REGULATORY_MARKER" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_s1_detection(self):
        query = "The S-1 registration statement was filed"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "REGULATORY_MARKER" in _entity_types(result)


class TestCovenantTerms:
    """Covenant and credit term detection."""

    @pytest.mark.asyncio
    async def test_leverage_ratio(self):
        query = "The leverage ratio covenant requires 3.5x maximum"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "COVENANT_TERM" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_debt_covenant(self):
        query = "Check the debt covenant compliance status"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "COVENANT_TERM" in _entity_types(result)

    @pytest.mark.asyncio
    async def test_interest_coverage(self):
        query = "What is the interest coverage ratio this quarter"
        result = await extract_entities(query.split(), query, "FINANCE")
        assert "COVENANT_TERM" in _entity_types(result)


class TestCleanQuery:
    """No entities on innocuous input."""

    @pytest.mark.asyncio
    async def test_no_entities_on_clean_query(self):
        query = "What is the weather like today"
        result = await extract_entities(query.split(), query, "GENERIC")
        assert result.data["pii_types_detected"] == []
        # May still have some entities from spaCy if loaded, but no PII
        pii_entities = [
            e for e in result.data["entities_detected"]
            if e["type"].startswith("PII_")
        ]
        assert pii_entities == []


class TestCustomerEntityRegistry:
    """Customer entity registry matching."""

    @pytest.mark.asyncio
    async def test_registry_match(self):
        query = "What is the exposure to Acme Corp"
        registry = {"Acme Corp", "Globex Industries"}
        result = await extract_entities(
            query.split(), query, "FINANCE",
            customer_entity_registry=registry,
        )
        counterparty_entities = [
            e for e in result.data["entities_detected"]
            if e["type"] == "COUNTERPARTY_NAME"
        ]
        values = [e["value"] for e in counterparty_entities]
        assert "Acme Corp" in values

    @pytest.mark.asyncio
    async def test_registry_no_match(self):
        query = "What is the weather today"
        registry = {"Acme Corp", "Globex Industries"}
        result = await extract_entities(
            query.split(), query, "GENERIC",
            customer_entity_registry=registry,
        )
        counterparty_entities = [
            e for e in result.data["entities_detected"]
            if e["type"] == "COUNTERPARTY_NAME"
        ]
        assert counterparty_entities == []

    @pytest.mark.asyncio
    async def test_registry_case_insensitive(self):
        query = "What about acme corp exposure"
        registry = {"Acme Corp"}
        result = await extract_entities(
            query.split(), query, "FINANCE",
            customer_entity_registry=registry,
        )
        counterparty_entities = [
            e for e in result.data["entities_detected"]
            if e["type"] == "COUNTERPARTY_NAME"
        ]
        assert len(counterparty_entities) >= 1


class TestStageResultShape:
    """Structural guarantees of the stage result."""

    @pytest.mark.asyncio
    async def test_stage_name(self):
        result = await extract_entities(["hello"], "hello", "GENERIC")
        assert result.stage_name == "entity_extractor"

    @pytest.mark.asyncio
    async def test_no_error_on_valid_input(self):
        result = await extract_entities(["test"], "test", "GENERIC")
        assert result.error is None
