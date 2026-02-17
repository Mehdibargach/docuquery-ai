import numpy as np

_chunks: list[dict] = []
_embeddings: np.ndarray | None = None

TOP_K = 10


def add_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Store chunks and their embeddings in memory."""
    global _chunks, _embeddings
    _chunks = chunks
    _embeddings = np.array(embeddings)


def query(query_embedding: list[float], n_results: int = TOP_K) -> dict:
    """Find the most similar chunks using cosine similarity."""
    if _embeddings is None or len(_chunks) == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    query_vec = np.array(query_embedding)

    # Cosine similarity = dot product of normalized vectors
    norms = np.linalg.norm(_embeddings, axis=1)
    query_norm = np.linalg.norm(query_vec)
    similarities = _embeddings @ query_vec / (norms * query_norm)

    # Get top K indices (highest similarity first)
    k = min(n_results, len(_chunks))
    top_indices = np.argsort(similarities)[-k:][::-1]

    return {
        "documents": [[_chunks[i]["text"] for i in top_indices]],
        "metadatas": [[{k: v for k, v in _chunks[i].items() if k != "text"}
                       for i in top_indices]],
        "distances": [[float(1 - similarities[i]) for i in top_indices]],
    }


def clear() -> None:
    """Remove all stored data."""
    global _chunks, _embeddings
    _chunks = []
    _embeddings = None
