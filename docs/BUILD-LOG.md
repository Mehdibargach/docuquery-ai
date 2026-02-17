# Build Log — DocuQuery AI

**Project Name:** DocuQuery AI

---

## Entries

### 2026-02-12 — FRAME

**What happened:**
Created Builder PM 1-Pager. Identified 5 inconsistencies between project-specs.md and ARCHITECTURE.md (chunk size, vector DB, file types, LLM, scope). Resolved all in 1-Pager. Added Riskiest Assumption and Scope Scoring (Pain/Risk/Effort) to replace intuitive IN/OUT list.

**Decisions made:**
- ChromaDB only (no Pinecone) — MVP simplicity
- 500 tokens, 100 overlap (hypothesis to validate in EVALUATE)
- CSV not DOCX — more useful for PM work
- Claude Sonnet only — one LLM, simpler code
- MVP = upload + Q&A with citations. Multi-doc search = v1.1.
- Riskiest Assumption: "RAG can provide precisely cited answers from 50+ page docs"

**Time spent:** 1.5h

**Next step:** Update ARCHITECTURE.md to match 1-Pager, then start BUILD

---

### 2026-02-13 — BUILD Gameplan + Method Audit

**What happened:**
Created BUILD Gameplan for DocuQuery AI. Decomposed MVP into Walking Skeleton + 3 Scopes (vertical slices). Discovered critical anti-pattern: the original plan decomposed into backend → frontend → integration (horizontal layers). Replaced with vertical slicing approach across all files.

Audited the Builder PM Method end-to-end. Formalized: 4 phases, 2 iteration loops, 7 templates, 5 GO/NO-GO rituals, configurable Cycle timebox. Confirmed originality through competitive research — "Builder PM" is an unclaimed term, no integrated method exists combining 1-Pager + Walking Skeleton + AI Evaluation + SHIP.

**Decisions made:**
- Walking Skeleton = TXT only → full end-to-end (upload → chunk → embed → search → answer with citation)
- Scope 1 = PDF + CSV parsing (format support, vertical)
- Scope 2 = Citation precision + error handling (quality, vertical)
- Scope 3 = UI polish via Lovable (usability, vertical)
- Anti-pattern: NEVER decompose backend → frontend → integration. Always vertical slices.
- Method: Cycle = configurable timebox (not fixed "1 week side project")

**Time spent:** 2h

**Next step:** Start Walking Skeleton build (TXT → answer with citation, end-to-end)

---

### 2026-02-13 — BUILD: Walking Skeleton Complete

**What happened:**
Built the full Walking Skeleton end-to-end: TXT upload → chunk (500 tokens, 100 overlap) → embed (OpenAI text-embedding-3-small) → store → search → generate answer with citations (Claude Sonnet) → display in Streamlit UI.

Hit 4 problems during the build:
1. Python 3.14 incompatibility with tiktoken → used Python 3.11 venv
2. Anthropic API 529 (overloaded) on rapid successive calls → added 3-second delay
3. ChromaDB telemetry warning → ignored (cosmetic)
4. **ChromaDB SQLite critical failure** — `no such table: collections` error. Tried 5 fixes (EphemeralClient, Settings, /tmp path, etc.), none worked. Root cause: ChromaDB 0.6.3 SQLite initialization fails on iCloud-synced directories. **Replaced ChromaDB entirely with numpy-based cosine similarity** (~50 lines of code). Same API surface, zero external dependencies.

Ran micro-test on 10-page document (25,159 chars, 14 chunks): Q4 tested → correct answer ("1 week" for recommended Cycle duration) with correct citations (Chunks 12, 13). Remaining 4 questions to run.

**Decisions made:**
- ChromaDB → numpy in-memory store (ADR-worthy: simplicity wins over feature-rich library)
- Python 3.11 (not 3.14) for venv
- Created ultra-didactic BUILD-WALKTHROUGH-WS.md (~5,000 words) for the book

**Time spent:** 4h (build) + 2h (documentation) + 1h (debugging ChromaDB)

**Next step:** Complete micro-test (5/5 questions), then Skeleton Check → Scope 1

---

### 2026-02-17 — BUILD: Scope 1 (PDF + CSV Parsing)

**What happened:**
Added PDF and CSV support to DocuQuery AI as two vertical slices. The pipeline now handles three file formats end-to-end: TXT (existing), PDF (new), and CSV (new).

Created `rag/parser.py` — a routing module that detects file type by extension and delegates to the correct parser:
- `_parse_txt()`: reads UTF-8 with latin-1 fallback (same behavior as Walking Skeleton, extracted from app.py)
- `_parse_pdf()`: uses pdfplumber to extract text page-by-page, builds a `page_map` that maps each page to character positions in the full text
- `_parse_csv()`: converts each row to prose format (`"Row 1: col1=val1, col2=val2"`), groups rows into chunks under 400 tokens, prepends headers to each chunk for context

Modified 4 existing files:
- `chunker.py`: added `page_map` parameter and `_find_pages()` helper that maps chunk character ranges to PDF page numbers
- `store.py`: replaced 4 hardcoded metadata keys with dynamic passthrough (`{k: v for k, v in chunk.items() if k != "text"}`) — store is now format-agnostic
- `generator.py`: updated system prompt for multi-format citations (PDF→Page, CSV→Rows, TXT→Chunk), added `_format_chunk_header()` for context-aware headers
- `app.py`: extended file uploader to accept PDF/CSV, routes through parser, enriched debug panel with page/row info, added scanned PDF warning

**Decisions made:**
- pdfplumber over PyPDF2/pymupdf/pdfminer — pure Python, MIT license, clean page-by-page API, accepts BytesIO (Streamlit-compatible)
- CSV rows converted to prose (not raw CSV) — embedding models understand natural language better than comma-separated values
- CSV chunk limit = 400 tokens (not 500) — leaves room for the header line prepended to each chunk
- Store passthrough is dynamic — any new metadata field added by future parsers will flow through without touching store.py
- Scanned PDF warning at <100 chars — graceful degradation, not a crash

**Problems encountered:**
- Initial test PDF was 3 pages instead of 50+ (gameplan violation). Fixed: generated 59-page NovaPay PRD.
- fpdf2 crashed on Unicode characters (em-dash, smart quotes). Fixed: ASCII replacement function.
- `load_dotenv()` fails from stdin (no stack frame). Fixed: `dotenv_values()` + `os.environ.update()`.
- Automated micro-test matching reported 3/6 FAIL — all 6 answers were correct (matching too strict, plus one expected value was wrong on our side).

**Micro-test results: 6/6 PASS**
- PDF (59 pages, 48 chunks): 3/3 — budget ($18.5M), latency (340ms), design partners (15) all correct with accurate page citations
- CSV (25 rows, 4 chunks): 2/2 — highest score (Advanced Analytics, 4.9) and shipped count (20) correct with row citations
- TXT (regression): 1/1 — zero regression, same behavior as Walking Skeleton

**Process correction:** Added 4 Build Rules to CLAUDE.md: (1) micro-test = gate before commit, (2) gameplan authoritative on test data, (3) walkthrough quality checklist, (4) no batch mode.

**Time spent:** ~4h (code: 1h, 59-page PDF generation: 1h, micro-tests + debugging env vars: 1h, walkthrough rewrite: 1h)

**Next step:** Scope 2 (Citation precision + error handling)

---

## Running Notes

- Started BUILD before FRAME — caught the mistake, went back. This is exactly what the method is designed to prevent.
- The inconsistencies between specs and architecture prove why FRAME matters: without a single source of truth, every contributor (including future-you) makes different assumptions.
- First version of 1-Pager had scope IN/OUT with no rationale. Added Pain/Risk/Effort scoring — the table IS the rationale. Scoring caught an error: Session History was intuitively IN but scores 1. Intuition != method.
- "500 tokens = better citation precision" was stated as fact. It's a hypothesis. Marked it as such — to validate in EVALUATE.
