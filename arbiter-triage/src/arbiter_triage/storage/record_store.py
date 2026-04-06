"""Async decision record storage for the Arbiter Triage Engine.

Stores immutable TriageDecisionRecord objects in an append-only SQLite
table with hash-chain integrity verification.

NOTE: In production the ``data`` column MUST be encrypted at rest
(e.g., AES-256-GCM with an HSM-managed key).  The current implementation
stores plain JSON — encryption should be added before deployment to any
environment handling real data.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from arbiter_triage.models import TriageDecisionRecord

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = "/var/lib/arbiter/triage/records.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS records (
    record_id            TEXT PRIMARY KEY,
    session_id           TEXT NOT NULL,
    query_id             TEXT NOT NULL,
    user_id              TEXT NOT NULL,
    timestamp            TEXT NOT NULL,
    data                 TEXT NOT NULL,
    record_hash          TEXT NOT NULL,
    previous_record_hash TEXT NOT NULL
);
"""

# -- NOTE: In production, ``data`` would be encrypted (AES-256-GCM). --

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_records_session_id ON records (session_id);",
    "CREATE INDEX IF NOT EXISTS idx_records_timestamp ON records (timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_records_record_hash ON records (record_hash);",
]


def _record_to_data_json(record: TriageDecisionRecord) -> str:
    """Serialize all record fields to a JSON string for storage.

    NOTE: In production this JSON blob would be encrypted before storage.
    """
    payload = {
        "record_id": record.record_id,
        "session_id": record.session_id,
        "query_id": record.query_id,
        "user_id": record.user_id,
        "timestamp": record.timestamp.isoformat(),
        "query_hash": record.query_hash,
        "query_length_tokens": record.query_length_tokens,
        "data_sources_referenced": record.data_sources_referenced,
        "entities_detected": record.entities_detected,
        "pii_types_detected": record.pii_types_detected,
        "sensitivity_components": record.sensitivity_components,
        "exposure_components": record.exposure_components,
        "sensitivity_score": record.sensitivity_score,
        "exposure_score": record.exposure_score,
        "sensitivity_band": record.sensitivity_band,
        "exposure_band": record.exposure_band,
        "hard_rules_evaluated": record.hard_rules_evaluated,
        "hard_rules_fired": record.hard_rules_fired,
        "hard_rule_override": record.hard_rule_override,
        "cumulative_sensitivity_at_time": record.cumulative_sensitivity_at_time,
        "context_elevation_applied": record.context_elevation_applied,
        "context_elevation_reason": record.context_elevation_reason,
        "matrix_result": record.matrix_result,
        "final_lane": record.final_lane,
        "decision_reason": record.decision_reason,
        "frontier_payload_id": record.frontier_payload_id,
        "payload_approved": record.payload_approved,
        "approval_actor": record.approval_actor,
        "approval_timestamp": (
            record.approval_timestamp.isoformat()
            if record.approval_timestamp
            else None
        ),
        "approval_modifications": record.approval_modifications,
        "record_hash": record.record_hash,
        "previous_record_hash": record.previous_record_hash,
    }
    return json.dumps(payload, sort_keys=True, default=str)


class RecordStore:
    """Async SQLite-backed append-only record store with hash-chain integrity.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Parent directories are created
        automatically on ``initialize()``.
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Open database, create table and indexes if they do not exist."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute(_CREATE_TABLE_SQL)
            for idx_sql in _CREATE_INDEXES_SQL:
                await self._db.execute(idx_sql)
            await self._db.commit()
            logger.info("RecordStore initialized at %s", self.db_path)
        except Exception as exc:
            logger.error("RecordStore.initialize failed: %s", exc, exc_info=True)
            raise

    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self._db is not None:
                await self._db.close()
                self._db = None
        except Exception as exc:
            logger.error("RecordStore.close failed: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    # Write (append-only — records are NEVER updated)
    # ------------------------------------------------------------------

    async def write_record(self, record: TriageDecisionRecord) -> str:
        """Insert an immutable decision record and return its ``record_id``.

        Records are **never** updated after insertion.
        """
        try:
            assert self._db is not None, "RecordStore not initialized"
            data_json = _record_to_data_json(record)
            await self._db.execute(
                """
                INSERT INTO records
                    (record_id, session_id, query_id, user_id, timestamp,
                     data, record_hash, previous_record_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.session_id,
                    record.query_id,
                    record.user_id,
                    record.timestamp.isoformat(),
                    data_json,  # NOTE: encrypt in production
                    record.record_hash,
                    record.previous_record_hash,
                ),
            )
            await self._db.commit()
            return record.record_id
        except Exception as exc:
            logger.error("RecordStore.write_record failed: %s", exc, exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    async def get_last_record_hash(self) -> str:
        """Return the ``record_hash`` of the most recent record, or ``""``."""
        try:
            assert self._db is not None, "RecordStore not initialized"
            cursor = await self._db.execute(
                "SELECT record_hash FROM records ORDER BY timestamp DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else ""
        except Exception as exc:
            logger.error(
                "RecordStore.get_last_record_hash failed: %s", exc, exc_info=True
            )
            return ""

    async def get_record(self, record_id: str) -> dict | None:
        """Retrieve a record by its ID, returned as a dict (parsed from JSON)."""
        try:
            assert self._db is not None, "RecordStore not initialized"
            cursor = await self._db.execute(
                "SELECT data FROM records WHERE record_id = ?",
                (record_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return json.loads(row[0])
        except Exception as exc:
            logger.error("RecordStore.get_record failed: %s", exc, exc_info=True)
            return None

    async def count_records(self) -> int:
        """Return the total number of records in the store."""
        try:
            assert self._db is not None, "RecordStore not initialized"
            cursor = await self._db.execute("SELECT COUNT(*) FROM records")
            row = await cursor.fetchone()
            return row[0] if row else 0
        except Exception as exc:
            logger.error("RecordStore.count_records failed: %s", exc, exc_info=True)
            return 0

    # ------------------------------------------------------------------
    # Chain verification
    # ------------------------------------------------------------------

    async def verify_chain(self, last_n: int = 100) -> tuple[bool, str]:
        """Verify the hash chain of the last *last_n* records.

        Each record's ``previous_record_hash`` must equal the preceding
        record's ``record_hash``.  The first record in the chain (or the
        oldest within the window) is allowed to have any
        ``previous_record_hash`` value (including ``""``).

        Returns
        -------
        tuple[bool, str]
            ``(True, "Chain valid ...")`` on success, or
            ``(False, "Chain broken at ...")`` on failure.
        """
        try:
            assert self._db is not None, "RecordStore not initialized"
            cursor = await self._db.execute(
                """
                SELECT record_id, record_hash, previous_record_hash, data
                FROM records
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (last_n,),
            )
            rows = await cursor.fetchall()

            if not rows:
                return True, "Chain valid: no records to verify."

            # Reverse so we walk oldest -> newest.
            rows = list(reversed(rows))

            verified = 0
            for i, row in enumerate(rows):
                record_id, stored_hash, prev_hash, data_json = row

                # Re-derive the hash from the stored data to detect tampering.
                data = json.loads(data_json)
                # Build the same input that compute_record_hash uses.
                hash_input = {
                    "record_id": data.get("record_id", ""),
                    "session_id": data.get("session_id", ""),
                    "query_id": data.get("query_id", ""),
                    "user_id": data.get("user_id", ""),
                    "timestamp": data.get("timestamp", ""),
                    "query_hash": data.get("query_hash", ""),
                    "query_length_tokens": data.get("query_length_tokens", 0),
                    "data_sources_referenced": data.get("data_sources_referenced", []),
                    "entities_detected": data.get("entities_detected", []),
                    "pii_types_detected": data.get("pii_types_detected", []),
                    "sensitivity_components": data.get("sensitivity_components", {}),
                    "exposure_components": data.get("exposure_components", {}),
                    "sensitivity_score": data.get("sensitivity_score", 0.0),
                    "exposure_score": data.get("exposure_score", 0.0),
                    "sensitivity_band": data.get("sensitivity_band", "NONE"),
                    "exposure_band": data.get("exposure_band", "NONE"),
                    "hard_rules_evaluated": data.get("hard_rules_evaluated", []),
                    "hard_rules_fired": data.get("hard_rules_fired", []),
                    "hard_rule_override": data.get("hard_rule_override", False),
                    "cumulative_sensitivity_at_time": data.get(
                        "cumulative_sensitivity_at_time", 0.0
                    ),
                    "context_elevation_applied": data.get(
                        "context_elevation_applied", False
                    ),
                    "context_elevation_reason": data.get(
                        "context_elevation_reason", None
                    ),
                    "matrix_result": data.get("matrix_result", "RED"),
                    "final_lane": data.get("final_lane", "RED"),
                    "decision_reason": data.get("decision_reason", ""),
                    "frontier_payload_id": data.get("frontier_payload_id", None),
                    "payload_approved": data.get("payload_approved", None),
                    "approval_actor": data.get("approval_actor", None),
                    "approval_timestamp": data.get("approval_timestamp", None),
                    "approval_modifications": data.get("approval_modifications", None),
                    "previous_record_hash": data.get("previous_record_hash", ""),
                }
                serialized = json.dumps(hash_input, sort_keys=True, default=str)
                computed_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

                if computed_hash != stored_hash:
                    return (
                        False,
                        f"Chain broken at record {record_id}: stored hash does not "
                        f"match recomputed hash (tampering detected).",
                    )

                # Check linkage to previous record.
                if i > 0:
                    expected_prev = rows[i - 1][1]  # record_hash of prior row
                    if prev_hash != expected_prev:
                        return (
                            False,
                            f"Chain broken at record {record_id}: "
                            f"previous_record_hash ({prev_hash!r}) does not match "
                            f"prior record's hash ({expected_prev!r}).",
                        )

                verified += 1

            return True, f"Chain valid: {verified} record(s) verified."

        except Exception as exc:
            logger.error("RecordStore.verify_chain failed: %s", exc, exc_info=True)
            return False, f"Chain verification error: {exc}"
