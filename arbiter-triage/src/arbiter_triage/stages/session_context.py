"""Stage 6: Session context accumulation for the Arbiter Triage Engine.

Tracks cumulative sensitivity across multi-turn conversations and
applies context-based lane elevation rules.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from arbiter_triage.models import SessionContext, StageResult


class SessionContextManager:
    """Manages session state, decay-weighted sensitivity, and elevation logic.

    Parameters
    ----------
    default_decay:
        Exponential decay factor applied to cumulative sensitivity each turn.
    timeout_minutes:
        Minutes of inactivity after which a session is considered expired.
    """

    MAX_ACTIVE_SESSIONS: int = 200

    def __init__(
        self,
        default_decay: float = 0.85,
        timeout_minutes: int = 30,
    ) -> None:
        self._sessions: dict[str, SessionContext] = {}
        self._default_decay = default_decay
        self._timeout_minutes = timeout_minutes

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def get_or_create_session(
        self, session_id: str, user_id: str
    ) -> SessionContext:
        """Return an existing session or create a new one."""
        if session_id in self._sessions:
            return self._sessions[session_id]

        session = SessionContext(
            session_id=session_id,
            user_id=user_id,
            decay_factor=self._default_decay,
        )
        self._sessions[session_id] = session
        self._enforce_lru_limit()
        return session

    async def update_session(
        self,
        session_id: str,
        sensitivity_score: float,
        entities: list[str],
        data_sources: list[str],
        lane: str,
    ) -> SessionContext:
        """Update session state after a query has been triaged.

        Applies the decay formula:
            cumulative(t) = cumulative(t-1) * decay + current * (1 - decay)
        """
        session = self._sessions[session_id]

        # Decay-weighted cumulative sensitivity
        decay = session.decay_factor
        session.cumulative_sensitivity = (
            session.cumulative_sensitivity * decay
            + sensitivity_score * (1 - decay)
        )

        # Track peak
        if session.cumulative_sensitivity > session.peak_sensitivity:
            session.peak_sensitivity = session.cumulative_sensitivity

        # Entity registry
        session.entity_registry.update(entities)

        # Data sources
        for src in data_sources:
            if src not in session.data_sources_accessed:
                session.data_sources_accessed.append(src)

        # Lane history & bookkeeping
        session.lane_history.append(lane)
        session.query_count += 1
        session.last_activity = datetime.now(timezone.utc)

        return session

    # ------------------------------------------------------------------
    # Elevation logic
    # ------------------------------------------------------------------

    async def evaluate_elevation(
        self, session_id: str, current_lane: str
    ) -> StageResult:
        """Determine whether context warrants elevating the current lane.

        Elevation rules (evaluated in priority order):
        1. cumulative > 90 AND current == GREEN  -> RED
        2. cumulative > 80 AND current == AMBER  -> RED
        3. cumulative > 60 AND current == GREEN  -> AMBER
        """
        session = self._sessions[session_id]
        cumulative = session.cumulative_sensitivity

        elevated = False
        elevated_lane = current_lane
        reason: str | None = None

        if cumulative > 90 and current_lane == "GREEN":
            elevated = True
            elevated_lane = "RED"
            reason = (
                f"Cumulative sensitivity {cumulative:.1f} > 90 "
                "with current lane GREEN; elevated directly to RED"
            )
        elif cumulative > 80 and current_lane == "AMBER":
            elevated = True
            elevated_lane = "RED"
            reason = (
                f"Cumulative sensitivity {cumulative:.1f} > 80 "
                "with current lane AMBER; elevated to RED"
            )
        elif cumulative > 60 and current_lane == "GREEN":
            elevated = True
            elevated_lane = "AMBER"
            reason = (
                f"Cumulative sensitivity {cumulative:.1f} > 60 "
                "with current lane GREEN; elevated to AMBER"
            )

        return StageResult(
            stage_name="session_context",
            data={
                "context_elevated": elevated,
                "elevated_lane": elevated_lane,
                "elevation_reason": reason,
                "cumulative_sensitivity": cumulative,
            },
        )

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    async def cleanup_expired(self) -> None:
        """Remove sessions that have been inactive beyond the timeout."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=self._timeout_minutes
        )
        expired = [
            sid
            for sid, ctx in self._sessions.items()
            if ctx.last_activity < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]

    def _enforce_lru_limit(self) -> None:
        """Evict the oldest sessions (by last_activity) when over capacity."""
        while len(self._sessions) > self.MAX_ACTIVE_SESSIONS:
            oldest_id = min(
                self._sessions,
                key=lambda sid: self._sessions[sid].last_activity,
            )
            del self._sessions[oldest_id]
