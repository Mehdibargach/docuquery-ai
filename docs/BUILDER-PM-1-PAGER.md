# Builder PM 1-Pager

**Project Name:** DocuQuery AI
**One-liner:** Ask questions to your documents, get answers with citations.
**Date:** 2026-02-12
**Builder PM Method Phase:** BUILD (RAG pipeline, PM Vibe Coding)

---

## Problem

- PMs receive hundreds of pages of research, PRDs, competitor reports.
- No time to read everything — they need specific answers fast.
- Current options are all broken:
  - **Ctrl+F**: keyword only, misses semantic questions ("what does the report conclude about retention?").
  - **ChatGPT paste**: no citations, hallucinations, context window limits on long docs.
  - **Manual reading**: hours per document, doesn't scale across multiple docs.

## User

- **Primary:** Product Managers, UX Researchers
- **Secondary:** Strategy teams, consultants, analysts
- **Context:** B2B knowledge workers dealing with 50-200+ page documents regularly. Need answers during meetings, sprint planning, or strategy sessions — not hours later.

## Solution

| Pain | Feature |
|------|---------|
| Keyword search misses semantic questions | Natural language Q&A (ask "what does the report say about churn?" instead of guessing keywords) |
| ChatGPT gives answers without sources, hallucinates | Answers with exact citations (document name, page number, paragraph) |
| Manual reading doesn't scale | Upload and parse documents automatically (PDF, TXT, CSV) |

## Riskiest Assumption

**"A RAG pipeline with 500-token chunks and cosine similarity search can provide accurate, precisely cited answers (page + paragraph) from 50+ page documents."**

If this is wrong — if the citations are vague or the answers hallucinate — the product has no edge over ChatGPT paste. Everything else (multi-doc, UI polish, auth) is irrelevant until this is proven.

**Update (2026-02-13):** Walking Skeleton micro-test PASSED (5/5 correct answers, 5/5 correct citations on a 10-page document). Riskiest Assumption holds. Continue to Scopes.

## Scope Scoring

**Criteria:**
- **Pain** (1-3): Does this feature solve the core problem? 1 = nice-to-have, 3 = without it the product is useless.
- **Risk** (1-3): Does building this test our riskiest assumption? 1 = we already know the answer, 3 = this IS the critical test.
- **Effort** (1-3): How hard to build? 1 = a few hours, 2 = 1-2 days, 3 = 3+ days.

**Formula:** Score = Pain + Risk - Effort. **MVP threshold: ≥ 3.**

| Feature | Pain | Risk | Effort | Score | In/Out |
|---------|------|------|--------|-------|--------|
| Upload + parse documents (PDF, TXT, CSV) | 3 | 2 | 2 | **3** | IN |
| Q&A with exact citations (page, paragraph) | 3 | 3 | 2 | **4** | IN |
| Multi-document search | 2 | 2 | 2 | **2** | OUT |
| Drag & drop UI | 2 | 1 | 1 | **2** | OUT |
| Session history | 1 | 1 | 1 | **1** | OUT |
| Auth / multi-user | 1 | 1 | 3 | **-1** | OUT |
| Conversational memory (follow-ups) | 2 | 2 | 3 | **1** | OUT |
| Image/table extraction from PDFs | 2 | 2 | 3 | **1** | OUT |
| DOCX support | 1 | 1 | 2 | **0** | OUT |

### MVP (Score ≥ 3)
- Upload + parse documents (PDF, TXT, CSV)
- Natural language Q&A with exact citations

### Out of Scope (Score < 3)
- Multi-document search (v1.1 — first after MVP, score 2)
- Drag & drop UI (v1.1 — basic file input is enough for MVP)
- Session history
- Authentication / multi-user
- Conversational memory
- Image/table extraction
- DOCX support
- Pinecone / cloud vector DB

## Success Metrics

| Metric | Target | How to Test |
|--------|--------|-------------|
| Answer accuracy | Correct answer from a 50-page PDF | Upload real PRD, ask 10 questions, grade manually |
| Citation quality | Source points to the right paragraph | Verify each citation matches the answer content |
| Latency | < 5 seconds end-to-end | Time from question submit to answer render |
| Format support | Works with PDF, TXT, CSV | Upload + query each format, verify results |
| Usability | Non-tech person uses it without instructions | Watch 2-3 people use it cold, note where they get stuck |

## Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector Store | numpy in-memory cosine similarity (replaced ChromaDB) | ChromaDB had SQLite issues on iCloud. numpy = zero dependencies, ~50 lines, same performance. Pinecone overkill for MVP. |
| Chunk size | 500 tokens, 100 token overlap | Hypothesis: smaller chunks = more precise citation attribution. To validate in EVALUATE. |
| File types | PDF, TXT, CSV (no DOCX) | CSV more useful for PM work (data exports, research tables). DOCX adds parser complexity. |
| LLM | Claude Sonnet only (no GPT-4) | One LLM = simpler billing, simpler code. Claude better at following citation instructions. |
| Embedding | text-embedding-3-small (OpenAI) | Cheap ($0.02/1M tokens), good quality for MVP. Upgrade path exists. |
| API layer | FastAPI (Python) | Async support for LLM calls, auto-generated API docs, Pydantic validation. |
| Interface | Streamlit or React (TBD in BUILD) | Streamlit for speed, React if we need more control. Decide in first BUILD session. |

## Open Questions

- How well does the numpy in-memory store handle 50+ page documents with 500-token chunks? (~500+ vectors per doc — is cosine similarity search still fast?)
- Is 500-token chunk size actually better for citation precision than 1000 chars? This is a hypothesis, not a fact — needs A/B comparison in EVALUATE.
- CSV parsing: do we treat rows as chunks or the whole file? Tabular data doesn't chunk the same way as prose.
