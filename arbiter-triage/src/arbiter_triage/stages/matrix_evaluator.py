"""Stage 7 -- Matrix Evaluator: map dual scores to GREEN/AMBER/RED lane.

Budget targets:
    target   1 ms
    hard     5 ms
"""

from __future__ import annotations

import time

from arbiter_triage.models import StageResult

# ---------------------------------------------------------------------------
# Band definitions
# ---------------------------------------------------------------------------

SENSITIVITY_BANDS: dict[str, tuple[int, int]] = {
    'NONE':     (0,   20),
    'LOW':      (21,  40),
    'MEDIUM':   (41,  60),
    'HIGH':     (61,  80),
    'CRITICAL': (81, 100),
}

EXPOSURE_BANDS: dict[str, tuple[int, int]] = {
    'NONE':        (0,   20),
    'MINIMAL':     (21,  40),
    'MODERATE':    (41,  60),
    'SIGNIFICANT': (61,  80),
    'ESSENTIAL':   (81, 100),
}

# ---------------------------------------------------------------------------
# 5x5 decision matrix
# ---------------------------------------------------------------------------

DECISION_MATRIX: dict[tuple[str, str], str] = {
    ('NONE',     'NONE'):        'GREEN',
    ('NONE',     'MINIMAL'):     'GREEN',
    ('NONE',     'MODERATE'):    'GREEN',
    ('NONE',     'SIGNIFICANT'): 'GREEN',
    ('NONE',     'ESSENTIAL'):   'GREEN',
    ('LOW',      'NONE'):        'GREEN',
    ('LOW',      'MINIMAL'):     'GREEN',
    ('LOW',      'MODERATE'):    'GREEN',
    ('LOW',      'SIGNIFICANT'): 'AMBER',
    ('LOW',      'ESSENTIAL'):   'AMBER',
    ('MEDIUM',   'NONE'):        'GREEN',
    ('MEDIUM',   'MINIMAL'):     'GREEN',
    ('MEDIUM',   'MODERATE'):    'AMBER',
    ('MEDIUM',   'SIGNIFICANT'): 'AMBER',
    ('MEDIUM',   'ESSENTIAL'):   'RED',
    ('HIGH',     'NONE'):        'GREEN',
    ('HIGH',     'MINIMAL'):     'AMBER',
    ('HIGH',     'MODERATE'):    'AMBER',
    ('HIGH',     'SIGNIFICANT'): 'RED',
    ('HIGH',     'ESSENTIAL'):   'RED',
    ('CRITICAL', 'NONE'):        'GREEN',
    ('CRITICAL', 'MINIMAL'):     'AMBER',
    ('CRITICAL', 'MODERATE'):    'RED',
    ('CRITICAL', 'SIGNIFICANT'): 'RED',
    ('CRITICAL', 'ESSENTIAL'):   'RED',
}

_HARD_LIMIT_MS = 5.0


# ---------------------------------------------------------------------------
# Band lookup helpers
# ---------------------------------------------------------------------------

def get_sensitivity_band(score: float) -> str:
    """Map a sensitivity score (0-100) to its band name."""
    clamped = max(0.0, min(100.0, score))
    for band_name, (low, high) in SENSITIVITY_BANDS.items():
        if low <= clamped <= high:
            return band_name
    # Fallback — should not be reached with valid input
    return 'CRITICAL'


def get_exposure_band(score: float) -> str:
    """Map an exposure score (0-100) to its band name."""
    clamped = max(0.0, min(100.0, score))
    for band_name, (low, high) in EXPOSURE_BANDS.items():
        if low <= clamped <= high:
            return band_name
    # Fallback — should not be reached with valid input
    return 'ESSENTIAL'


# ---------------------------------------------------------------------------
# Main stage entry point
# ---------------------------------------------------------------------------

async def evaluate_matrix(
    sensitivity_score: float,
    exposure_score: float,
) -> StageResult:
    """Look up the decision matrix and return the triage lane.

    Returns a :class:`StageResult` with ``stage_name="matrix_evaluator"``
    whose ``data`` dict contains:

    * ``lane``             -- str  (GREEN | AMBER | RED)
    * ``sensitivity_band`` -- str
    * ``exposure_band``    -- str
    """
    start = time.perf_counter()
    try:
        sensitivity_band = get_sensitivity_band(sensitivity_score)
        exposure_band = get_exposure_band(exposure_score)

        lane = DECISION_MATRIX.get(
            (sensitivity_band, exposure_band),
            'RED',  # default-safe: unknown combos go RED
        )

        elapsed_ms = (time.perf_counter() - start) * 1_000

        return StageResult(
            stage_name="matrix_evaluator",
            data={
                "lane": lane,
                "sensitivity_band": sensitivity_band,
                "exposure_band": exposure_band,
            },
            elapsed_ms=round(elapsed_ms, 3),
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1_000
        return StageResult(
            stage_name="matrix_evaluator",
            data={
                "lane": "RED",
                "sensitivity_band": "CRITICAL",
                "exposure_band": "ESSENTIAL",
            },
            elapsed_ms=round(elapsed_ms, 3),
            error=f"matrix_evaluator failed: {exc}",
        )
