"""Unit tests for the rule engine — most critical test file."""
import pytest
from arbiter_triage.stages.rule_engine import evaluate_rules

@pytest.mark.asyncio
async def test_covenant_triggers_red():
    result = await evaluate_rules("What is our debt covenant status?", ["what", "is", "our", "debt", "covenant", "status"], {}, 0, [], [], 6)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_merger_triggers_red():
    result = await evaluate_rules("Details on the acquisition target company", ["details", "on", "the", "acquisition", "target", "company"], {}, 0, [], [], 6)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_10k_triggers_red():
    result = await evaluate_rules("Review the 10-K filing details", ["review", "the", "10-K", "filing", "details"], {}, 0, [], [], 5)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_mnpi_triggers_red():
    result = await evaluate_rules("This contains material non-public information", ["this", "contains", "material", "non-public", "information"], {}, 0, [], [], 5)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_board_minutes_triggers_red():
    result = await evaluate_rules("Access the board minutes from last meeting", ["access", "the", "board", "minutes", "from", "last", "meeting"], {}, 0, [], [], 7)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_credit_facility_triggers_red():
    result = await evaluate_rules("What is the revolving credit facility balance?", ["what", "is", "the", "revolving", "credit", "facility", "balance"], {}, 0, [], [], 7)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_due_diligence_triggers_red():
    result = await evaluate_rules("Start the due diligence process", ["start", "the", "due", "diligence", "process"], {}, 0, [], [], 5)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_nda_triggers_red():
    result = await evaluate_rules("Review the NDA terms", ["review", "the", "NDA", "terms"], {}, 0, [], [], 4)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_executive_compensation_triggers_red():
    result = await evaluate_rules("What is the executive compensation package?", ["what", "is", "the", "executive", "compensation", "package"], {}, 0, [], [], 6)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_green_simple_definition():
    result = await evaluate_rules("What is a balance sheet?", ["what", "is", "a", "balance", "sheet"], {}, 0, [], [], 5)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "GREEN"

@pytest.mark.asyncio
async def test_green_fails_with_numbers():
    result = await evaluate_rules("What is a $500M balance sheet?", ["what", "is", "a", "$500M", "balance", "sheet"], {}, 1, [], [], 6)
    # Should NOT match GREEN because numerical tokens > 0
    assert result.data.get("lane_override") != "GREEN" or result.data.get("hard_rule_fired") is False

@pytest.mark.asyncio
async def test_green_fails_with_entities():
    result = await evaluate_rules("What is Acme Corp revenue?", ["what", "is", "acme", "corp", "revenue"], {}, 0, ["Acme Corp"], [], 5)
    # Should NOT match GREEN because named entities present
    assert result.data.get("lane_override") != "GREEN" or result.data.get("hard_rule_fired") is False

@pytest.mark.asyncio
async def test_green_fails_long_query():
    tokens = [f"word{i}" for i in range(60)]
    query = "What is " + " ".join(tokens)
    result = await evaluate_rules(query, ["what", "is"] + tokens, {}, 0, [], [], 62)
    # Should NOT match GREEN because token count > 50
    assert result.data.get("lane_override") != "GREEN" or result.data.get("hard_rule_fired") is False

@pytest.mark.asyncio
async def test_no_rule_fires():
    result = await evaluate_rules("Show me the sales data for last quarter", ["show", "me", "the", "sales", "data", "for", "last", "quarter"], {}, 0, [], [], 8)
    assert result.data["hard_rule_fired"] is False

@pytest.mark.asyncio
async def test_case_insensitivity():
    result = await evaluate_rules("WHAT IS OUR DEBT COVENANT?", ["WHAT", "IS", "OUR", "DEBT", "COVENANT"], {}, 0, [], [], 5)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_red_entity_type():
    result = await evaluate_rules("Check the credit agreement", ["check", "the", "credit", "agreement"], {"entities_detected": [{"type": "CREDIT_AGREEMENT"}]}, 0, [], [], 4)
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "RED"

@pytest.mark.asyncio
async def test_pre_approved_template():
    import hashlib
    query = "show me the dashboard"
    normalized = " ".join(query.lower().split())
    h = hashlib.sha256(normalized.encode()).hexdigest()
    result = await evaluate_rules(query, ["show", "me", "the", "dashboard"], {}, 0, [], [], 4, pre_approved_hashes={h})
    assert result.data["hard_rule_fired"] is True
    assert result.data["lane_override"] == "GREEN"
    assert result.data["rule_type"] == "PRE_APPROVED"
