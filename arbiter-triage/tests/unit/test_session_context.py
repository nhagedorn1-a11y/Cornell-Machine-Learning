"""Unit tests for session context accumulation."""
import pytest
from arbiter_triage.stages.session_context import SessionContextManager

@pytest.mark.asyncio
async def test_session_creation():
    mgr = SessionContextManager()
    session = await mgr.get_or_create_session("sess1", "user1")
    assert session.session_id == "sess1"
    assert session.cumulative_sensitivity == 0.0

@pytest.mark.asyncio
async def test_cumulative_decay():
    mgr = SessionContextManager(default_decay=0.85)
    await mgr.get_or_create_session("sess1", "user1")
    session = await mgr.update_session("sess1", 80.0, [], [], "AMBER")
    # cumulative = 0 * 0.85 + 80 * 0.15 = 12.0
    assert abs(session.cumulative_sensitivity - 12.0) < 0.1

@pytest.mark.asyncio
async def test_cumulative_builds_up():
    mgr = SessionContextManager(default_decay=0.85)
    await mgr.get_or_create_session("sess1", "user1")
    for _ in range(30):
        await mgr.update_session("sess1", 90.0, [], [], "AMBER")
    session = mgr._sessions["sess1"]
    # After many high-sensitivity queries, cumulative should be high
    assert session.cumulative_sensitivity > 60

@pytest.mark.asyncio
async def test_elevation_green_to_amber():
    mgr = SessionContextManager(default_decay=0.85)
    await mgr.get_or_create_session("sess1", "user1")
    # Force cumulative above 60
    mgr._sessions["sess1"].cumulative_sensitivity = 65.0
    result = await mgr.evaluate_elevation("sess1", "GREEN")
    assert result.data["context_elevated"] is True
    assert result.data["elevated_lane"] == "AMBER"

@pytest.mark.asyncio
async def test_elevation_amber_to_red():
    mgr = SessionContextManager(default_decay=0.85)
    await mgr.get_or_create_session("sess1", "user1")
    mgr._sessions["sess1"].cumulative_sensitivity = 85.0
    result = await mgr.evaluate_elevation("sess1", "AMBER")
    assert result.data["context_elevated"] is True
    assert result.data["elevated_lane"] == "RED"

@pytest.mark.asyncio
async def test_elevation_green_to_red_direct():
    mgr = SessionContextManager(default_decay=0.85)
    await mgr.get_or_create_session("sess1", "user1")
    mgr._sessions["sess1"].cumulative_sensitivity = 95.0
    result = await mgr.evaluate_elevation("sess1", "GREEN")
    assert result.data["context_elevated"] is True
    assert result.data["elevated_lane"] == "RED"

@pytest.mark.asyncio
async def test_no_elevation_below_threshold():
    mgr = SessionContextManager(default_decay=0.85)
    await mgr.get_or_create_session("sess1", "user1")
    mgr._sessions["sess1"].cumulative_sensitivity = 30.0
    result = await mgr.evaluate_elevation("sess1", "GREEN")
    assert result.data["context_elevated"] is False

@pytest.mark.asyncio
async def test_lru_eviction():
    mgr = SessionContextManager()
    for i in range(205):
        await mgr.get_or_create_session(f"sess{i}", "user1")
    assert len(mgr._sessions) <= 200

@pytest.mark.asyncio
async def test_cleanup_expired():
    import datetime
    mgr = SessionContextManager(timeout_minutes=0)  # 0 min timeout = everything expires
    await mgr.get_or_create_session("sess1", "user1")
    mgr._sessions["sess1"].last_activity = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    await mgr.cleanup_expired()
    assert "sess1" not in mgr._sessions
