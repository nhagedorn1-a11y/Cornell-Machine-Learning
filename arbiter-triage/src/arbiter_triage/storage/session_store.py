"""Async session persistence for the Arbiter Triage Engine.

Stores and retrieves SessionContext objects using aiosqlite.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from arbiter_triage.models import SessionContext

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = "/var/lib/arbiter/triage/sessions.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id     TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    data           TEXT NOT NULL,
    opened_at      TEXT NOT NULL,
    last_activity  TEXT NOT NULL
);
"""


def _session_to_row(session: SessionContext) -> tuple[str, str, str, str, str]:
    """Serialize a SessionContext into a database row tuple."""
    data = {
        "query_count": session.query_count,
        "cumulative_sensitivity": session.cumulative_sensitivity,
        "entity_registry": sorted(session.entity_registry),
        "data_sources_accessed": session.data_sources_accessed,
        "peak_sensitivity": session.peak_sensitivity,
        "approved_payloads": session.approved_payloads,
        "lane_history": session.lane_history,
        "decay_factor": session.decay_factor,
    }
    return (
        session.session_id,
        session.user_id,
        json.dumps(data, default=str),
        session.opened_at.isoformat(),
        session.last_activity.isoformat(),
    )


def _row_to_session(row: aiosqlite.Row) -> SessionContext:
    """Deserialize a database row into a SessionContext."""
    session_id, user_id, data_json, opened_at, last_activity = row
    data: dict = json.loads(data_json)
    return SessionContext(
        session_id=session_id,
        user_id=user_id,
        opened_at=datetime.fromisoformat(opened_at),
        last_activity=datetime.fromisoformat(last_activity),
        query_count=data.get("query_count", 0),
        cumulative_sensitivity=data.get("cumulative_sensitivity", 0.0),
        entity_registry=set(data.get("entity_registry", [])),
        data_sources_accessed=data.get("data_sources_accessed", []),
        peak_sensitivity=data.get("peak_sensitivity", 0.0),
        approved_payloads=data.get("approved_payloads", []),
        lane_history=data.get("lane_history", []),
        decay_factor=data.get("decay_factor", 0.85),
    )


class SessionStore:
    """Async SQLite-backed session store.

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
        """Open the database connection and create the table if needed."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
            await self._db.execute(_CREATE_TABLE_SQL)
            await self._db.commit()
            logger.info("SessionStore initialized at %s", self.db_path)
        except Exception as exc:
            logger.error("SessionStore.initialize failed: %s", exc, exc_info=True)
            raise

    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self._db is not None:
                await self._db.close()
                self._db = None
        except Exception as exc:
            logger.error("SessionStore.close failed: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def save_session(self, session: SessionContext) -> None:
        """Insert or update (upsert) a session."""
        try:
            row = _session_to_row(session)
            assert self._db is not None, "SessionStore not initialized"
            await self._db.execute(
                """
                INSERT INTO sessions (session_id, user_id, data, opened_at, last_activity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id       = excluded.user_id,
                    data          = excluded.data,
                    opened_at     = excluded.opened_at,
                    last_activity = excluded.last_activity
                """,
                row,
            )
            await self._db.commit()
        except Exception as exc:
            logger.error("SessionStore.save_session failed: %s", exc, exc_info=True)
            raise

    async def load_session(self, session_id: str) -> SessionContext | None:
        """Load a session by its ID, or return ``None`` if not found."""
        try:
            assert self._db is not None, "SessionStore not initialized"
            cursor = await self._db.execute(
                "SELECT session_id, user_id, data, opened_at, last_activity "
                "FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_session(row)
        except Exception as exc:
            logger.error("SessionStore.load_session failed: %s", exc, exc_info=True)
            return None

    async def delete_session(self, session_id: str) -> None:
        """Delete a session by its ID."""
        try:
            assert self._db is not None, "SessionStore not initialized"
            await self._db.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            await self._db.commit()
        except Exception as exc:
            logger.error("SessionStore.delete_session failed: %s", exc, exc_info=True)
            raise

    async def list_expired(self, timeout_minutes: int) -> list[str]:
        """Return session_ids that have been inactive longer than *timeout_minutes*."""
        try:
            assert self._db is not None, "SessionStore not initialized"
            cutoff = datetime.now(timezone.utc).isoformat()
            cursor = await self._db.execute(
                """
                SELECT session_id FROM sessions
                WHERE julianday(?) - julianday(last_activity) > ? / 1440.0
                """,
                (cutoff, timeout_minutes),
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as exc:
            logger.error("SessionStore.list_expired failed: %s", exc, exc_info=True)
            return []
