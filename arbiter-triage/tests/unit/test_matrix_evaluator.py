"""Unit tests for matrix evaluation."""
import pytest
from arbiter_triage.stages.matrix_evaluator import (
    evaluate_matrix, get_sensitivity_band, get_exposure_band,
    DECISION_MATRIX, SENSITIVITY_BANDS, EXPOSURE_BANDS,
)

def test_sensitivity_bands():
    assert get_sensitivity_band(0) == "NONE"
    assert get_sensitivity_band(20) == "NONE"
    assert get_sensitivity_band(21) == "LOW"
    assert get_sensitivity_band(40) == "LOW"
    assert get_sensitivity_band(41) == "MEDIUM"
    assert get_sensitivity_band(60) == "MEDIUM"
    assert get_sensitivity_band(61) == "HIGH"
    assert get_sensitivity_band(80) == "HIGH"
    assert get_sensitivity_band(81) == "CRITICAL"
    assert get_sensitivity_band(100) == "CRITICAL"

def test_exposure_bands():
    assert get_exposure_band(0) == "NONE"
    assert get_exposure_band(20) == "NONE"
    assert get_exposure_band(21) == "MINIMAL"
    assert get_exposure_band(40) == "MINIMAL"
    assert get_exposure_band(41) == "MODERATE"
    assert get_exposure_band(60) == "MODERATE"
    assert get_exposure_band(61) == "SIGNIFICANT"
    assert get_exposure_band(80) == "SIGNIFICANT"
    assert get_exposure_band(81) == "ESSENTIAL"
    assert get_exposure_band(100) == "ESSENTIAL"

@pytest.mark.asyncio
async def test_all_matrix_combinations():
    """Test all 25 matrix combinations produce correct lane."""
    test_cases = [
        (10, 10, "GREEN"),   # NONE, NONE
        (10, 30, "GREEN"),   # NONE, MINIMAL
        (10, 50, "GREEN"),   # NONE, MODERATE
        (10, 70, "GREEN"),   # NONE, SIGNIFICANT
        (10, 90, "GREEN"),   # NONE, ESSENTIAL
        (30, 10, "GREEN"),   # LOW, NONE
        (30, 30, "GREEN"),   # LOW, MINIMAL
        (30, 50, "GREEN"),   # LOW, MODERATE
        (30, 70, "AMBER"),   # LOW, SIGNIFICANT
        (30, 90, "AMBER"),   # LOW, ESSENTIAL
        (50, 10, "GREEN"),   # MEDIUM, NONE
        (50, 30, "GREEN"),   # MEDIUM, MINIMAL
        (50, 50, "AMBER"),   # MEDIUM, MODERATE
        (50, 70, "AMBER"),   # MEDIUM, SIGNIFICANT
        (50, 90, "RED"),     # MEDIUM, ESSENTIAL
        (70, 10, "GREEN"),   # HIGH, NONE
        (70, 30, "AMBER"),   # HIGH, MINIMAL
        (70, 50, "AMBER"),   # HIGH, MODERATE
        (70, 70, "RED"),     # HIGH, SIGNIFICANT
        (70, 90, "RED"),     # HIGH, ESSENTIAL
        (90, 10, "GREEN"),   # CRITICAL, NONE
        (90, 30, "AMBER"),   # CRITICAL, MINIMAL
        (90, 50, "RED"),     # CRITICAL, MODERATE
        (90, 70, "RED"),     # CRITICAL, SIGNIFICANT
        (90, 90, "RED"),     # CRITICAL, ESSENTIAL
    ]
    for sens, exp, expected_lane in test_cases:
        result = await evaluate_matrix(sens, exp)
        assert result.data["lane"] == expected_lane, f"Failed for sens={sens}, exp={exp}: got {result.data['lane']}, expected {expected_lane}"

@pytest.mark.asyncio
async def test_boundary_zero():
    result = await evaluate_matrix(0.0, 0.0)
    assert result.data["lane"] == "GREEN"

@pytest.mark.asyncio
async def test_boundary_max():
    result = await evaluate_matrix(100.0, 100.0)
    assert result.data["lane"] == "RED"

@pytest.mark.asyncio
async def test_result_has_bands():
    result = await evaluate_matrix(50, 70)
    assert result.data["sensitivity_band"] == "MEDIUM"
    assert result.data["exposure_band"] == "SIGNIFICANT"
