"""
RAG Retriever

Loads the FAISS index and chunk metadata from disk,
embeds a query, and returns the top-k most similar chunks.
"""

import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Paths — resolved relative to this file so it works from any CWD
_BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
_DEFAULT_INDEX_PATH = os.path.join(_BASE_DIR, "faiss_index", "index.faiss")
_DEFAULT_CHUNKS_PATH = os.path.join(_BASE_DIR, "faiss_index", "chunks.json")

# Lazy-loaded singletons
_model = None
_index = None
_chunks = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_index_and_chunks():
    """Load FAISS index and chunk metadata from disk (once)."""
    global _index, _chunks

    index_path = os.environ.get("FAISS_INDEX_PATH", _DEFAULT_INDEX_PATH)
    chunks_path = os.environ.get("CHUNKS_PATH", _DEFAULT_CHUNKS_PATH)

    if _index is None:
        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"FAISS index not found at {index_path}. "
                "Run `python rag/embedder.py` first to build the index."
            )
        _index = faiss.read_index(index_path)

    if _chunks is None:
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(
                f"Chunks metadata not found at {chunks_path}. "
                "Run `python rag/embedder.py` first to build the index."
            )
        with open(chunks_path, "r", encoding="utf-8") as f:
            _chunks = json.load(f)

    return _index, _chunks


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve the top-k most similar knowledge base chunks for a query.

    Args:
        query: The search query (typically skills + role combined).
        top_k: Number of chunks to return.

    Returns:
        List of dicts with keys: text, source, score (L2 distance).
    """
    index, chunks = _load_index_and_chunks()
    model = _get_model()

    # Embed the query
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding, dtype="float32")

    # Search FAISS index
    distances, indices = index.search(query_embedding, min(top_k, len(chunks)))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(chunks) and idx >= 0:
            chunk = chunks[idx]
            results.append({
                "text": chunk["text"],
                "source": chunk["source"],
                "score": float(dist),
            })

    return results
