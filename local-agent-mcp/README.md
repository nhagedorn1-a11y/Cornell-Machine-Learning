# Local Agent MCP Framework

A fully local, privacy-first AI agent that integrates **Anthropic MCP** (Model Context Protocol) for tool orchestration with a **local LLM** (Nemotron Nano 30B via LM Studio) for inference. One chat box, grounded answers with citations, zero cloud API calls at runtime.

## Architecture

```
 User Prompt
      |
      v
 +-------------+       stdio        +--------------+
 | Orchestrator | <================> | MCP-Web      |
 | (MCP Client) |      stdio        | Server       |
 |              | <================> +--------------+
 |              |                    | MCP-RAG      |
 |              |                    | Server       |
 +--------------+                    +--------------+
      |
      | HTTP (OpenAI-compatible)
      v
 +-------------+
 | LM Studio   |
 | Nemotron    |
 | 30B         |
 +-------------+
```

**Flow:** Prompt → intent detection → MCP tools (search/fetch/chunk/embed/query) → context pack with [S#] citations → LLM call → response with sources.

## Prerequisites

- **Python 3.11+**
- **LM Studio** with Nemotron Nano 30B (or any model) loaded and server running
- **Git** (to clone this repo)
- **(Optional)** Docker & Docker Compose for SearXNG

## Quick Start

### 1. Clone and Install

```bash
cd local-agent-mcp
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.json config.json
# Edit config.json:
#   - Set lmstudio.model to match your loaded model name
#   - Set searxng.enabled to true if using SearXNG
```

### 3. Start LM Studio Server

1. Open LM Studio
2. Load **Nemotron Nano 30B** (or your chosen model)
3. Go to **Local Server** tab
4. Click **Start Server** (defaults to `http://localhost:1234`)

### 4. (Optional) Start SearXNG

```bash
docker-compose up -d
# Wait ~30 seconds for startup
# SearXNG will be at http://localhost:8080
# Set "searxng": {"enabled": true} in config.json
```

### 5. Run the App

```bash
# From the local-agent-mcp directory:
cd local-agent-mcp
python -m app.main
```

Open **http://localhost:8000** in your browser.

## How It Works

### Intent Detection

The orchestrator routes prompts automatically:

| Input pattern | Action |
|---|---|
| Contains URLs (`https://...`) | Fetch → extract → chunk → embed → store → query |
| Contains trigger words ("latest", "what's new", "today") | SearXNG search → fetch top results → ingest → query |
| Plain question | Query existing FAISS index → answer with evidence or from knowledge |

### MCP Servers

#### mcp-web (6 tools)
| Tool | Description |
|---|---|
| `web_search` | Search via local SearXNG instance |
| `fetch_url` | Fetch a web page (with disk cache) |
| `extract_text` | Extract readable text from HTML |
| `chunk_text` | Split text into overlapping chunks for embedding |
| `clear_cache` | Remove all cached pages |
| `cache_status` | Check if a URL is cached |

#### mcp-rag (4 tools)
| Tool | Description |
|---|---|
| `rag_upsert` | Embed and store text chunks in FAISS |
| `rag_query` | Semantic search over stored chunks |
| `rag_count` | Count stored chunks |
| `rag_clear` | Reset the entire index |

### Citation Policy

When evidence is available:
- Every claim is cited with `[S#]` markers
- Sources list is included in response JSON
- The LLM is instructed to answer **only** from evidence

When no evidence exists:
- The LLM answers from training knowledge
- Explicitly states it cannot confirm real-time information

### Caching & Persistence

- **Web cache:** Fetched pages stored on disk by URL hash (`data/cache/`)
- **FAISS index:** Persisted to disk (`data/faiss/index.bin`)
- **Metadata:** JSONL sidecar (`data/faiss/metadata.jsonl`)

## API Reference

### POST /chat

```json
{
  "prompt": "What is the latest news about LLMs?",
  "debug": true
}
```

Response:
```json
{
  "reply": "According to [S1], recent developments include...",
  "sources": [
    {"id": "[S1]", "url": "https://...", "title": "..."}
  ],
  "debug": [
    {"tool": "web_search", "args": {"query": "..."}},
    {"tool": "rag_query", "args": {"query": "...", "top_k": 5}}
  ]
}
```

### GET /health

Returns system status for LM Studio, MCP-Web, and MCP-RAG.

## Smoke Tests

```bash
# From local-agent-mcp directory:

# Test LM Studio connectivity
python tests/test_lmstudio.py

# Test MCP tool calls
python tests/test_mcp_tools.py

# End-to-end test
python tests/test_e2e.py
```

## Project Structure

```
local-agent-mcp/
  README.md
  requirements.txt
  config.example.json
  config.json               (your config - gitignored)
  docker-compose.yml        (optional SearXNG)
  app/
    main.py                 (FastAPI + UI + /chat endpoint)
    orchestrator.py          (MCP client + routing + LM Studio calls)
    lmstudio_client.py       (OpenAI-compatible client)
    prompts.py               (system prompts + citation policy)
  mcp_servers/
    web_server/
      server.py              (MCP server exposing web tools)
      tools.py               (search, fetch, extract, chunk)
      cache.py               (disk cache by URL hash)
    rag_server/
      server.py              (MCP server exposing RAG tools)
      embeddings.py           (sentence-transformers embeddings)
      faiss_store.py           (FAISS index + metadata persistence)
      models.py               (Pydantic data models)
  ui/
    templates/index.html     (single chat box UI)
  tests/
    test_lmstudio.py
    test_mcp_tools.py
    test_e2e.py
  data/                      (auto-created at runtime)
    cache/
    faiss/
```

## Configuration Reference

| Key | Default | Description |
|---|---|---|
| `lmstudio.base_url` | `http://localhost:1234/v1` | LM Studio API endpoint |
| `lmstudio.model` | `nemotron-nano-30b` | Model name in LM Studio |
| `lmstudio.max_tokens` | `2048` | Max generation tokens |
| `lmstudio.temperature` | `0.3` | Sampling temperature |
| `lmstudio.timeout_seconds` | `120` | Request timeout |
| `searxng.base_url` | `http://localhost:8080` | SearXNG endpoint |
| `searxng.enabled` | `false` | Enable web search |
| `searxng.max_results` | `5` | Results per search |
| `faiss.top_k` | `5` | RAG retrieval count |
| `cache.max_age_hours` | `24` | Page cache TTL |

## Troubleshooting

**LM Studio not connecting**
- Ensure the server is started in LM Studio's Local Server tab
- Check the port matches `lmstudio.base_url` in config.json
- Run `python tests/test_lmstudio.py` to diagnose

**MCP servers failing**
- Run `python mcp_servers/web_server/server.py` directly to check for import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`

**SearXNG not returning results**
- Check `docker-compose logs searxng` for errors
- Ensure `searxng.enabled` is `true` in config.json
- SearXNG needs ~30s to start after `docker-compose up`

**FAISS index issues**
- Delete `data/faiss/` directory to reset the index
- The index is auto-created on first use

## License

MIT
