from openai import OpenAI

MODEL = "text-embedding-3-small"

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using OpenAI text-embedding-3-small.

    Returns a list of embedding vectors.
    """
    client = _get_client()
    response = client.embeddings.create(model=MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
