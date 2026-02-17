# BUILD Walkthrough — Scope 1: PDF + CSV Parsing

> DocuQuery AI — Side Project #1 of The Builder PM Method
> Date: 2026-02-17
> Author: Mehdi Bargach (Builder PM) + Claude Code (AI pair)
> Phase: BUILD (Scope 1)

---

## What is this document?

This is the Scope 1 walkthrough for DocuQuery AI. In the Walking Skeleton walkthrough, we built the entire pipeline end-to-end for TXT files. Now we're adding PDF and CSV support — two vertical slices that extend the existing pipeline without breaking what already works.

Every decision is explained. Every piece of code is broken down. If the Walking Skeleton walkthrough was "how RAG works," this one is "how to extend RAG to handle real-world file formats."

---

## Table of Contents

1. [Why PDF and CSV?](#1-why-pdf-and-csv)
2. [The approach: vertical slices, not horizontal layers](#2-the-approach)
3. [Step 1: The Parser — routing files to the right handler](#3-step-1-the-parser)
4. [Step 2: PDF parsing — text extraction with page mapping](#4-step-2-pdf-parsing)
5. [Step 3: CSV parsing — turning tables into prose](#5-step-3-csv-parsing)
6. [Step 4: The Chunker — adding page awareness](#6-step-4-the-chunker)
7. [Step 5: The Store — dynamic metadata passthrough](#7-step-5-the-store)
8. [Step 6: The Generator — multi-format citations](#8-step-6-the-generator)
9. [Step 7: The UI — accepting all formats](#9-step-7-the-ui)
10. [Decisions summary](#10-decisions-summary)

---

## 1. Why PDF and CSV?

The Walking Skeleton proved the pipeline works: upload a TXT file, ask a question, get an answer with citations. But no PM uses `.txt` files in their daily work. They use:

- **PDFs**: PRDs, research reports, strategy decks exported to PDF, compliance documents
- **CSVs**: data exports from analytics tools, metrics dashboards, A/B test results

Without PDF/CSV support, DocuQuery AI is a demo. With it, it's a tool you'd actually use.

### Why not DOCX?

DOCX was considered and rejected in FRAME. The reasoning:
- DOCX requires `python-docx` which adds complexity for marginal gain
- Most DOCX files can be exported to PDF
- CSV covers the "structured data" use case that DOCX doesn't
- Adding DOCX later is trivial once the parser routing exists

---

## 2. The approach: vertical slices, not horizontal layers

A horizontal approach would be: "First, build all the parsers. Then update the chunker. Then update the store. Then update the generator. Then update the UI." This is how most teams work. It's also how you end up with parsers that don't work with the rest of the system until the very end.

The Builder PM Method uses **vertical slices**. Each slice adds a complete feature, end-to-end:

```
Slice 1 (PDF):  parser._parse_pdf → chunker (page_map) → store → generator → UI
Slice 2 (CSV):  parser._parse_csv → (chunker bypassed) → store → generator → UI
```

Each slice is independently testable. If PDF works but CSV doesn't, we still shipped value.

In practice, the code changes for both slices overlap significantly (the store and generator changes handle both formats), so we built them together. But conceptually, we thought about them as independent vertical slices.

---

## 3. Step 1: The Parser — routing files to the right handler

### The problem

In the Walking Skeleton, `app.py` had this inline:

```python
text = uploaded_file.read().decode("utf-8")
```

This works for TXT. It crashes on PDF (binary file, not UTF-8). It works on CSV but produces raw comma-separated text that embeddings handle poorly.

### The solution: `rag/parser.py`

We created a new module that sits between the file upload and the chunker. Its job is simple: look at the file extension, call the right parser, return a standardized result.

```python
@dataclass
class ParseResult:
    text: str                                        # Full extracted text
    filename: str
    file_type: str                                   # "txt", "pdf", "csv"
    page_map: list[tuple[int, int, int]] | None      # PDF: [(page, char_start, char_end)]
    chunks: list[dict] | None                        # CSV: pre-built chunks
```

**Why a dataclass?** Because different file types need different metadata:
- TXT needs nothing extra — just the text
- PDF needs a `page_map` so the chunker can figure out which page each chunk covers
- CSV needs `chunks` because it builds its own chunks (rows grouped under a token limit) instead of using the token-based chunker

**Why not just return text for everything?** Because citation quality depends on format-specific metadata. "Page 3" is useful for PDFs. "Rows 15-22" is useful for CSVs. If we stripped that information at parse time, the generator couldn't produce precise citations.

### The routing logic

```python
def parse_file(uploaded_file) -> ParseResult:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":    return _parse_pdf(uploaded_file, filename)
    elif ext == "csv":  return _parse_csv(uploaded_file, filename)
    else:               return _parse_txt(uploaded_file, filename)
```

Simple `if/elif/else`. No plugin system, no registry, no abstract base classes. Three formats, three branches. If we add DOCX later, it's one more `elif`.

---

## 4. Step 2: PDF parsing — text extraction with page mapping

### Choosing pdfplumber

| Library | Page-by-page | Text quality | Install | License |
|---------|:---:|:---:|:---:|:---:|
| **pdfplumber** | Yes | Good | `pip install` | MIT |
| PyPDF2 | Yes | Medium (missing spaces) | `pip install` | BSD |
| pymupdf (fitz) | Yes | Excellent | C extension required | AGPL |
| pdfminer | Yes | Good | `pip install` | MIT |

**pdfplumber wins** because:
1. Pure Python — no C extensions to compile (pymupdf fails on some systems)
2. MIT license — no AGPL concerns (pymupdf is AGPL, which contaminates your code)
3. Clean page-by-page API: `pdf.pages[i].extract_text()`
4. Accepts `BytesIO` — which is exactly what Streamlit's file uploader provides

### How PDF parsing works

```python
def _parse_pdf(uploaded_file, filename):
    pdf_bytes = io.BytesIO(uploaded_file.read())
    full_text = ""
    page_map = []

    with pdfplumber.open(pdf_bytes) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            char_start = len(full_text)
            full_text += page_text
            char_end = len(full_text)
            page_map.append((i + 1, char_start, char_end))  # 1-indexed
```

**The key insight is the `page_map`.** It records the character positions where each page starts and ends in the concatenated text. Later, when the chunker creates a chunk at characters 1500-2000, we can look up the page_map to find which pages those characters belong to.

**Why `or ""`?** Some PDF pages are blank or contain only images. `extract_text()` returns `None` for those. The `or ""` prevents a crash.

**Why 1-indexed?** Because when a user sees "Page 3" in a citation, they expect to open the PDF and find the information on the page numbered 3, not on the page at index 2.

### The scanned PDF problem

If a PDF contains only scanned images (no selectable text), pdfplumber extracts nothing. We detect this:

```python
if len(full_text.strip()) < 100:
    # Warning in UI: likely scanned/image-based PDF
```

We don't crash. We don't try OCR (that's a different scope entirely). We warn the user and let them decide. Graceful degradation, not a crash.

---

## 5. Step 3: CSV parsing — turning tables into prose

### The problem with raw CSV

If you feed `"Feature,Quarter,Status,Users\nSmart Search,Q1 2025,shipped,12500"` into an embedding model, it produces a mediocre vector. The model doesn't understand that "Smart Search" is a feature name and "12500" is its user count.

### The solution: prose conversion

We convert each row into natural language:

```
Row 1: Feature=Smart Search, Quarter=Q1 2025, Status=shipped, Users=12500
```

Now the embedding model understands the relationships. When someone asks "Which feature has the most users?", the vector for the question will be close to the vector for the row that says "Users=22000".

### Grouping rows into chunks

Unlike TXT/PDF where the chunker splits on token boundaries, CSV chunks are built by the parser itself. Why? Because splitting a CSV row in the middle is meaningless. Each row is atomic.

The algorithm:
1. Parse headers from the first line
2. Convert each data row to prose
3. Group consecutive rows until the total would exceed 400 tokens
4. Prepend the header line to each chunk (so each chunk is self-contained)

**Why 400 tokens, not 500?** The header line takes ~50-100 tokens depending on column count. 400 + header ≈ 450-500, staying within our chunk size target.

```python
for row_num, prose in prose_rows:
    row_tokens = len(ENCODING.encode(prose + "\n"))
    if current_tokens + row_tokens > CSV_CHUNK_TOKEN_LIMIT and current_rows:
        # Flush current chunk
        chunks.append(...)
        current_rows = []
        current_tokens = header_tokens
```

Each chunk's metadata includes `row_start` and `row_end`, so the generator can cite "Rows 9-16" instead of "Chunk 1".

### Encoding fallback

Excel exports CSVs in `latin-1`, not `utf-8`. We try `utf-8` first, fall back to `latin-1`:

```python
try:
    content = raw.decode("utf-8")
except UnicodeDecodeError:
    content = raw.decode("latin-1")
```

Same pattern as `_parse_txt()`. Simple, handles 99% of real-world CSVs.

---

## 6. Step 4: The Chunker — adding page awareness

### What changed

The chunker's core algorithm (500 tokens, 100 overlap) didn't change at all. We added two things:

1. **New parameters**: `file_type` and `page_map`
2. **New helper**: `_find_pages()` that maps character ranges to page numbers

### Before

```python
def chunk_text(text, filename) -> list[dict]:
    # Returns: text, source, chunk_index, char_start, char_end
```

### After

```python
def chunk_text(text, filename, file_type="txt", page_map=None) -> list[dict]:
    # Returns: text, source, chunk_index, char_start, char_end,
    #          file_type, page_start, page_end, row_start, row_end
```

**For TXT files**: `file_type="txt"`, `page_map=None` → `page_start=None`, `page_end=None`. Identical behavior to the Walking Skeleton. Zero regression risk.

### How `_find_pages()` works

```python
def _find_pages(char_start, char_end, page_map):
    for page_num, p_start, p_end in page_map:
        if p_end > char_start and p_start < char_end:
            # This page intersects with the chunk
```

It's a simple range intersection. If a chunk spans characters 700-1600, and Page 1 covers 0-763 and Page 2 covers 763-1506, then this chunk intersects both pages → `page_start=1, page_end=2`.

**Why a chunk can span multiple pages**: Our chunker works on tokens, not pages. A 500-token chunk might start at the bottom of Page 1 and continue into Page 2. The citation will say "Pages 1-2", which is accurate and useful — the user knows to look at both pages.

---

## 7. Step 5: The Store — dynamic metadata passthrough

### The one-line change that made everything work

In the Walking Skeleton, the store had 4 hardcoded metadata keys:

```python
# BEFORE
"metadatas": [[{
    "source": _chunks[i]["source"],
    "chunk_index": _chunks[i]["chunk_index"],
    "char_start": _chunks[i]["char_start"],
    "char_end": _chunks[i]["char_end"],
} for i in top_indices]]
```

Every time we add a new metadata field (like `page_start` or `row_end`), we'd need to update this list. That's fragile.

```python
# AFTER
"metadatas": [[{k: v for k, v in _chunks[i].items() if k != "text"}
               for i in top_indices]]
```

Now the store passes through **everything** except the text content. It doesn't need to know about pages, rows, or any future metadata. It's format-agnostic.

This is the kind of change that seems tiny but prevents an entire category of bugs. The store will never drop metadata fields again, no matter what new file formats we add.

---

## 8. Step 6: The Generator — multi-format citations

### Updated system prompt

The Walking Skeleton system prompt had one citation format: `[Source: {filename}, Chunk {chunk_index}]`. Now we have three:

```
- PDF files: [Source: {filename}, Page {page}]
- CSV files: [Source: {filename}, Rows {start}-{end}]
- Text files: [Source: {filename}, Chunk {chunk_index}]
```

The LLM sees the chunk headers and knows which format to use.

### Context-aware chunk headers

```python
def _format_chunk_header(meta):
    if file_type == "pdf":
        return f"--- Chunk {idx} from {source} (Page {page}) ---"
    elif file_type == "csv":
        return f"--- Chunk {idx} from {source} (Rows {row_start}-{row_end}) ---"
    else:
        return f"--- Chunk {idx} from {source} (chars {char_start}-{char_end}) ---"
```

When the LLM sees `"--- Chunk 0 from report.pdf (Page 2) ---"`, it knows to cite `[Source: report.pdf, Page 2]`. The header format matches the citation format in the system prompt. This alignment is intentional — it makes the LLM's job easier and citations more accurate.

---

## 9. Step 7: The UI — accepting all formats

### Changes to app.py

Three simple changes:
1. File uploader accepts `["txt", "pdf", "csv"]` instead of just `["txt"]`
2. Parsed files are routed through `parse_file()` instead of inline `read().decode()`
3. Debug panel shows pages/rows instead of just chunk index

### The routing logic

```python
result = parse_file(uploaded_file)
if result.file_type == "csv":
    chunks = result.chunks                    # CSV provides pre-built chunks
else:
    chunks = chunk_text(result.text, ...)     # TXT/PDF use the standard chunker
```

CSV is special because its chunks are built by the parser (row-based grouping), not by the token-based chunker. TXT and PDF both flow through the standard chunker.

### Enriched debug panel

The debug panel now shows format-specific information:
- PDF: `"Chunk 0 — Page 2 (distance: 0.4370)"`
- CSV: `"Chunk 1 — Rows 9-16 (distance: 0.5102)"`
- TXT: `"Chunk 0 (distance: 0.3456)"` (unchanged)

This helps users verify that citations are pointing to the right location.

---

## 10. Decisions summary

| Decision | Options considered | Chosen | Why |
|----------|-------------------|--------|-----|
| PDF library | pdfplumber, PyPDF2, pymupdf, pdfminer | pdfplumber | Pure Python, MIT, clean page API, BytesIO support |
| CSV strategy | Raw CSV, prose conversion | Prose conversion | Embeddings understand prose better than raw CSV |
| CSV chunk limit | 500 tokens, 400 tokens | 400 tokens | Leaves room for header prepended to each chunk |
| Store metadata | Hardcoded keys, dynamic passthrough | Dynamic passthrough | Future-proof, prevents dropped metadata bugs |
| Page numbers | 0-indexed, 1-indexed | 1-indexed | Matches what users see in PDF viewers |
| Scanned PDF | Crash, OCR, warn | Warn | OCR is a separate scope; warning is graceful |
| CSV encoding | UTF-8 only, UTF-8 + latin-1 fallback | Fallback | Handles Excel exports without crashing |

---

## Architecture after Scope 1

```
┌─────────────────────────────────────────────────────┐
│                    Streamlit UI                      │
│         (file upload: TXT, PDF, CSV)                │
└───────────┬─────────────────────────────┬───────────┘
            │ upload                       │ question
            ▼                             ▼
    ┌───────────────┐            ┌──────────────┐
    │  rag/parser   │            │ rag/embedder │
    │ (route by ext)│            │  (OpenAI)    │
    └───┬───┬───┬───┘            └──────┬───────┘
        │   │   │                       │
    TXT PDF CSV                         │
        │   │   │                       │
        ▼   ▼   │                       ▼
    ┌───────────┐│              ┌──────────────┐
    │rag/chunker││              │  rag/store   │
    │(500 tok,  ││              │  (numpy cos) │
    │ page_map) │└──────────────►  (dynamic    │
    └───────────┘               │   metadata)  │
                                └──────┬───────┘
                                       │ top 5
                                       ▼
                                ┌──────────────┐
                                │rag/generator │
                                │ (Claude,     │
                                │  multi-fmt   │
                                │  citations)  │
                                └──────────────┘
```

**New module**: `rag/parser.py` — sits between upload and chunker
**Modified**: chunker (page awareness), store (dynamic metadata), generator (multi-format citations), app.py (routing)
**Unchanged**: `rag/embedder.py` — embeddings don't care what format the text came from
