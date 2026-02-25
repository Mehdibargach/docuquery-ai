import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 100  # tokens


def chunk_text(text: str, filename: str, file_type: str = "txt", page_map: list | None = None) -> list[dict]:
    """Split text into ~500-token chunks with 100-token overlap.

    Returns a list of dicts with metadata including file_type and page info.
    """
    tokens = ENCODING.encode(text)
    chunks = []
    start = 0

    # Pre-compute char positions at chunk boundaries to avoid O(n^2) decoding.
    # Old code decoded tokens[:start] and tokens[:end] on EVERY iteration,
    # which for a 300-page PDF meant 1200+ decode calls and massive allocations.
    boundaries = set()
    pos = 0
    while pos < len(tokens):
        boundaries.add(pos)
        end = min(pos + CHUNK_SIZE, len(tokens))
        boundaries.add(end)
        if end >= len(tokens):
            break
        pos = end - CHUNK_OVERLAP
    boundaries.add(len(tokens))

    char_at = {}
    for b in sorted(boundaries):
        char_at[b] = len(ENCODING.decode(tokens[:b])) if b > 0 else 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_decoded = ENCODING.decode(chunk_tokens)

        char_start = char_at[start]
        char_end = char_at[end]

        # Find page range for PDF
        page_start, page_end = _find_pages(char_start, char_end, page_map)

        chunks.append({
            "text": chunk_text_decoded,
            "source": filename,
            "chunk_index": len(chunks),
            "char_start": char_start,
            "char_end": char_end,
            "file_type": file_type,
            "page_start": page_start,
            "page_end": page_end,
            "row_start": None,
            "row_end": None,
        })

        if end >= len(tokens):
            break
        start = end - CHUNK_OVERLAP

    return chunks


def _find_pages(char_start: int, char_end: int, page_map: list | None) -> tuple[int | None, int | None]:
    """Find the first and last page that intersect [char_start, char_end]."""
    if page_map is None:
        return None, None

    first_page = None
    last_page = None

    for page_num, p_start, p_end in page_map:
        # Check if this page intersects with the chunk range
        if p_end > char_start and p_start < char_end:
            if first_page is None:
                first_page = page_num
            last_page = page_num

    return first_page, last_page
