"""Pydantic models for RAG server data structures."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChunkInput(BaseModel):
    """A single chunk to be upserted into the FAISS index."""
    chunk_id: str
    text: str
    url: str = ""
    title: str = ""


class UpsertRequest(BaseModel):
    """Request to upsert one or more chunks."""
    chunks: list[ChunkInput]


class QueryRequest(BaseModel):
    """Request to query the FAISS index."""
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


class Evidence(BaseModel):
    """A single piece of retrieved evidence."""
    chunk_id: str
    text: str
    url: str = ""
    title: str = ""
    score: float = 0.0


class QueryResult(BaseModel):
    """Result of a FAISS query."""
    query: str
    results: list[Evidence]
