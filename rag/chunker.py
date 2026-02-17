import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 100  # tokens


def chunk_text(text: str, filename: str) -> list[dict]:
    """Split text into ~500-token chunks with 100-token overlap.

    Returns a list of dicts:
        {"text": str, "source": str, "chunk_index": int, "char_start": int, "char_end": int}
    """
    tokens = ENCODING.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_decoded = ENCODING.decode(chunk_tokens)

        # Find character positions in original text for citation
        char_start = len(ENCODING.decode(tokens[:start]))
        char_end = len(ENCODING.decode(tokens[:end]))

        chunks.append({
            "text": chunk_text_decoded,
            "source": filename,
            "chunk_index": len(chunks),
            "char_start": char_start,
            "char_end": char_end,
        })

        if end >= len(tokens):
            break
        start = end - CHUNK_OVERLAP

    return chunks
