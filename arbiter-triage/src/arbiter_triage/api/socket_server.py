"""Unix domain socket server for the Arbiter Triage Engine.

Exposes a JSON-over-Unix-socket API at /var/run/arbiter/triage.sock.
No HTTP, no gRPC, no external network exposure.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

from arbiter_triage.models import DataContext, TriageRequest, TriageResponse, ErrorResponse
from arbiter_triage.pipeline import TriagePipeline
from arbiter_triage.storage.record_store import RecordStore
from arbiter_triage.storage.session_store import SessionStore
from arbiter_triage.stages.session_context import SessionContextManager
from arbiter_triage.telemetry.otel import TracingManager

logger = logging.getLogger("arbiter_triage.api")

DEFAULT_SOCKET_PATH = "/var/run/arbiter/triage.sock"
DEFAULT_RECORD_DB = "/var/lib/arbiter/triage/records.db"
DEFAULT_SESSION_DB = "/var/lib/arbiter/triage/sessions.db"


class TriageServer:
    """Async Unix domain socket server for triage requests."""

    def __init__(
        self,
        socket_path: str = DEFAULT_SOCKET_PATH,
        record_db_path: str = DEFAULT_RECORD_DB,
        session_db_path: str = DEFAULT_SESSION_DB,
        max_concurrent: int = 50,
    ):
        self.socket_path = socket_path
        self.record_db_path = record_db_path
        self.session_db_path = session_db_path
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._server: asyncio.Server | None = None
        self._pipeline: TriagePipeline | None = None
        self._tracing = TracingManager()
        self._running = False
        self._request_count = 0

    async def initialize(self) -> None:
        """Initialize all subsystems."""
        logger.info("Initializing triage server...")

        # Initialize storage
        record_store = RecordStore(db_path=self.record_db_path)
        session_store = SessionStore(db_path=self.session_db_path)
        session_manager = SessionContextManager()

        # Initialize pipeline
        self._pipeline = TriagePipeline(
            record_store=record_store,
            session_store=session_store,
            session_manager=session_manager,
        )
        await self._pipeline.initialize()

        # Initialize telemetry
        await self._tracing.initialize()

        logger.info("Triage server initialized successfully")

    async def start(self) -> None:
        """Start listening on the Unix domain socket."""
        # Ensure socket directory exists
        socket_dir = os.path.dirname(self.socket_path)
        os.makedirs(socket_dir, exist_ok=True)

        # Remove stale socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        self._server = await asyncio.start_unix_server(
            self._handle_client, path=self.socket_path,
        )
        # Set socket permissions (owner + group read/write)
        os.chmod(self.socket_path, 0o660)

        self._running = True
        logger.info("Triage server listening on %s", self.socket_path)

        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        """Handle a single client connection."""
        try:
            data = await asyncio.wait_for(reader.read(1_048_576), timeout=10.0)  # 1MB max
            if not data:
                return

            request_json = json.loads(data.decode("utf-8"))
            response = await self._process_request(request_json)

            response_bytes = json.dumps(response, default=str).encode("utf-8")
            writer.write(response_bytes)
            await writer.drain()
        except asyncio.TimeoutError:
            error = {"error": True, "error_code": "TIMEOUT", "lane": "RED", "message": "Request read timeout"}
            writer.write(json.dumps(error).encode("utf-8"))
            await writer.drain()
        except json.JSONDecodeError as exc:
            error = {"error": True, "error_code": "INTERNAL", "lane": "RED", "message": f"Invalid JSON: {exc}"}
            writer.write(json.dumps(error).encode("utf-8"))
            await writer.drain()
        except Exception:
            logger.exception("Unhandled error in client handler")
            error = {"error": True, "error_code": "INTERNAL", "lane": "RED", "message": "Internal server error"}
            writer.write(json.dumps(error).encode("utf-8"))
            await writer.drain()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def _process_request(self, request_json: dict) -> dict:
        """Parse and process a triage request."""
        async with self._semaphore:
            self._request_count += 1

            # Parse request
            data_ctx = request_json.get("data_context", {})
            request = TriageRequest(
                request_id=request_json.get("request_id", ""),
                session_id=request_json.get("session_id", ""),
                user_id=request_json.get("user_id", ""),
                query=request_json.get("query", ""),
                data_context=DataContext(
                    sources_referenced=data_ctx.get("sources_referenced", []),
                    schema_hints=data_ctx.get("schema_hints", {}),
                ),
                vertical_pack=request_json.get("vertical_pack", "GENERIC"),
                air_gap_mode=request_json.get("air_gap_mode", False),
            )

            if not request.query:
                return {
                    "error": True,
                    "error_code": "INTERNAL",
                    "lane": "RED",
                    "request_id": request.request_id,
                    "message": "Empty query",
                }

            # Process through pipeline
            result = await self._pipeline.process(request)

            # Serialize response
            if isinstance(result, ErrorResponse):
                return {
                    "request_id": result.request_id,
                    "error": True,
                    "error_code": result.error_code,
                    "error_stage": result.error_stage,
                    "lane": result.lane,
                    "record_id": result.record_id,
                    "message": result.message,
                }

            return {
                "request_id": result.request_id,
                "record_id": result.record_id,
                "session_id": result.session_id,
                "lane": result.lane,
                "sensitivity_score": result.sensitivity_score,
                "exposure_score": result.exposure_score,
                "sensitivity_band": result.sensitivity_band,
                "exposure_band": result.exposure_band,
                "decision_reason": result.decision_reason,
                "hard_rule_fired": result.hard_rule_fired,
                "hard_rule_id": result.hard_rule_id,
                "context_elevated": result.context_elevated,
                "frontier_payload": result.frontier_payload,
                "processing_time_ms": result.processing_time_ms,
                "stage_times_ms": result.stage_times_ms,
                "degraded_mode": result.degraded_mode,
                "degraded_reason": result.degraded_reason,
            }

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down triage server...")
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if self._pipeline:
            await self._pipeline.shutdown()
        await self._tracing.shutdown()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        logger.info("Triage server stopped")

    @property
    def request_count(self) -> int:
        return self._request_count


def main():
    """Entry point for the triage service."""
    import uvloop
    uvloop.install()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    server = TriageServer()
    loop = asyncio.new_event_loop()

    def _signal_handler():
        loop.create_task(server.shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    try:
        loop.run_until_complete(server.initialize())
        loop.run_until_complete(server.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(server.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
