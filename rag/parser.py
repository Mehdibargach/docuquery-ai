"""File parser module — routes uploaded files to the correct parser."""

from dataclasses import dataclass, field
import io

import pdfplumber
import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CSV_CHUNK_TOKEN_LIMIT = 400
SUPPORTED_EXTENSIONS = {"txt", "pdf", "csv"}


@dataclass
class ParseResult:
    text: str
    filename: str
    file_type: str  # "txt", "pdf", "csv"
    page_map: list[tuple[int, int, int]] | None = None  # [(page_num, char_start, char_end)]
    chunks: list[dict] | None = None  # Pre-built chunks for CSV


def parse_file(uploaded_file) -> ParseResult | None:
    """Route an uploaded file to the appropriate parser based on extension.

    Returns None if the file type is unsupported.
    """
    filename = uploaded_file.name
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        return None

    if ext == "pdf":
        return _parse_pdf(uploaded_file, filename)
    elif ext == "csv":
        return _parse_csv(uploaded_file, filename)
    else:
        return _parse_txt(uploaded_file, filename)


def _parse_txt(uploaded_file, filename: str) -> ParseResult:
    """Parse a plain text file."""
    raw = uploaded_file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return ParseResult(text=text, filename=filename, file_type="txt")


def _parse_pdf(uploaded_file, filename: str) -> ParseResult:
    """Parse a PDF file, extracting text page-by-page with a page_map."""
    uploaded_file.seek(0)
    pdf_bytes = io.BytesIO(uploaded_file.read())

    pages_text: list[str] = []
    page_map = []  # (page_number, char_start, char_end)
    char_count = 0

    with pdfplumber.open(pdf_bytes) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            if page_text and not page_text.endswith("\n"):
                page_text += "\n"
            char_start = char_count
            pages_text.append(page_text)
            char_count += len(page_text)
            page_map.append((i + 1, char_start, char_count))  # 1-indexed page numbers

    # Single join at the end — avoids O(n^2) string concatenation
    full_text = "".join(pages_text)

    if len(full_text.strip()) < 100:
        # Warning: likely a scanned/image-based PDF
        pass

    return ParseResult(
        text=full_text,
        filename=filename,
        file_type="pdf",
        page_map=page_map,
    )


def _parse_csv(uploaded_file, filename: str) -> ParseResult:
    """Parse a CSV file, converting rows to prose and grouping into chunks."""
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    lines = content.strip().split("\n")
    if len(lines) < 2:
        return ParseResult(text=content, filename=filename, file_type="txt")

    # Parse header
    header_line = lines[0]
    headers = [h.strip().strip('"') for h in header_line.split(",")]

    # Convert each data row to prose
    prose_rows = []
    for row_idx, line in enumerate(lines[1:], start=1):
        values = _split_csv_line(line)
        parts = [f"{headers[j]}={values[j]}" for j in range(min(len(headers), len(values)))]
        prose_rows.append((row_idx, f"Row {row_idx}: {', '.join(parts)}"))

    # Group rows into chunks under the token limit
    header_str = "Headers: " + ", ".join(headers) + "\n\n"
    header_tokens = len(ENCODING.encode(header_str))

    chunks = []
    current_rows = []
    current_row_start = None
    current_tokens = header_tokens

    for row_num, prose in prose_rows:
        row_tokens = len(ENCODING.encode(prose + "\n"))

        if current_tokens + row_tokens > CSV_CHUNK_TOKEN_LIMIT and current_rows:
            # Flush current chunk
            chunk_text = header_str + "\n".join(r for _, r in current_rows)
            chunks.append({
                "text": chunk_text,
                "source": filename,
                "chunk_index": len(chunks),
                "char_start": 0,
                "char_end": 0,
                "file_type": "csv",
                "page_start": None,
                "page_end": None,
                "row_start": current_row_start,
                "row_end": current_rows[-1][0],
            })
            current_rows = []
            current_tokens = header_tokens
            current_row_start = None

        if current_row_start is None:
            current_row_start = row_num
        current_rows.append((row_num, prose))
        current_tokens += row_tokens

    # Flush last chunk
    if current_rows:
        chunk_text = header_str + "\n".join(r for _, r in current_rows)
        chunks.append({
            "text": chunk_text,
            "source": filename,
            "chunk_index": len(chunks),
            "char_start": 0,
            "char_end": 0,
            "file_type": "csv",
            "page_start": None,
            "page_end": None,
            "row_start": current_row_start,
            "row_end": current_rows[-1][0],
        })

    return ParseResult(
        text=content,
        filename=filename,
        file_type="csv",
        chunks=chunks,
    )


def _split_csv_line(line: str) -> list[str]:
    """Split a CSV line handling quoted fields with commas."""
    fields = []
    current = ""
    in_quotes = False
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            fields.append(current.strip().strip('"'))
            current = ""
        else:
            current += char
    fields.append(current.strip().strip('"'))
    return fields
