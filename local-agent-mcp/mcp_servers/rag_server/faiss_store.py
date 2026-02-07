"""Persistent FAISS index with JSONL metadata sidecar."""

from __future__ import annotations

import json
import pathlib
import threading
from typing import Optional

import faiss
import numpy as np

from .embeddings import embed_texts, embed_query, get_dimension

_lock = threading.Lock()


class FaissStore:
    """Thread-safe FAISS flat-L2 index with metadata persistence."""

    def __init__(
        self,
        index_path: str = "data/faiss/index.bin",
        metadata_path: str = "data/faiss/metadata.jsonl",
        dimension: int | None = None,
    ) -> None:
        self.index_path = pathlib.Path(index_path)
        self.metadata_path = pathlib.Path(metadata_path)
        self.dimension = dimension or get_dimension()

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

        self.metadata: list[dict] = []
        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        self.metadata.append(json.loads(line))

    def _save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "w", encoding="utf-8") as fh:
            for m in self.metadata:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    def upsert(self, chunks: list[dict]) -> dict:
        """Add chunks to the index. Each chunk must have 'chunk_id' and 'text'.
        Optional fields: url, title.

        Returns {added: int, total: int}.
        """
        if not chunks:
            return {"added": 0, "total": self.index.ntotal}

        texts = [c["text"] for c in chunks]
        vectors = embed_texts(texts)

        with _lock:
            self.index.add(vectors)
            for c in chunks:
                self.metadata.append({
                    "chunk_id": c.get("chunk_id", ""),
                    "text": c["text"],
                    "url": c.get("url", ""),
                    "title": c.get("title", ""),
                })
            self._save()

        return {"added": len(chunks), "total": self.index.ntotal}

    def query(self, query_text: str, top_k: int = 5) -> list[dict]:
        """Retrieve the top-k most similar chunks for *query_text*.

        Returns list of {chunk_id, text, url, title, score}.
        """
        if self.index.ntotal == 0:
            return []

        vec = embed_query(query_text)
        k = min(top_k, self.index.ntotal)

        with _lock:
            distances, indices = self.index.search(vec, k)

        results: list[dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append({
                "chunk_id": meta.get("chunk_id", ""),
                "text": meta.get("text", ""),
                "url": meta.get("url", ""),
                "title": meta.get("title", ""),
                "score": float(dist),
            })
        return results

    def count(self) -> int:
        return self.index.ntotal

    def clear(self) -> dict:
        """Reset the index and metadata."""
        with _lock:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            self._save()
        return {"cleared": True, "total": 0}
