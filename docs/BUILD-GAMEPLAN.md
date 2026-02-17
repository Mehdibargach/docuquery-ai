# BUILD Gameplan

> Template from The Builder PM Method — BUILD phase (start)
> Fill this AFTER the 1-Pager, BEFORE writing any code.
> Decompose your MVP into vertical slices — NOT horizontal layers (backend, frontend).
> Each slice goes end-to-end: from data to user interface.

---

**Project Name:** DocuQuery AI
**Date:** 2026-02-13
**Cycle Appetite:** 1 week (side project)
**MVP Features (from 1-Pager):**
- Upload + parse documents (PDF, TXT, CSV)
- Natural language Q&A with exact citations (page, paragraph)

**Riskiest Assumption (from 1-Pager):**
"A RAG pipeline with 500-token chunks and ChromaDB can provide accurate, precisely cited answers (page + paragraph) from 50+ page documents."

---

## Context Setup

> Before writing the first line of code, configure your AI tool so it understands the project.

**Action:** The 1-Pager's key sections (Problem, Solution, Architecture Decisions) go into the project's `CLAUDE.md` for Claude Code. For Lovable (Scope 3), use the initial project description.

**For each slice:** Give Claude Code the slice description below (What it does + Done when + Architecture Decisions from 1-Pager).

---

## Walking Skeleton

> The thinnest possible slice that goes end-to-end and tests your Riskiest Assumption.
> This is ALWAYS your first build. No exceptions.
> Reference: Cockburn (Crystal Clear), Hunt & Thomas (Pragmatic Programmer — Tracer Bullet).

**What it does:** Upload a TXT file, chunk it, embed it, store in ChromaDB, ask a question, get an answer with a citation pointing to the right chunk.

**End-to-end path:** TXT upload → chunking (500 tokens, 100 overlap) → embedding (text-embedding-3-small) → ChromaDB storage → semantic search (top 5) → Claude Sonnet generation → answer + citation displayed

**Done when:** A user can upload a .txt file via a minimal Streamlit UI, ask a question about its content, and receive a correct answer with a citation that points to the right passage.

**Micro-test:** Upload a 10-page TXT document. Ask 5 factual questions. Grade: are the answers correct? Do the citations point to the right passage?

→ **RITUAL: Skeleton Check** — Does the Riskiest Assumption hold?
- If NO → Pivot or kill. The RAG approach doesn't produce precise enough citations — consider larger chunks, hybrid search, or different embedding model before continuing.
- If YES → Continue to Scopes.

---

## Scopes

> Each scope is a vertical slice: a coherent piece of the product that can be finished independently.
> Order by value: most important scope first.
> Scope naming from Shape Up: "a scope is a piece of the problem, not a list of tasks."

### Scope 1: PDF + CSV parsing

**What it adds:** Support for PDF and CSV file formats, end-to-end. PDF: extract text with page numbers preserved (critical for citations). CSV: treat rows as structured data, handle tabular queries.
**Done when:** A user can upload a PDF or CSV, ask a question, and get an answer with a citation that includes the page number (PDF) or row reference (CSV).
**Micro-test:** Upload a 50-page PDF. Ask 3 questions. Verify citations include correct page numbers. Upload a CSV data export. Ask a data question. Verify the answer references the right rows.

### Scope 2: Citation precision + error handling

**What it adds:** Improved citation quality (paragraph-level precision, not just chunk-level). Graceful error handling for unsupported files, empty documents, queries with no relevant context. "I don't have enough information" responses when the answer isn't in the document.
**Done when:** Citations point to specific paragraphs (not just "chunk 3"). Edge cases handled without crashes. LLM correctly refuses to answer when context is insufficient.
**Micro-test:** Ask 3 questions where the answer IS in the document — verify paragraph-level citations. Ask 2 questions where the answer is NOT in the document — verify the system says so instead of hallucinating.

### Scope 3: UI polish (Lovable)

**What it adds:** Clean, usable interface. File upload area, question input, answer display with formatted citations, loading states. Non-technical user can use it without instructions.
**Done when:** A non-tech person can upload a document and ask questions without help. Interface shows clear loading states, formatted answers, and clickable citations.
**Micro-test:** Watch 2-3 people use it cold. Note where they get stuck. Zero confusion on core flow (upload → ask → read answer).

> **Running out of Cycle time?** Cut from the bottom. Scope 3 goes first, then Scope 2.
> The Walking Skeleton is non-negotiable — it tests the Riskiest Assumption.
> Better to ship 1 solid slice than 3 broken ones.

---

## Exit Criteria (BUILD → EVALUATE)

- [ ] All MVP features from 1-Pager functional end-to-end
- [ ] Riskiest Assumption tested (Skeleton Check passed)
- [ ] Open Questions from 1-Pager resolved or converted to ADRs
- [ ] Build Log up to date
- [ ] Ready for formal evaluation against Success Metrics
