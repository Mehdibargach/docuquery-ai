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

## Definition of Ready / Definition of Done

> Standard DOR and DOD that apply to EVERY slice (Walking Skeleton + Scopes).
> Think of DOR as "can I START?" and DOD as "can I CLOSE?"
> No slice starts without DOR met. No slice closes without DOD met.

### DOR — Definition of Ready (before starting a slice)

| # | Criteria | Walking Skeleton variant |
|---|----------|--------------------------|
| R1 | Previous gate PASSED | FRAME Review ritual passed (1-Pager approved) |
| R2 | Dependencies identified and installed | Dev environment set up (venv, APIs verified) |
| R3 | Test data specs defined in gameplan (file type, size, content) | Test doc created per gameplan specs |
| R4 | Micro-tests defined as acceptance criteria in gameplan BEFORE coding | Same |
| R5 | CLAUDE.md updated with current phase and slice context | Same |

### DOD — Definition of Done (before closing a slice)

| # | Criteria | Artifact |
|---|----------|----------|
| D1 | All micro-tests PASS per gate criteria | Gameplan → Result line |
| D2 | BUILD-LOG entry written | `docs/BUILD-LOG.md` — what/decisions/problems/time |
| D3 | BUILD-WALKTHROUGH written + quality checklist passed | `docs/BUILD-WALKTHROUGH-{slice}.md` |
| D4 | CLAUDE.md updated with next phase | `CLAUDE.md` |
| D5 | Committed on main with descriptive message | Git log |

### Compliance tracker

| Slice | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | D5 | Status |
|-------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|--------|
| Walking Skeleton | FRAME Review | venv + APIs | test_doc.txt 10p | 5 tests defined | Done | 5/5 PASS | Done | WS.md | Done | `939f40b` | CLOSED |
| Scope 1 (PDF+CSV) | Skeleton Check | pdfplumber | 59p PDF + 25-row CSV | 6 tests defined | Done | 5/6 + 1 PARTIAL | Done | S1.md | Done | `567b3da` | CLOSED (P3 → Scope 2) |
| Scope 2 (Citation+Errors) | Scope 1 gate | none new | test_empty.txt + test_unsupported.docx | 7 tests defined | Done | 7/7 PASS | Done | S2.md | Done | `91baa8d` | CLOSED |
| Scope 3 | Scope 2 gate | — | — | — | — | — | — | — | — | — | NOT STARTED |

---

## Walking Skeleton

> The thinnest possible slice that goes end-to-end and tests your Riskiest Assumption.
> This is ALWAYS your first build. No exceptions.
> Reference: Cockburn (Crystal Clear), Hunt & Thomas (Pragmatic Programmer — Tracer Bullet).

**What it does:** Upload a TXT file, chunk it, embed it, store in ChromaDB, ask a question, get an answer with a citation pointing to the right chunk.

**End-to-end path:** TXT upload → chunking (500 tokens, 100 overlap) → embedding (text-embedding-3-small) → ChromaDB storage → semantic search (top 5) → Claude Sonnet generation → answer + citation displayed

**Done when:** A user can upload a .txt file via a minimal Streamlit UI, ask a question about its content, and receive a correct answer with a citation that points to the right passage.

**Micro-test:**

| # | Input | Question | Expected Answer | Expected Citation | Pass Criteria |
|---|-------|----------|-----------------|-------------------|---------------|
| WS-1 | `test_doc.txt` (10 pages, ~25K chars) | What are the four phases of the Builder PM Method? | FRAME, BUILD, EVALUATE, SHIP | [Source: test_doc.txt, Chunk 0] | All 4 phases listed + correct chunk |
| WS-2 | same | What is the micro-loop in the method? | BUILD <-> EVALUATE iterative loop | [Source: test_doc.txt, Chunk X] | Correct description + relevant chunk |
| WS-3 | same | What is a Walking Skeleton and where does the concept come from? | Thinnest end-to-end slice; Cockburn + Hunt & Thomas | [Source: test_doc.txt, Chunk 0] | Definition + both origins cited |
| WS-4 | same | How does the Builder PM Method differ from Scrum? | Configurable timebox, EVALUATE phase, not prescriptive ceremonies | [Source: test_doc.txt, Chunk X] | At least 2 differences + citation |
| WS-5 | same | What are the seven templates? | 1-Pager, BUILD Gameplan, Build Log, ADR, Eval Report, Deploy Checklist, Project Dossier | [Source: test_doc.txt, Chunk 2] | All 7 listed + correct chunk |

**Gate:** 5/5 correct answers AND 5/5 citations pointing to relevant chunks.

**Result:** 5/5 PASS (2026-02-13). Details in BUILD-WALKTHROUGH-WS.md Section 12.

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

**Micro-test:**

| # | Input | Question | Expected Answer | Expected Citation | Pass Criteria |
|---|-------|----------|-----------------|-------------------|---------------|
| P1 | `test_sample.pdf` (59 pages, 48 chunks) | What is the total development budget for NovaPay? | $18.5 million | [Source: test_sample.pdf, Page 1-2] | Correct amount + page citation |
| P2 | same | What is the P95 API response latency target? | 340 milliseconds | [Source: test_sample.pdf, Page 1-2] | Correct latency + page citation |
| P3 | same | How many design partners and what credit do they receive? | 15 design partners, $2,000/month during beta (LOI commitment) | [Source: test_sample.pdf, Page 6] | Both numbers correct + page citation |
| C1 | `test_sample.csv` (25 rows, 4 chunks) | Which feature has the highest satisfaction score? | Advanced Analytics (4.9) | [Source: test_sample.csv, Rows X-Y] containing row 21 | Correct feature + score + row citation |
| C2 | same | How many features have status "shipped"? | 20 | [Source: test_sample.csv, Rows X-Y] | Correct count + row citation |
| T1 | `test_doc.txt` (regression) | What are the four phases of the Builder PM Method? | FRAME, BUILD, EVALUATE, SHIP | [Source: test_doc.txt, Chunk X] | All 4 phases + chunk citation (zero regression) |

**Gate:** 6/6 correct answers AND 6/6 citations with format-specific references (pages for PDF, rows for CSV, chunks for TXT).

**Result:** 5/6 PASS, 1 PARTIAL (2026-02-17). P3 retrieval gap: 15 partners found (correct) but $2,000/month detail on Page 6 not in top 5 retrieved chunks. Details in BUILD-WALKTHROUGH-S1.md Section 11.

### Scope 2: Citation precision + error handling

**What it adds:** Improved citation quality (paragraph-level precision, not just chunk-level). Graceful error handling for unsupported files, empty documents, queries with no relevant context. "I don't have enough information" responses when the answer isn't in the document. Fix P3 retrieval gap from Scope 1 (increase top-K or add re-ranking).
**Done when:** Citations point to specific paragraphs (not just "chunk 3"). Edge cases handled without crashes. LLM correctly refuses to answer when context is insufficient.

**Micro-test:**

| # | Type | Input | Question / Action | Expected Behavior | Pass Criteria |
|---|------|-------|-------------------|-------------------|---------------|
| S2-1 | Precision | `test_sample.pdf` (59p) | What is the total development budget? | Answer with paragraph-level citation, not just "Page 1-2" | Citation includes specific section/paragraph reference |
| S2-2 | Precision | same | How many design partners and what do they commit to? | 15 partners, $2,000/month (LOI) — Page 6 retrieved | P3 regression fix: Page 6 chunk in top results |
| S2-3 | Precision | `test_doc.txt` | What are the seven templates? | Each template cited to its specific paragraph | At least 3 distinct paragraph-level citations |
| S2-4 | Refusal | `test_sample.pdf` | What is the CEO's favorite color? | "I don't have enough information in the document" | No hallucination, explicit refusal |
| S2-5 | Refusal | `test_sample.csv` | What was the company revenue in 2024? | "I don't have enough information in the document" | No hallucination, explicit refusal |
| S2-6 | Error | Upload a `.docx` file | — | Graceful error message (unsupported format) | No crash, clear user message |
| S2-7 | Error | Upload an empty `.txt` file | Ask any question | Graceful handling, no crash | No crash, meaningful message |

**Gate:** 7/7 — all precision tests show paragraph-level citations, all refusals are correct, all errors handled gracefully.

**Result:** 7/7 PASS (2026-02-17). S2-6 PASS by design (Streamlit filters at UI level) + defense-in-depth (parser returns None). UX fix: added Rule 5 to system prompt — LLM never uses technical jargon ("chunks", "context") in answers. Details in BUILD-WALKTHROUGH-S2.md.

### Scope 3: UI polish (Lovable)

**What it adds:** Clean, usable interface. File upload area, question input, answer display with formatted citations, loading states. Non-technical user can use it without instructions.
**Done when:** A non-tech person can upload a document and ask questions without help. Interface shows clear loading states, formatted answers, and clickable citations.

**Micro-test:**

| # | Type | Test | Expected Behavior | Pass Criteria |
|---|------|------|-------------------|---------------|
| S3-1 | Usability | Cold test: give app to 2-3 non-tech people, no instructions | Complete upload → ask → read flow without help | Zero confusion on core flow |
| S3-2 | Loading | Upload a 59-page PDF | Visible loading state during processing | User knows something is happening |
| S3-3 | Citations | Ask a question about the PDF | Citations are visually formatted and distinguishable | Citations stand out from answer text |
| S3-4 | Empty state | Open app with no file uploaded | Clear instructions on what to do | User understands they need to upload first |

**Gate:** 4/4 — all usability tests pass, zero confusion on core flow.

**Result:** — (not started)

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
