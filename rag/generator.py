import anthropic

MODEL = "claude-sonnet-4-20250514"

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


SYSTEM_PROMPT = """You are a document Q&A assistant. Answer the user's question based ONLY on the provided context chunks.

Rules:
1. Only use information from the provided context. If the answer is not in the context, say "I don't have enough information in the document to answer this question."
2. For every claim in your answer, add a citation in the format [Source: {filename}, Chunk {chunk_index}].
3. Be precise and concise. Quote relevant passages when helpful.
4. Never invent or hallucinate information not present in the context."""


def generate_answer(question: str, search_results: dict) -> str:
    """Generate an answer with citations using Claude Sonnet."""
    documents = search_results["documents"][0]
    metadatas = search_results["metadatas"][0]

    # Build context from retrieved chunks
    context_parts = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        context_parts.append(
            f"--- Chunk {meta['chunk_index']} from {meta['source']} "
            f"(chars {meta['char_start']}-{meta['char_end']}) ---\n{doc}"
        )
    context = "\n\n".join(context_parts)

    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }
        ],
    )
    return response.content[0].text
