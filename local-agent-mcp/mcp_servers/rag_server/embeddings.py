"""Local embedding model wrapper using sentence-transformers.

Uses all-MiniLM-L6-v2 (384-dim) by default – fast, small, and runs on CPU.
The model is downloaded once and cached locally.
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_DIMENSION = 384

# Lazy singleton
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of strings. Returns float32 ndarray of shape (n, 384)."""
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return vectors.astype(np.float32)


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string. Returns shape (1, 384)."""
    return embed_texts([text])


def get_dimension() -> int:
    return _DIMENSION
