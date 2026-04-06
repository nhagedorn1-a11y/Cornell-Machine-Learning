"""Unit tests for Stage 4 -- Exposure Scorer."""

from __future__ import annotations

import pytest

from arbiter_triage.stages.exposure_scorer import (
    score_exposure,
    _WEIGHTS,
)


class TestScoreRange:
    """Exposure score is always in [0, 100]."""

    @pytest.mark.asyncio
    async def test_score_in_range_simple(self):
        result = await score_exposure(
            query="What is revenue",
            tokens=["What", "is", "revenue"],
            token_count=3,
        )
        score = result.data["exposure_score"]
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_score_in_range_complex(self):
        result = await score_exposure(
            query=(
                "Analyze the correlation between leverage ratio and interest "
                "coverage, then forecast the implications assuming a 200bps "
                "rate increase, and subsequently derive the optimal hedging "
                "strategy contingent on Basel III requirements while taking "
                "into account the multi-step dependency chain"
            ),
            tokens=[
                "Analyze", "the", "correlation", "between", "leverage",
                "ratio", "and", "interest", "coverage", "then", "forecast",
                "the", "implications", "assuming", "a", "200bps", "rate",
                "increase", "and", "subsequently", "derive", "the",
                "optimal", "hedging", "strategy", "contingent", "on",
                "Basel", "III", "requirements", "while", "taking", "into",
                "account", "the", "multi-step", "dependency", "chain",
            ],
            token_count=38,
        )
        score = result.data["exposure_score"]
        assert 0.0 <= score <= 100.0


class TestAirGapMode:
    """Air-gap mode must return 0 for all components."""

    @pytest.mark.asyncio
    async def test_air_gap_returns_zero(self):
        result = await score_exposure(
            query="Analyze the complex multi-step correlation",
            tokens=["Analyze", "the", "complex", "multi-step", "correlation"],
            token_count=5,
            air_gap_mode=True,
        )
        assert result.data["exposure_score"] == 0.0
        for component_score in result.data["exposure_components"].values():
            assert component_score == 0.0

    @pytest.mark.asyncio
    async def test_air_gap_all_component_keys_present(self):
        result = await score_exposure(
            query="Some query", tokens=["Some", "query"],
            token_count=2, air_gap_mode=True,
        )
        for key in _WEIGHTS:
            assert key in result.data["exposure_components"]


class TestComplexVsSimple:
    """Complex queries should score higher than simple ones."""

    @pytest.mark.asyncio
    async def test_complex_scores_higher_than_simple(self):
        simple_result = await score_exposure(
            query="What is revenue",
            tokens=["What", "is", "revenue"],
            token_count=3,
        )
        complex_result = await score_exposure(
            query=(
                "Analyze and compare the quarterly revenue trends, then "
                "evaluate the implications of the interest coverage ratio "
                "assuming current market conditions, and subsequently "
                "forecast the optimized capital structure"
            ),
            tokens=[
                "Analyze", "and", "compare", "the", "quarterly", "revenue",
                "trends", "then", "evaluate", "the", "implications", "of",
                "the", "interest", "coverage", "ratio", "assuming", "current",
                "market", "conditions", "and", "subsequently", "forecast",
                "the", "optimized", "capital", "structure",
            ],
            token_count=27,
        )
        assert complex_result.data["exposure_score"] > simple_result.data["exposure_score"]


class TestSimpleQueryLowScore:
    """Simple queries should produce a low exposure score."""

    @pytest.mark.asyncio
    async def test_simple_query_low(self):
        result = await score_exposure(
            query="Hello",
            tokens=["Hello"],
            token_count=1,
        )
        score = result.data["exposure_score"]
        assert score < 50.0, "A trivial query should not need frontier model access"


class TestComponentWeights:
    """Exposure component weights must sum to 1.0."""

    def test_weights_sum_to_one(self):
        total = sum(_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=1e-9)


class TestStageResultShape:
    """Result structure verification."""

    @pytest.mark.asyncio
    async def test_stage_name_and_keys(self):
        result = await score_exposure(
            query="test", tokens=["test"], token_count=1,
        )
        assert result.stage_name == "exposure_scorer"
        assert result.error is None
        assert "exposure_score" in result.data
        assert "exposure_components" in result.data

    @pytest.mark.asyncio
    async def test_elapsed_ms_non_negative(self):
        result = await score_exposure(
            query="test", tokens=["test"], token_count=1,
        )
        assert result.elapsed_ms >= 0.0
