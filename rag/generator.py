from openai import OpenAI

MODEL = "gpt-4o-mini"

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


SYSTEM_PROMPT = """You are a document Q&A assistant. Answer the user's question based ONLY on the provided context chunks.

Rules:
1. Only use information from the provided context. If the answer is not in the context, say "I don't have enough information in the document to answer this question."
2. For every claim in your answer, add a precise citation:
   - PDF files: [Source: {filename}, Page {page}, P{n}] where P{n} is the paragraph marker
   - CSV files: [Source: {filename}, Rows {start}-{end}]
   - Text files: [Source: {filename}, Chunk {chunk_index}, P{n}] where P{n} is the paragraph marker
   If no paragraph markers are present in the chunk, omit the P{n} part.
3. Be precise and concise. Quote relevant passages when helpful.
4. Never invent or hallucinate information not present in the context.
5. Write for a non-technical user. Never use internal terms like "chunks", "context", "embeddings", or "retrieval" in your answers. Refer to "the document" or "the uploaded file" instead."""


def _format_chunk_header(meta: dict) -> str:
    """Format the chunk header based on file type."""
    file_type = meta.get("file_type", "txt")
    source = meta["source"]
    chunk_idx = meta["chunk_index"]

    if file_type == "pdf":
        page_start = meta.get("page_start")
        page_end = meta.get("page_end")
        if page_start and page_end and page_start != page_end:
            page_info = f"Pages {page_start}-{page_end}"
        elif page_start:
            page_info = f"Page {page_start}"
        else:
            page_info = "Page unknown"
        return f"--- Chunk {chunk_idx} from {source} ({page_info}) ---"

    elif file_type == "csv":
        row_start = meta.get("row_start")
        row_end = meta.get("row_end")
        if row_start and row_end:
            return f"--- Chunk {chunk_idx} from {source} (Rows {row_start}-{row_end}) ---"
        return f"--- Chunk {chunk_idx} from {source} ---"

    else:
        return (f"--- Chunk {chunk_idx} from {source} "
                f"(chars {meta['char_start']}-{meta['char_end']}) ---")


def _add_paragraph_markers(text: str) -> str:
    """Add [P1], [P2], etc. markers to each paragraph in chunk text."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) <= 1:
        return text  # No markers for single-paragraph chunks
    return "\n\n".join(f"[P{i+1}] {p}" for i, p in enumerate(paragraphs))


def generate_answer(question: str, search_results: dict) -> str:
    """Generate an answer with citations using GPT-4o-mini."""
    documents = search_results["documents"][0]
    metadatas = search_results["metadatas"][0]

    # Build context from retrieved chunks
    context_parts = []
    for doc, meta in zip(documents, metadatas):
        header = _format_chunk_header(meta)
        marked_doc = _add_paragraph_markers(doc)
        context_parts.append(f"{header}\n{marked_doc}")
    context = "\n\n".join(context_parts)

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    return response.choices[0].message.content
