from openai import OpenAI

MODEL = "text-embedding-3-small"

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


BATCH_SIZE = 50


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using OpenAI text-embedding-3-small.

    Processes in batches of 50 to avoid memory spikes on large documents.
    Returns a list of embedding vectors.
    """
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=MODEL, input=batch)
        all_embeddings.extend(item.embedding for item in response.data)

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
