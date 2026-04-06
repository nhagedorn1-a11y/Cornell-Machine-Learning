"""Main inspection pipeline — orchestrates all 9 triage stages."""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from arbiter_triage.models import (
    DataContext,
    ErrorResponse,
    FrontierPayload,
    StageResult,
    TriageDecisionRecord,
    TriageRequest,
    TriageResponse,
    higher_lane,
)
from arbiter_triage.stages.tokenizer import tokenize
from arbiter_triage.stages.entity_extractor import extract_entities
from arbiter_triage.stages.sensitivity_scorer import score_sensitivity
from arbiter_triage.stages.exposure_scorer import score_exposure
from arbiter_triage.stages.rule_engine import evaluate_rules
from arbiter_triage.stages.session_context import SessionContextManager
from arbiter_triage.stages.matrix_evaluator import evaluate_matrix, get_sensitivity_band, get_exposure_band
from arbiter_triage.stages.payload_constructor import construct_payload
from arbiter_triage.stages.record_writer import write_record
from arbiter_triage.storage.record_store import RecordStore
from arbiter_triage.storage.session_store import SessionStore

logger = logging.getLogger("arbiter_triage.pipeline")


class TriagePipeline:
    """
    Stateful, real-time policy enforcement pipeline.

    Every query passes through 9 sequential inspection stages:
    1. Tokenization
    2. Entity Extraction
    3. Sensitivity Scoring
    4. Exposure Scoring
    5. Rule Engine
    6. Session Context
    7. Matrix Evaluation
    8. Payload Construction
    9. Decision Record
    """

    def __init__(
        self,
        record_store: RecordStore | None = None,
        session_store: SessionStore | None = None,
        session_manager: SessionContextManager | None = None,
        pre_approved_hashes: set[str] | None = None,
        customer_entity_registry: set[str] | None = None,
    ):
        self.record_store = record_store
        self.session_store = session_store
        self.session_manager = session_manager or SessionContextManager()
        self.pre_approved_hashes = pre_approved_hashes or set()
        self.customer_entity_registry = customer_entity_registry or set()
        self._initialized = False

    async def initialize(self):
        """Initialize storage backends."""
        if self.record_store:
            await self.record_store.initialize()
        if self.session_store:
            await self.session_store.initialize()
        self._initialized = True

    async def process(self, request: TriageRequest) -> TriageResponse | ErrorResponse:
        """
        Process a single triage request through all 9 stages.

        On any stage failure: classify as RED, log failure, continue to record.
        Never pass a query through uninspected.
        """
        pipeline_start = time.perf_counter()
        stage_times: dict[str, float] = {}
        query_id = str(uuid.uuid4())
        degraded_mode = False
        degraded_reason = None

        try:
            # ── Stage 1: Tokenization ──
            tok_result = await tokenize(request.query)
            stage_times["tokenization"] = tok_result.elapsed_ms
            if tok_result.error:
                return await self._fail(request, query_id, "tokenization", tok_result.error, stage_times, pipeline_start)

            tokens = tok_result.data["tokens"]
            token_count = tok_result.data["token_count"]
            numerical_token_count = tok_result.data["numerical_token_count"]
            numerical_ratio = tok_result.data["numerical_token_ratio"]

            # ── Stage 2: Entity Extraction ──
            ent_result = await extract_entities(
                tokens, request.query, request.vertical_pack,
                customer_entity_registry=self.customer_entity_registry,
            )
            stage_times["entity_extraction"] = ent_result.elapsed_ms
            if ent_result.error:
                return await self._fail(request, query_id, "entity_extraction", ent_result.error, stage_times, pipeline_start)

            entities = ent_result.data
            pii_types = entities.get("pii_types_detected", [])
            named_entities = entities.get("named_entities", [])
            data_source_refs = entities.get("data_source_references", [])

            # ── Stage 3: Sensitivity Scoring ──
            sens_result = await score_sensitivity(
                request.query, tokens, entities, numerical_ratio,
                request.vertical_pack,
            )
            stage_times["sensitivity_scoring"] = sens_result.elapsed_ms
            if sens_result.error:
                return await self._fail(request, query_id, "sensitivity_scoring", sens_result.error, stage_times, pipeline_start)

            sensitivity_score = sens_result.data["sensitivity_score"]
            sensitivity_components = sens_result.data.get("sensitivity_components", {})

            # ── Stage 4: Exposure Scoring ──
            exp_result = await score_exposure(
                request.query, tokens, token_count,
                air_gap_mode=request.air_gap_mode,
            )
            stage_times["exposure_scoring"] = exp_result.elapsed_ms
            if exp_result.error:
                return await self._fail(request, query_id, "exposure_scoring", exp_result.error, stage_times, pipeline_start)

            exposure_score = exp_result.data["exposure_score"]
            exposure_components = exp_result.data.get("exposure_components", {})

            # ── Stage 5: Rule Engine ──
            rule_result = await evaluate_rules(
                request.query, tokens, entities,
                numerical_token_count, named_entities, data_source_refs,
                token_count, pre_approved_hashes=self.pre_approved_hashes,
            )
            stage_times["rule_engine"] = rule_result.elapsed_ms
            if rule_result.error:
                return await self._fail(request, query_id, "rule_engine", rule_result.error, stage_times, pipeline_start)

            hard_rule_fired = rule_result.data.get("hard_rule_fired", False)
            lane_override = rule_result.data.get("lane_override")
            rule_type = rule_result.data.get("rule_type")
            rule_id = rule_result.data.get("rule_id")

            # ── Stage 6: Session Context ──
            session = await self.session_manager.get_or_create_session(
                request.session_id, request.user_id,
            )

            # Determine initial lane (from hard rule or matrix)
            if hard_rule_fired and lane_override:
                matrix_lane = lane_override
                sensitivity_band = get_sensitivity_band(sensitivity_score)
                exposure_band = get_exposure_band(exposure_score)
            else:
                # ── Stage 7: Matrix Evaluation ──
                mat_result = await evaluate_matrix(sensitivity_score, exposure_score)
                stage_times["matrix_evaluation"] = mat_result.elapsed_ms
                matrix_lane = mat_result.data["lane"]
                sensitivity_band = mat_result.data["sensitivity_band"]
                exposure_band = mat_result.data["exposure_band"]

            # Update session and evaluate context elevation
            # When a hard RED rule fires, treat as maximum sensitivity for session context
            effective_sensitivity = 100.0 if (hard_rule_fired and lane_override == "RED") else sensitivity_score
            await self.session_manager.update_session(
                request.session_id, effective_sensitivity,
                list(entities.get("named_entities", [])),
                request.data_context.sources_referenced if request.data_context else [],
                matrix_lane,
            )

            ctx_result = await self.session_manager.evaluate_elevation(
                request.session_id, matrix_lane,
            )
            stage_times["session_context"] = ctx_result.elapsed_ms

            context_elevated = ctx_result.data.get("context_elevated", False)
            elevated_lane = ctx_result.data.get("elevated_lane", matrix_lane)
            elevation_reason = ctx_result.data.get("elevation_reason")
            cumulative_sensitivity = ctx_result.data.get("cumulative_sensitivity", 0.0)

            # Final lane is the higher of matrix result and context-elevated result
            if hard_rule_fired and lane_override == "RED":
                final_lane = "RED"
            elif hard_rule_fired and lane_override == "GREEN":
                # GREEN hard rules can still be elevated by context
                final_lane = elevated_lane if context_elevated else "GREEN"
            else:
                final_lane = higher_lane(matrix_lane, elevated_lane) if context_elevated else matrix_lane

            if "matrix_evaluation" not in stage_times:
                stage_times["matrix_evaluation"] = 0.0

            # ── Stage 8: Payload Construction ──
            pay_result = await construct_payload(
                request.query, entities, pii_types, final_lane,
            )
            stage_times["payload_construction"] = pay_result.elapsed_ms

            payload_data = pay_result.data.get("payload")
            if pay_result.data.get("escalate_to_red"):
                final_lane = "RED"

            # ── Stage 9: Decision Record ──
            decision_reason = self._build_reason(
                final_lane, hard_rule_fired, rule_type, rule_id,
                context_elevated, elevation_reason,
                sensitivity_score, exposure_score,
                sensitivity_band, exposure_band,
            )

            record = TriageDecisionRecord(
                session_id=request.session_id,
                query_id=query_id,
                user_id=request.user_id,
                query_hash=hashlib.sha256(request.query.encode()).hexdigest(),
                query_length_tokens=token_count,
                data_sources_referenced=request.data_context.sources_referenced if request.data_context else [],
                entities_detected=[e.get("type", "") for e in entities.get("entities_detected", [])],
                pii_types_detected=pii_types,
                sensitivity_components=sensitivity_components,
                exposure_components=exposure_components,
                sensitivity_score=sensitivity_score,
                exposure_score=exposure_score,
                sensitivity_band=sensitivity_band,
                exposure_band=exposure_band,
                hard_rules_evaluated=rule_result.data.get("rules_evaluated", []),
                hard_rules_fired=rule_result.data.get("rules_fired", []),
                hard_rule_override=hard_rule_fired,
                cumulative_sensitivity_at_time=cumulative_sensitivity,
                context_elevation_applied=context_elevated,
                context_elevation_reason=elevation_reason,
                matrix_result=matrix_lane,
                final_lane=final_lane,
                decision_reason=decision_reason,
                frontier_payload_id=payload_data.get("payload_id") if payload_data else None,
            )

            # Chain to previous record
            if self.record_store:
                record.previous_record_hash = await self.record_store.get_last_record_hash()

            rec_result = await write_record(record, self.record_store)
            stage_times["record_write"] = rec_result.elapsed_ms

            total_ms = (time.perf_counter() - pipeline_start) * 1000
            if total_ms > 500:
                logger.critical("Pipeline latency CRITICAL: %.1fms", total_ms)
            elif total_ms > 435:
                logger.warning("Pipeline latency WARNING: %.1fms", total_ms)

            # Build frontier payload dict for response
            frontier_payload_resp = None
            if payload_data:
                frontier_payload_resp = {
                    "payload_id": payload_data.get("payload_id", ""),
                    "sanitized_content": payload_data.get("sanitized_content", ""),
                    "redacted_fields": payload_data.get("redacted_fields", []),
                    "original_intent": payload_data.get("original_intent", ""),
                    "sensitivity_after_sanitization": payload_data.get("sensitivity_after_sanitization", 0.0),
                    "payload_hash": payload_data.get("payload_hash", ""),
                }

            return TriageResponse(
                request_id=request.request_id,
                record_id=record.record_id,
                session_id=request.session_id,
                lane=final_lane,
                sensitivity_score=sensitivity_score,
                exposure_score=exposure_score,
                sensitivity_band=sensitivity_band,
                exposure_band=exposure_band,
                decision_reason=decision_reason,
                hard_rule_fired=hard_rule_fired,
                hard_rule_id=rule_id,
                context_elevated=context_elevated,
                frontier_payload=frontier_payload_resp,
                processing_time_ms=round(total_ms, 2),
                stage_times_ms=stage_times,
                degraded_mode=degraded_mode,
                degraded_reason=degraded_reason,
            )

        except Exception as exc:
            logger.exception("Unhandled pipeline error")
            return await self._fail(
                request, query_id, "pipeline",
                str(exc), stage_times, pipeline_start,
            )

    async def _fail(
        self, request: TriageRequest, query_id: str,
        stage: str, error_msg: str,
        stage_times: dict, pipeline_start: float,
    ) -> ErrorResponse:
        """Handle stage failure — always RED, always write a record."""
        logger.error("Stage failure in %s: %s", stage, error_msg)

        record = TriageDecisionRecord(
            session_id=request.session_id,
            query_id=query_id,
            user_id=request.user_id,
            query_hash=hashlib.sha256(request.query.encode()).hexdigest(),
            final_lane="RED",
            decision_reason=f"Stage failure in {stage}: {error_msg}",
        )
        if self.record_store:
            record.previous_record_hash = await self.record_store.get_last_record_hash()
        await write_record(record, self.record_store)

        return ErrorResponse(
            request_id=request.request_id,
            error_code="STAGE_FAILURE",
            error_stage=stage,
            record_id=record.record_id,
            message=f"Stage failure in {stage}: {error_msg}",
        )

    def _build_reason(
        self, lane, hard_rule_fired, rule_type, rule_id,
        context_elevated, elevation_reason,
        sens_score, exp_score, sens_band, exp_band,
    ) -> str:
        parts = []
        if hard_rule_fired:
            parts.append(f"Hard rule {rule_type} fired (rule: {rule_id})")
        parts.append(f"Sensitivity: {sens_score:.1f} ({sens_band}), Exposure: {exp_score:.1f} ({exp_band})")
        if context_elevated:
            parts.append(f"Context elevated: {elevation_reason}")
        parts.append(f"Final lane: {lane}")
        return "; ".join(parts)


    async def shutdown(self):
        """Graceful shutdown."""
        if self.record_store:
            await self.record_store.close()
        if self.session_store:
            await self.session_store.close()
