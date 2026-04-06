"""Unit tests for data models."""

import pytest
import uuid
from datetime import datetime, timezone

from arbiter_triage.models import (
    FrontierPayload,
    LANE_ORDER,
    TriageDecisionRecord,
    higher_lane,
)


# ── TriageDecisionRecord hash computation ─────────────────────────────


class TestTriageDecisionRecordHash:
    """Tests for TriageDecisionRecord.compute_record_hash."""

    def test_hash_is_deterministic(self):
        """Computing the hash twice on the same record yields identical results."""
        record = TriageDecisionRecord(
            record_id="fixed-id",
            session_id="session-1",
            query_id="query-1",
            user_id="user-1",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            sensitivity_score=50.0,
            exposure_score=30.0,
            final_lane="AMBER",
        )

        hash1 = record.compute_record_hash()
        hash2 = record.compute_record_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_hash_deterministic_across_instances(self):
        """Two records with identical fields produce the same hash."""
        kwargs = dict(
            record_id="fixed-id",
            session_id="session-1",
            query_id="query-1",
            user_id="user-1",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            sensitivity_score=50.0,
            exposure_score=30.0,
            final_lane="AMBER",
        )

        r1 = TriageDecisionRecord(**kwargs)
        r2 = TriageDecisionRecord(**kwargs)

        assert r1.compute_record_hash() == r2.compute_record_hash()

    def test_hash_changes_when_sensitivity_score_changes(self):
        """Changing the sensitivity_score must produce a different hash."""
        base = dict(
            record_id="fixed-id",
            session_id="session-1",
            query_id="query-1",
            user_id="user-1",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            final_lane="GREEN",
        )

        r1 = TriageDecisionRecord(**base, sensitivity_score=10.0)
        r2 = TriageDecisionRecord(**base, sensitivity_score=90.0)

        assert r1.compute_record_hash() != r2.compute_record_hash()

    def test_hash_changes_when_final_lane_changes(self):
        """Changing the final_lane must produce a different hash."""
        base = dict(
            record_id="fixed-id",
            session_id="session-1",
            query_id="query-1",
            user_id="user-1",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            sensitivity_score=50.0,
        )

        r1 = TriageDecisionRecord(**base, final_lane="GREEN")
        r2 = TriageDecisionRecord(**base, final_lane="RED")

        assert r1.compute_record_hash() != r2.compute_record_hash()

    def test_hash_changes_when_user_id_changes(self):
        """Changing the user_id must produce a different hash."""
        base = dict(
            record_id="fixed-id",
            session_id="session-1",
            query_id="query-1",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            sensitivity_score=50.0,
            final_lane="GREEN",
        )

        r1 = TriageDecisionRecord(**base, user_id="alice")
        r2 = TriageDecisionRecord(**base, user_id="bob")

        assert r1.compute_record_hash() != r2.compute_record_hash()

    def test_hash_changes_when_previous_record_hash_changes(self):
        """Changing previous_record_hash must produce a different hash."""
        base = dict(
            record_id="fixed-id",
            session_id="session-1",
            query_id="query-1",
            user_id="user-1",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )

        r1 = TriageDecisionRecord(**base, previous_record_hash="aaa")
        r2 = TriageDecisionRecord(**base, previous_record_hash="bbb")

        assert r1.compute_record_hash() != r2.compute_record_hash()


# ── FrontierPayload hash computation ──────────────────────────────────


class TestFrontierPayloadHash:
    """Tests for FrontierPayload.compute_hash."""

    def test_hash_is_deterministic(self):
        """Computing the hash twice yields the same result."""
        payload = FrontierPayload(sanitized_content="Hello world")

        hash1 = payload.compute_hash()
        hash2 = payload.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_hash_depends_on_content(self):
        """Different sanitized_content values produce different hashes."""
        p1 = FrontierPayload(sanitized_content="Hello world")
        p2 = FrontierPayload(sanitized_content="Goodbye world")

        assert p1.compute_hash() != p2.compute_hash()

    def test_hash_stored_on_payload(self):
        """compute_hash should set the payload_hash attribute."""
        payload = FrontierPayload(sanitized_content="test content")
        result = payload.compute_hash()

        assert payload.payload_hash == result
        assert payload.payload_hash != ""


# ── higher_lane ───────────────────────────────────────────────────────


class TestHigherLane:
    """Tests for the higher_lane helper function."""

    def test_red_beats_green(self):
        assert higher_lane("RED", "GREEN") == "RED"

    def test_red_beats_amber(self):
        assert higher_lane("RED", "AMBER") == "RED"

    def test_amber_beats_green(self):
        assert higher_lane("AMBER", "GREEN") == "AMBER"

    def test_same_lane_returned(self):
        assert higher_lane("GREEN", "GREEN") == "GREEN"
        assert higher_lane("AMBER", "AMBER") == "AMBER"
        assert higher_lane("RED", "RED") == "RED"

    def test_is_commutative(self):
        """higher_lane(a, b) == higher_lane(b, a) for all combinations."""
        lanes = ["GREEN", "AMBER", "RED"]
        for a in lanes:
            for b in lanes:
                assert higher_lane(a, b) == higher_lane(b, a)

    def test_unknown_lane_defaults_to_red(self):
        """Unknown lane names should be treated as RED (most restrictive)."""
        assert higher_lane("UNKNOWN", "GREEN") == "UNKNOWN"
        assert higher_lane("GREEN", "INVALID") == "INVALID"


# ── LANE_ORDER ────────────────────────────────────────────────────────


class TestLaneOrder:
    """Tests for the LANE_ORDER constant."""

    def test_contains_all_lanes(self):
        assert "GREEN" in LANE_ORDER
        assert "AMBER" in LANE_ORDER
        assert "RED" in LANE_ORDER

    def test_ordering_is_correct(self):
        assert LANE_ORDER["GREEN"] < LANE_ORDER["AMBER"]
        assert LANE_ORDER["AMBER"] < LANE_ORDER["RED"]

    def test_green_is_least_restrictive(self):
        assert LANE_ORDER["GREEN"] == min(LANE_ORDER.values())

    def test_red_is_most_restrictive(self):
        assert LANE_ORDER["RED"] == max(LANE_ORDER.values())
