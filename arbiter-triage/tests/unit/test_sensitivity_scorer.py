"""Unit tests for Stage 3 -- Sensitivity Scorer."""

from __future__ import annotations

import pytest

from arbiter_triage.stages.sensitivity_scorer import (
    score_sensitivity,
    _WEIGHTS,
    _score_pii_presence,
    _score_financial_entity_density,
    _score_named_counterparty,
    _score_contractual_terms,
    _score_regulatory_markers,
    _score_numerical_density,
    _score_customer_sensitivity_profile,
)


class TestScoreRange:
    """Final score is always in [0, 100]."""

    @pytest.mark.asyncio
    async def test_score_in_range_clean(self):
        result = await score_sensitivity(
            query="What is the weather",
            tokens=["What", "is", "the", "weather"],
            entities={},
            numerical_ratio=0.0,
            vertical_pack="GENERIC",
        )
        score = result.data["sensitivity_score"]
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_score_in_range_heavy(self):
        result = await score_sensitivity(
            query="SSN 123-45-6789 email a@b.com leverage ratio 10-K $5M covenant breach",
            tokens=["SSN", "123-45-6789", "email", "a@b.com", "leverage",
                     "ratio", "10-K", "$5M", "covenant", "breach"],
            entities={
                "pii_types": ["ssn", "email"],
                "financial": ["$5M"],
                "regulatory": ["10-K"],
                "named_entities": [],
                "customer_registry_matches": [],
            },
            numerical_ratio=0.2,
            vertical_pack="FINANCE",
            customer_sensitivity_profile=80.0,
        )
        score = result.data["sensitivity_score"]
        assert 0.0 <= score <= 100.0


class TestZeroSensitivity:
    """Clean queries with no sensitive content should score low."""

    @pytest.mark.asyncio
    async def test_clean_query_low_score(self):
        result = await score_sensitivity(
            query="what is the weather like today",
            tokens=["what", "is", "the", "weather", "like", "today"],
            entities={},
            numerical_ratio=0.0,
            vertical_pack="GENERIC",
            customer_sensitivity_profile=0.0,
        )
        score = result.data["sensitivity_score"]
        # With no PII, no financial, no entities, no regulatory, no numerics,
        # and customer profile at 0, the score should be very low
        assert score < 10.0


class TestHighSensitivity:
    """PII-heavy queries should score high."""

    @pytest.mark.asyncio
    async def test_pii_heavy_high_score(self):
        result = await score_sensitivity(
            query="SSN 123-45-6789 and credit card and passport",
            tokens=["SSN", "123-45-6789", "and", "credit", "card", "and", "passport"],
            entities={
                "pii_types": ["ssn", "credit_card", "passport"],
                "financial": [],
                "regulatory": [],
                "named_entities": [],
                "customer_registry_matches": [],
            },
            numerical_ratio=0.1,
            vertical_pack="GENERIC",
            customer_sensitivity_profile=50.0,
        )
        score = result.data["sensitivity_score"]
        assert score > 25.0, "PII-heavy query should produce a significant sensitivity score"


class TestComponentWeights:
    """Component weights must sum to 1.0."""

    def test_weights_sum_to_one(self):
        total = sum(_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_all_components_present(self):
        expected = {
            "pii_presence",
            "financial_entity_density",
            "named_counterparty_detection",
            "contractual_term_detection",
            "regulatory_data_markers",
            "numerical_density",
            "customer_sensitivity_profile",
        }
        assert set(_WEIGHTS.keys()) == expected


class TestSubScoreRanges:
    """Each sub-component must produce values in [0, 100]."""

    def test_pii_presence_zero(self):
        assert _score_pii_presence({}) == 0.0

    def test_pii_presence_max(self):
        score = _score_pii_presence({"pii_types": ["ssn", "credit_card", "passport"]})
        assert 0.0 <= score <= 100.0

    def test_pii_presence_single_ssn(self):
        score = _score_pii_presence({"pii_types": ["ssn"]})
        assert score == 90.0

    def test_financial_entity_density_zero(self):
        assert _score_financial_entity_density({}, 10) == 0.0

    def test_financial_entity_density_nonzero(self):
        score = _score_financial_entity_density(
            {"financial": ["$1M", "$2M", "$3M"]}, 10,
        )
        assert 0.0 <= score <= 100.0

    def test_financial_entity_density_zero_tokens(self):
        score = _score_financial_entity_density({"financial": ["$1M"]}, 0)
        assert score == 0.0

    def test_named_counterparty_zero(self):
        assert _score_named_counterparty({}) == 0.0

    def test_named_counterparty_registry_match(self):
        score = _score_named_counterparty(
            {"customer_registry_matches": ["Acme Corp"]},
        )
        assert score == 90.0

    def test_named_counterparty_single_named(self):
        score = _score_named_counterparty({"named_entities": ["Goldman Sachs"]})
        assert score == 40.0

    def test_named_counterparty_multiple_named(self):
        score = _score_named_counterparty(
            {"named_entities": ["Goldman Sachs", "JP Morgan"]},
        )
        assert score == 70.0

    def test_contractual_terms_zero(self):
        assert _score_contractual_terms("hello world") == 0.0

    def test_contractual_terms_some(self):
        score = _score_contractual_terms("indemnification liability breach")
        assert 0.0 < score <= 100.0

    def test_regulatory_markers_zero(self):
        assert _score_regulatory_markers({}, "hello world") == 0.0

    def test_regulatory_markers_high_value(self):
        score = _score_regulatory_markers(
            {"regulatory": ["10-K"]}, "review the 10-k filing",
        )
        assert score > 0.0

    def test_numerical_density_zero(self):
        assert _score_numerical_density(0.0) == 0.0

    def test_numerical_density_full(self):
        assert _score_numerical_density(1.0) == 100.0

    def test_numerical_density_half(self):
        assert _score_numerical_density(0.5) == 50.0

    def test_customer_sensitivity_clamped_low(self):
        assert _score_customer_sensitivity_profile(-10.0) == 0.0

    def test_customer_sensitivity_clamped_high(self):
        assert _score_customer_sensitivity_profile(200.0) == 100.0

    def test_customer_sensitivity_passthrough(self):
        assert _score_customer_sensitivity_profile(42.0) == 42.0


class TestStageResultShape:
    """Result structure verification."""

    @pytest.mark.asyncio
    async def test_stage_name(self):
        result = await score_sensitivity(
            query="test", tokens=["test"], entities={},
            numerical_ratio=0.0, vertical_pack="GENERIC",
        )
        assert result.stage_name == "sensitivity_scorer"
        assert result.error is None
        assert "sensitivity_score" in result.data
        assert "sensitivity_components" in result.data
        assert "sub_scores" in result.data
