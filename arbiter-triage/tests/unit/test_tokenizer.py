"""Unit tests for Stage 1 -- Tokenizer."""

from __future__ import annotations

import pytest

from arbiter_triage.models import StageResult
from arbiter_triage.stages.tokenizer import tokenize


class TestTokenizerBasic:
    """Core tokenization behaviour."""

    @pytest.mark.asyncio
    async def test_basic_tokenization_produces_correct_count(self):
        result = await tokenize("What is the leverage ratio for Acme Corp")
        assert isinstance(result, StageResult)
        assert result.stage_name == "tokenizer"
        assert result.data["token_count"] == len(result.data["tokens"])
        assert result.data["token_count"] > 0

    @pytest.mark.asyncio
    async def test_empty_string_returns_zero_tokens(self):
        result = await tokenize("")
        assert result.data["token_count"] == 0
        assert result.data["tokens"] == []
        assert result.data["numerical_token_ratio"] == 0.0

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_zero_tokens(self):
        result = await tokenize("     \t  \n  ")
        assert result.data["token_count"] == 0
        assert result.data["tokens"] == []

    @pytest.mark.asyncio
    async def test_numerical_token_detection(self):
        result = await tokenize("Revenue was $5,000,000 or 12.5% growth")
        num_count = result.data["numerical_token_count"]
        assert num_count >= 1, "Should detect at least one numerical token"

    @pytest.mark.asyncio
    async def test_numerical_token_ratio_range(self):
        result = await tokenize("100 200 300 hello world")
        ratio = result.data["numerical_token_ratio"]
        assert 0.0 <= ratio <= 1.0

    @pytest.mark.asyncio
    async def test_all_numeric_tokens_ratio_is_one(self):
        result = await tokenize("100 200 300")
        assert result.data["numerical_token_ratio"] == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_result_is_stage_result_no_error(self):
        result = await tokenize("A perfectly normal query about weather")
        assert isinstance(result, StageResult)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_elapsed_ms_is_non_negative(self):
        result = await tokenize("timing check")
        assert result.elapsed_ms >= 0.0

    @pytest.mark.asyncio
    async def test_single_token(self):
        result = await tokenize("hello")
        assert result.data["token_count"] == 1
        assert result.data["tokens"] == ["hello"]

    @pytest.mark.asyncio
    async def test_punctuation_handling(self):
        result = await tokenize("Hello, world! How are you?")
        tokens = result.data["tokens"]
        # Punctuation should be consumed as delimiters, not appear as tokens
        for t in tokens:
            assert t not in (",", "!", "?")
