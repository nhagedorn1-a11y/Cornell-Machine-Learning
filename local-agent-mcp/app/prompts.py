"""System prompts and citation policy templates for the orchestrator."""

from __future__ import annotations

SYSTEM_WITH_EVIDENCE = """\
You are a helpful research assistant. You have been provided with EVIDENCE \
retrieved from web sources. Follow these rules strictly:

1. Answer the user's question using ONLY the evidence provided below.
2. Cite every major claim with [S#] references corresponding to the source numbers.
3. If the evidence does not contain enough information to fully answer, say so explicitly \
   and indicate which parts you cannot confirm.
4. Do NOT fabricate information or pretend you browsed the web yourself.
5. Be concise, accurate, and well-structured.

EVIDENCE:
{evidence_block}

SOURCES:
{sources_block}
"""

SYSTEM_NO_EVIDENCE = """\
You are a helpful assistant. You do NOT have access to the internet or any \
retrieved documents in this turn. Follow these rules strictly:

1. Answer from your training knowledge only.
2. If the question asks about recent events, breaking news, or real-time data, \
   clearly state that you cannot confirm this information without web retrieval.
3. Never pretend that you browsed the web or retrieved documents.
4. Be concise and honest about the limits of your knowledge.
"""

SYSTEM_INGEST_CONFIRM = """\
You are a helpful assistant. The user provided URLs that have been fetched and \
ingested into the local knowledge base. Summarize what was ingested and let the \
user know they can now ask questions about the content.

INGESTED DOCUMENTS:
{ingest_summary}
"""


def build_evidence_prompt(evidence_items: list[dict]) -> tuple[str, str]:
    """Build the evidence and sources blocks for the system prompt.

    Args:
        evidence_items: List of dicts with keys: text, url, title, score, chunk_id

    Returns:
        Tuple of (formatted system prompt, sources JSON string for response).
    """
    if not evidence_items:
        return SYSTEM_NO_EVIDENCE, "[]"

    evidence_lines: list[str] = []
    sources: list[dict] = []
    seen_urls: set[str] = set()

    for i, item in enumerate(evidence_items, 1):
        tag = f"[S{i}]"
        evidence_lines.append(f"{tag} {item.get('text', '')}")

        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({
                "id": tag,
                "url": url,
                "title": item.get("title", ""),
            })

    evidence_block = "\n\n".join(evidence_lines)
    sources_block = "\n".join(
        f"{s['id']} — {s['title'] or s['url']} ({s['url']})" for s in sources
    )

    system = SYSTEM_WITH_EVIDENCE.format(
        evidence_block=evidence_block,
        sources_block=sources_block,
    )

    import json
    return system, json.dumps(sources, ensure_ascii=False)
