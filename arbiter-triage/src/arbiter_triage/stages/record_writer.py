"""Stage 9: Write immutable decision record for the Arbiter Triage Engine.

Persists the finalized TriageDecisionRecord to the record store,
computing its integrity hash before writing.

Budget: 10ms target, 30ms hard limit.
"""

from __future__ import annotations

import logging
import time

from arbiter_triage.models import StageResult, TriageDecisionRecord

logger = logging.getLogger(__name__)

STAGE_NAME = "record_writer"
TARGET_MS = 10.0
HARD_LIMIT_MS = 30.0


async def write_record(
    record: TriageDecisionRecord,
    record_store,
) -> StageResult:
    """Compute record hash, persist to the record store, and return a StageResult.

    Parameters
    ----------
    record:
        The fully-populated decision record to persist.
    record_store:
        An object exposing ``async write_record(record) -> str``.

    Returns
    -------
    StageResult
        Contains ``record_id`` and ``record_hash`` on success, or an
        ``error`` string on failure.  This function **never** raises.
    """
    start = time.perf_counter()
    try:
        # Compute the integrity hash over all record fields.
        record_hash = record.compute_record_hash()

        # Persist to the store (async) if available.
        if record_store is None:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return StageResult(
                stage_name="record_writer",
                data={"record_id": record.record_id, "record_hash": record_hash},
                elapsed_ms=elapsed_ms,
            )

        record_id = await record_store.write_record(record)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if elapsed_ms > HARD_LIMIT_MS:
            logger.warning(
                "record_writer exceeded hard limit: %.2f ms (limit %s ms)",
                elapsed_ms,
                HARD_LIMIT_MS,
            )
        elif elapsed_ms > TARGET_MS:
            logger.info(
                "record_writer exceeded target: %.2f ms (target %s ms)",
                elapsed_ms,
                TARGET_MS,
            )

        return StageResult(
            stage_name=STAGE_NAME,
            data={"record_id": record_id, "record_hash": record_hash},
            elapsed_ms=elapsed_ms,
        )

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.error("record_writer failed: %s", exc, exc_info=True)
        return StageResult(
            stage_name=STAGE_NAME,
            data={},
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )
