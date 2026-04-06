"""Unit tests for the record store."""

import pytest
import tempfile
import os
import uuid
from datetime import datetime, timezone

from arbiter_triage.storage.record_store import RecordStore
from arbiter_triage.models import TriageDecisionRecord


@pytest.fixture
async def store(tmp_path):
    """Create a RecordStore backed by a temporary database file."""
    db_path = str(tmp_path / "test_records.db")
    rs = RecordStore(db_path=db_path)
    await rs.initialize()
    yield rs
    await rs.close()


def _make_record(**kwargs) -> TriageDecisionRecord:
    """Create a TriageDecisionRecord with sensible defaults."""
    record = TriageDecisionRecord(
        record_id=kwargs.get("record_id", str(uuid.uuid4())),
        session_id=kwargs.get("session_id", "session-1"),
        query_id=kwargs.get("query_id", str(uuid.uuid4())),
        user_id=kwargs.get("user_id", "test-user"),
        timestamp=kwargs.get("timestamp", datetime.now(timezone.utc)),
        query_hash=kwargs.get("query_hash", "abc123"),
        sensitivity_score=kwargs.get("sensitivity_score", 42.0),
        exposure_score=kwargs.get("exposure_score", 15.0),
        sensitivity_band=kwargs.get("sensitivity_band", "MEDIUM"),
        exposure_band=kwargs.get("exposure_band", "NONE"),
        final_lane=kwargs.get("final_lane", "GREEN"),
        decision_reason=kwargs.get("decision_reason", "test record"),
        previous_record_hash=kwargs.get("previous_record_hash", ""),
    )
    record.compute_record_hash()
    return record


# ── Initialization ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_initialize_creates_table(tmp_path):
    """After initialize(), the records table should exist in the db."""
    db_path = str(tmp_path / "init_test.db")
    rs = RecordStore(db_path=db_path)
    await rs.initialize()

    # Verify the file exists
    assert os.path.exists(db_path)

    # Verify we can count records (table exists)
    count = await rs.count_records()
    assert count == 0

    await rs.close()


# ── Write and read ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_write_and_read_record(store):
    """A record written to the store should be retrievable by record_id."""
    record = _make_record()
    returned_id = await store.write_record(record)
    assert returned_id == record.record_id

    fetched = await store.get_record(record.record_id)
    assert fetched is not None
    assert fetched["record_id"] == record.record_id
    assert fetched["session_id"] == record.session_id
    assert fetched["user_id"] == record.user_id
    assert fetched["sensitivity_score"] == record.sensitivity_score
    assert fetched["final_lane"] == record.final_lane


# ── Last record hash ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_last_record_hash_empty(store):
    """On an empty store, get_last_record_hash returns empty string."""
    last_hash = await store.get_last_record_hash()
    assert last_hash == ""


@pytest.mark.asyncio
async def test_get_last_record_hash(store):
    """After writing records, get_last_record_hash returns the latest hash."""
    r1 = _make_record()
    await store.write_record(r1)

    r2 = _make_record(previous_record_hash=r1.record_hash)
    await store.write_record(r2)

    last_hash = await store.get_last_record_hash()
    assert last_hash == r2.record_hash


# ── Hash-chain verification ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_chain_verification_with_10_linked_records(store):
    """A chain of 10 properly linked records should verify successfully."""
    prev_hash = ""

    for i in range(10):
        record = _make_record(
            previous_record_hash=prev_hash,
            decision_reason=f"test record {i}",
        )
        await store.write_record(record)
        prev_hash = record.record_hash

    valid, msg = await store.verify_chain(last_n=10)
    assert valid is True, f"Chain verification failed: {msg}"
    assert "10 record(s) verified" in msg


# ── Immutability ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_records_are_never_modified_after_write(store):
    """Records must not be modifiable after they have been written."""
    record = _make_record()
    await store.write_record(record)

    # Read the record back
    fetched_before = await store.get_record(record.record_id)
    assert fetched_before is not None

    # Attempting to write the same record_id again should raise (PRIMARY KEY conflict)
    duplicate = _make_record(record_id=record.record_id, decision_reason="tampered")
    duplicate.compute_record_hash()

    with pytest.raises(Exception):
        await store.write_record(duplicate)

    # Verify the original data is unchanged
    fetched_after = await store.get_record(record.record_id)
    assert fetched_after is not None
    assert fetched_after["decision_reason"] == "test record"
    assert fetched_after["record_hash"] == fetched_before["record_hash"]


# ── Count ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_count_records(store):
    """count_records should reflect the number of inserted records."""
    assert await store.count_records() == 0

    for _ in range(5):
        await store.write_record(_make_record())

    assert await store.count_records() == 5
