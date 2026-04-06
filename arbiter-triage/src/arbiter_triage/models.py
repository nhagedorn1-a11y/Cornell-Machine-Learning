"""Core data models for the Arbiter Triage Engine."""

from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TriageRequest:
    """Incoming triage request from the ingress API."""
    request_id: str
    session_id: str
    user_id: str
    query: str
    data_context: DataContext
    vertical_pack: str = "GENERIC"  # FINANCE | LEGAL | HEALTHCARE | GENERIC
    air_gap_mode: bool = False


@dataclass
class DataContext:
    """Data context accompanying a triage request."""
    sources_referenced: list[str] = field(default_factory=list)
    schema_hints: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class SessionContext:
    """Stateful session tracking across multi-turn conversations."""
    session_id: str
    user_id: str
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    query_count: int = 0
    cumulative_sensitivity: float = 0.0
    entity_registry: set[str] = field(default_factory=set)
    data_sources_accessed: list[str] = field(default_factory=list)
    peak_sensitivity: float = 0.0
    approved_payloads: list[str] = field(default_factory=list)
    lane_history: list[str] = field(default_factory=list)
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decay_factor: float = 0.85


@dataclass
class FrontierPayload:
    """Sanitized payload for frontier model submission."""
    payload_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sanitized_content: str = ""
    redacted_fields: list[dict[str, str]] = field(default_factory=list)
    original_intent: str = ""
    sensitivity_after_sanitization: float = 0.0
    payload_hash: str = ""
    constructed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: str | None = None
    approved_at: datetime | None = None

    def compute_hash(self) -> str:
        self.payload_hash = hashlib.sha256(
            self.sanitized_content.encode("utf-8")
        ).hexdigest()
        return self.payload_hash


@dataclass
class StageResult:
    """Result from an individual pipeline stage."""
    stage_name: str
    data: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    error: str | None = None


@dataclass
class ScoringComponents:
    """Individual scoring sub-components."""
    components: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0


@dataclass
class TriageDecisionRecord:
    """Immutable decision record for audit trail."""
    # Identity
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    query_id: str = ""
    user_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Raw input (stored encrypted)
    query_hash: str = ""
    query_length_tokens: int = 0
    data_sources_referenced: list[str] = field(default_factory=list)

    # Stage outputs
    entities_detected: list[str] = field(default_factory=list)
    pii_types_detected: list[str] = field(default_factory=list)
    sensitivity_components: dict[str, float] = field(default_factory=dict)
    exposure_components: dict[str, float] = field(default_factory=dict)
    sensitivity_score: float = 0.0
    exposure_score: float = 0.0
    sensitivity_band: str = "NONE"
    exposure_band: str = "NONE"

    # Rule engine
    hard_rules_evaluated: list[str] = field(default_factory=list)
    hard_rules_fired: list[str] = field(default_factory=list)
    hard_rule_override: bool = False

    # Session context
    cumulative_sensitivity_at_time: float = 0.0
    context_elevation_applied: bool = False
    context_elevation_reason: str | None = None

    # Final decision
    matrix_result: str = "RED"
    final_lane: str = "RED"
    decision_reason: str = ""

    # Payload
    frontier_payload_id: str | None = None
    payload_approved: bool | None = None
    approval_actor: str | None = None
    approval_timestamp: datetime | None = None
    approval_modifications: str | None = None

    # Integrity
    record_hash: str = ""
    previous_record_hash: str = ""

    def compute_record_hash(self) -> str:
        """Compute SHA-256 hash of all record fields except record_hash itself."""
        hash_input = {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "query_id": self.query_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "query_hash": self.query_hash,
            "query_length_tokens": self.query_length_tokens,
            "data_sources_referenced": self.data_sources_referenced,
            "entities_detected": self.entities_detected,
            "pii_types_detected": self.pii_types_detected,
            "sensitivity_components": self.sensitivity_components,
            "exposure_components": self.exposure_components,
            "sensitivity_score": self.sensitivity_score,
            "exposure_score": self.exposure_score,
            "sensitivity_band": self.sensitivity_band,
            "exposure_band": self.exposure_band,
            "hard_rules_evaluated": self.hard_rules_evaluated,
            "hard_rules_fired": self.hard_rules_fired,
            "hard_rule_override": self.hard_rule_override,
            "cumulative_sensitivity_at_time": self.cumulative_sensitivity_at_time,
            "context_elevation_applied": self.context_elevation_applied,
            "context_elevation_reason": self.context_elevation_reason,
            "matrix_result": self.matrix_result,
            "final_lane": self.final_lane,
            "decision_reason": self.decision_reason,
            "frontier_payload_id": self.frontier_payload_id,
            "payload_approved": self.payload_approved,
            "approval_actor": self.approval_actor,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            "approval_modifications": self.approval_modifications,
            "previous_record_hash": self.previous_record_hash,
        }
        serialized = json.dumps(hash_input, sort_keys=True, default=str)
        self.record_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return self.record_hash


@dataclass
class TriageResponse:
    """Response returned from the triage engine."""
    request_id: str
    record_id: str
    session_id: str
    lane: str  # GREEN | AMBER | RED
    sensitivity_score: float
    exposure_score: float
    sensitivity_band: str
    exposure_band: str
    decision_reason: str
    hard_rule_fired: bool = False
    hard_rule_id: str | None = None
    context_elevated: bool = False
    frontier_payload: dict | None = None
    processing_time_ms: float = 0.0
    stage_times_ms: dict[str, float] = field(default_factory=dict)
    degraded_mode: bool = False
    degraded_reason: str | None = None


@dataclass
class ErrorResponse:
    """Error response — always assigns RED lane."""
    request_id: str
    error: bool = True
    error_code: str = "INTERNAL"  # STAGE_FAILURE | MODEL_UNAVAILABLE | TIMEOUT | INTERNAL
    error_stage: str = ""
    lane: str = "RED"
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: str = ""


# Lane ordering for elevation comparisons
LANE_ORDER = {"GREEN": 0, "AMBER": 1, "RED": 2}

def higher_lane(a: str, b: str) -> str:
    """Return the more restrictive lane."""
    return a if LANE_ORDER.get(a, 2) >= LANE_ORDER.get(b, 2) else b
