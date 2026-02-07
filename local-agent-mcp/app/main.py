#!/usr/bin/env python3
"""FastAPI application: single-page chat UI + /chat API endpoint."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .orchestrator import Orchestrator

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _PROJECT_ROOT / "config.json"
_CONFIG_EXAMPLE_PATH = _PROJECT_ROOT / "config.example.json"


def _load_config() -> dict[str, Any]:
    path = _CONFIG_PATH if _CONFIG_PATH.exists() else _CONFIG_EXAMPLE_PATH
    logger.info("Loading config from %s", path)
    with open(path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    # Resolve MCP server script paths relative to project root
    for key in ("web", "rag"):
        srv = cfg.get("mcp_servers", {}).get(key, {})
        if "args" in srv:
            srv["args"] = [str(_PROJECT_ROOT / a) for a in srv["args"]]
        # Use the current Python interpreter
        srv["command"] = sys.executable
    return cfg


config = _load_config()
orchestrator = Orchestrator(config)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Local Agent MCP", version="1.0.0")

# Templates
_TEMPLATE_DIR = _PROJECT_ROOT / "ui" / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    prompt: str
    debug: bool = False


class ChatResponse(BaseModel):
    reply: str
    sources: list[dict]
    debug: list[dict] | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    logger.info("Chat request: %.120s", req.prompt)
    result = await orchestrator.process(req.prompt)
    return ChatResponse(
        reply=result["reply"],
        sources=result["sources"],
        debug=result["debug"] if req.debug else None,
    )


@app.get("/health")
async def health() -> JSONResponse:
    status = await orchestrator.health()
    return JSONResponse(content=status)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def start() -> None:
    """Run with: python -m app.main"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    start()
