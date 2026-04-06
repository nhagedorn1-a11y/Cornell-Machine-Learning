"""OpenTelemetry instrumentation for pipeline stage tracing."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger("arbiter_triage.telemetry")

# Try to import OpenTelemetry; all operations are no-ops if unavailable
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.info("OpenTelemetry not available; telemetry disabled")


class TracingManager:
    """Manages OpenTelemetry tracing for the triage engine."""

    def __init__(self, service_name: str = "arbiter-triage"):
        self.service_name = service_name
        self._tracer = None
        self._provider = None
        self._initialized = False

    async def initialize(self) -> None:
        if not OTEL_AVAILABLE:
            logger.info("Telemetry init skipped: OpenTelemetry not installed")
            return
        try:
            resource = Resource.create({"service.name": self.service_name})
            self._provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self._provider)
            self._tracer = trace.get_tracer(self.service_name)
            self._initialized = True
            logger.info("OpenTelemetry initialized for %s", self.service_name)
        except Exception:
            logger.exception("Failed to initialize OpenTelemetry")

    def start_span(self, name: str, attributes: dict[str, Any] | None = None):
        if not self._initialized or not self._tracer:
            return None
        try:
            span = self._tracer.start_span(name)
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v))
            return span
        except Exception:
            return None

    def end_span(self, span: Any, status: str = "OK") -> None:
        if span is None:
            return
        try:
            if status != "OK" and OTEL_AVAILABLE:
                span.set_status(trace.StatusCode.ERROR, status)
            span.end()
        except Exception:
            pass

    @contextmanager
    def trace_stage(self, stage_name: str) -> Generator[dict[str, float], None, None]:
        """Context manager that traces a pipeline stage and records elapsed time."""
        timing: dict[str, float] = {"elapsed_ms": 0.0}
        span = self.start_span(f"triage.{stage_name}")
        start = time.perf_counter()
        try:
            yield timing
        except Exception as exc:
            self.end_span(span, status=str(exc))
            raise
        finally:
            timing["elapsed_ms"] = (time.perf_counter() - start) * 1000
            self.end_span(span)

    async def shutdown(self) -> None:
        if self._provider and hasattr(self._provider, "shutdown"):
            try:
                self._provider.shutdown()
            except Exception:
                pass
