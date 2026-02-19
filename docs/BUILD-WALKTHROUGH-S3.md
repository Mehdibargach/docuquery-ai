# BUILD Walkthrough — Scope 3: From Prototype to Product

> Part of "The Builder PM" book — Chapter: BUILD Phase
> Walkthrough for DocuQuery AI, Scope 3
> Follows BUILD-WALKTHROUGH-WS.md (Walking Skeleton), BUILD-WALKTHROUGH-S1.md (PDF + CSV), and BUILD-WALKTHROUGH-S2.md (Citation Precision)

---

## 1. What This Scope Does

After Scope 2, DocuQuery AI worked. The EVALUATE phase confirmed it: 87.5% accuracy, 0% hallucination, 75% citation accuracy. The product was functional.

But it lived in Streamlit — a Python prototyping framework that runs locally and looks like what it is: a prototype. No hiring manager would look at a Streamlit app and think "this person ships products." They'd think "this person writes scripts."

Scope 3 transforms DocuQuery AI from a local prototype into a deployed, portfolio-grade product. Three changes:

1. **Backend split** — Extract the RAG pipeline into a FastAPI REST API (separate from the Streamlit UI)
2. **Deploy** — Put the backend on Render so it's accessible from anywhere
3. **Frontend rebuild** — Replace Streamlit with a React/Tailwind app built in Lovable (dark-mode, responsive, professional)

The key constraint: **zero changes to the 5 RAG modules.** Parser, chunker, embedder, store, generator — all untouched. This isn't a rewrite. It's a skin transplant.

---

## 2. The Architecture Decision

This is the biggest architectural decision since replacing ChromaDB with NumPy in the Walking Skeleton.

### Why Not Just Improve Streamlit?

| Option | Pros | Cons |
|--------|------|------|
| Polish Streamlit | Zero new code. Themes, custom CSS. | Still looks like Streamlit. Limited layout control. Can't deploy easily. No dark mode. LaTeX `$` rendering bug from EVALUATE persists. |
| FastAPI + React (Lovable) | Modern SaaS aesthetic. Full layout control. Deployable. Portfolio-grade. LaTeX bug eliminated (React renders markdown differently). | Two codebases. New deployment infra. CORS configuration. |

The decision was clear: a portfolio piece needs to look like a product, not a prototype.

### The Split

```
BEFORE (Streamlit monolith):
┌──────────────────────────────────────────┐
│ app.py (Streamlit)                        │
│   Upload UI → Parse → Chunk → Embed      │
│   Question UI → Search → Generate → Show  │
└──────────────────────────────────────────┘
  Runs locally only. Python-only UI.

AFTER (FastAPI + React):
┌──────────────────────┐     ┌──────────────────────┐
│ Lovable (React)       │────→│ api.py (FastAPI)      │
│ Upload UI             │ API │ POST /upload          │
│ Chat UI               │────→│ POST /query           │
│ About page            │     │ GET  /health          │
│ Dark/Light mode       │     │                       │
└──────────────────────┘     │ rag/parser.py    ←same│
  Deployed on lovable.app    │ rag/chunker.py   ←same│
                              │ rag/embedder.py  ←same│
                              │ rag/store.py     ←same│
                              │ rag/generator.py ←same│
                              └──────────────────────┘
                               Deployed on Render ($7/mo)
```

**The critical insight:** The RAG modules don't know (or care) that the frontend changed. They receive text, return results. That's the value of the modular architecture we built in the Walking Skeleton — the same 5 files serve both Streamlit and React.

---

## 3. Slice 1: The FastAPI Backend

### The Problem

`parse_file()` expects an object with `.name`, `.read()`, and `.seek()` — Streamlit's `UploadedFile` interface. FastAPI uses `UploadFile`, which has `.filename` (not `.name`) and async methods (not sync).

If we modify `parse_file()` to accept FastAPI's format, we break the Streamlit app. If we keep it as-is, FastAPI can't call it.

### The Solution: Adapter Pattern

Instead of modifying the RAG module, we create a lightweight adapter in `api.py` that makes FastAPI's upload look like Streamlit's upload:

```python
class _UploadFileAdapter:
    """Makes FastAPI's UploadFile look like Streamlit's UploadedFile."""

    def __init__(self, filename: str, content: bytes):
        self.name = filename          # .name, not .filename
        self._buffer = io.BytesIO(content)

    def read(self) -> bytes:          # sync, not async
        return self._buffer.read()

    def seek(self, pos: int) -> None:
        self._buffer.seek(pos)
```

**Analogy:** A power adapter. Your laptop (parse_file) has a US plug. The outlet (FastAPI) is European. The adapter converts the interface without modifying either side. The laptop doesn't know it's in Europe. The outlet doesn't know it's serving a US device.

**Why this matters architecturally:** Zero lines changed in `rag/`. Zero regression risk. The adapter lives in `api.py` — the only new file. If we ever add a third frontend (CLI, mobile), we write another adapter. The RAG pipeline stays frozen.

### The Three Endpoints

```python
@app.get("/health")
# Returns {"status": "ok", "version": "1.0"}
# Used by: monitoring, CORS testing, Render health checks

@app.post("/upload")
# Receives: file (multipart/form-data)
# Does: adapt → parse → chunk → embed → store
# Returns: {"filename", "file_type", "num_chunks", "status"}

@app.post("/query")
# Receives: {"question": "..."}
# Does: embed query → search → generate
# Returns: {"answer", "latency", "sources": [{chunk_index, page_start, ...}]}
```

The `/query` endpoint returns structured source data (chunk index, pages, text preview) instead of the raw debug dump that Streamlit showed. This lets the frontend display citation cards properly.

### CORS Configuration

The frontend and backend live on different domains. Browsers block cross-origin requests by default (security). CORS (Cross-Origin Resource Sharing) tells the browser "this frontend is allowed to call this backend."

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Lovable local dev
        "http://localhost:3000",      # Generic local dev
        "https://docuquery-ai-5rfb.onrender.com",  # Render self
    ],
    allow_origin_regex=r"https://.*\.(lovableproject\.com|lovable\.app)",
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # Lovable uses TWO domains: lovableproject.com (editor preview)
    # and lovable.app (published). Regex covers both.
)
```

**What went wrong:** The initial CORS config only allowed `*.lovable.app`. Lovable's editor runs on `*.lovableproject.com` — a completely different domain. Upload calls failed with a CORS error that looked like a network failure. Fixed by adding the regex pattern for both domains.

**Lesson:** Always test CORS from the actual client domain, not just from curl (curl ignores CORS — it's a browser-only security feature).

### Micro-Test Results

| # | Test | Command | Result |
|---|------|---------|--------|
| T1 | Health | `curl localhost:8000/health` | `{"status": "ok", "version": "1.0"}` — **PASS** |
| T2 | Upload PDF | `curl -F "file=@tests/test_sample.pdf" localhost:8000/upload` | 48 chunks — **PASS** |
| T3 | Query | `curl -X POST localhost:8000/query -d '{"question":"What is the total development budget?"}'` | "$18.5 million", 5.7s — **PASS** |
| T4 | Upload TXT | Same with test_doc.txt | 3 chunks — **PASS** |
| T5 | Upload CSV | Same with test_sample.csv | 4 chunks — **PASS** |

**Gate Slice 1: 5/5 PASS.** Same results as Streamlit. Zero regression.

---

## 4. Slice 2: Deploy to Render

### What and Why

The backend needs to be accessible from the internet for Lovable to call it. Render is a cloud hosting platform (like Heroku, Vercel, Railway) that deploys directly from GitHub.

**Decision: Render Starter ($7/mo) over Free tier.**

| | Free ($0) | Starter ($7/mo) |
|---|-----------|-----------------|
| Cold start | 30-60s after 15min idle | None — always on |
| For a demo | "Wait a minute..." | Instant response |
| For portfolio | Unreliable | Professional |

For a portfolio piece that a hiring manager might test at any moment, $7/mo is the obvious choice. The cost of a bad first impression is higher than $84/year.

### Deploy Setup

Three files needed:

**`Procfile`** — tells Render how to start the app:
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

**`render.yaml`** — infrastructure-as-code (Render reads this for auto-configuration):
```yaml
services:
  - type: web
    name: docuquery-ai
    runtime: python
    buildCommand: pip install -r requirements-api.txt
    startCommand: uvicorn api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
```

**`requirements-api.txt`** — only the actual dependencies (not the legacy `backend/requirements.txt` with ChromaDB, LangChain, etc.):
```
fastapi
uvicorn[standard]
python-multipart
anthropic
openai
pdfplumber
tiktoken
numpy
python-dotenv
pydantic
```

**Why a separate requirements file?** The existing `backend/requirements.txt` has 12 packages we don't use (ChromaDB, Pinecone, LangChain, python-docx, loguru...). Installing unused packages wastes build time and increases attack surface. A clean requirements file = faster deploys + fewer vulnerabilities.

### GitHub Repo

Created public repo: `github.com/Mehdibargach/docuquery-ai`

**Why public?** This is a portfolio piece. GitHub is the technical CV. A hiring manager who clicks your profile sees public repos with clean commits and real code. A private repo is invisible.

### Micro-Test Results

| # | Test | Local | Render | Result |
|---|------|-------|--------|--------|
| T6 | Health | `{"status": "ok"}` | `{"status": "ok"}` | **PASS** |
| T7 | Upload PDF | 48 chunks | 48 chunks | **PASS** |
| T8 | Query | "$18.5M", 5.7s | "$18.5M", 5.3s | **PASS** |

**Gate Slice 2: 3/3 PASS.** Backend identical on Render and local.

---

## 5. Slice 3: The Lovable Frontend

### The Approach: Structured Prompting

Lovable generates React/Tailwind apps from natural language prompts. The temptation is to dump everything in one massive prompt. We split it into three iterative prompts, each tested before moving to the next.

**Why three prompts?** Same reason we build in vertical slices — validate early, fix early. A single mega-prompt produces something that looks complete but may be fundamentally broken (wrong API integration, bad state management). Three prompts let you catch issues at each layer.

### Prompt 1: Structure + Upload

**What it defined:**
- Layout: header, main area, fixed input bar
- Upload zone with drag-and-drop
- 3-step progress stepper (Reading → Analyzing → Ready)
- Dark-first design system (dark bg #0A0A0B, indigo accent #6366F1, Inter font, 8px radius)
- API integration: POST to Render /upload endpoint

**Design decision — Dark mode default:**

| Style | Why rejected |
|-------|-------------|
| Claude/Anthropic (warm cream, peach accent) | Too close to copying. Not distinctive. |
| Generic SaaS (white, blue accent) | Forgettable. Every B2B tool looks like this. |
| **Dev-tool aesthetic (dark, indigo, minimal)** | Linear, Raycast, Vercel energy. Distinctive. Signals technical depth. |

**Stepper labels — user-friendly over technical:**

| Technical (rejected) | User-friendly (chosen) |
|---------------------|----------------------|
| Parsing | Reading your document |
| Embedding | Analyzing content |
| Ready | Ready to answer |

The technical version signals engineering knowledge to the developer. The user-friendly version signals UX maturity to the hiring manager. A Builder PM chooses the second — the engineering depth goes in the About page, not the UI.

### Prompt 2: Q&A + Citations

**What it defined:**
- Chat interface with user/AI message bubbles
- Skeleton loader during API calls
- Source cards (horizontal scroll, page/row numbers, text preview)
- Latency display
- Markdown rendering

**The CORS debugging session:**

First attempt: "Unable to reach the server." Console showed:
```
Access to fetch at 'https://docuquery-ai-5rfb.onrender.com/upload'
from origin 'https://...lovableproject.com' has been blocked by CORS
```

The origin was `lovableproject.com`, not `lovable.app`. Two different domains for Lovable's editor vs published app. Fixed the backend regex, pushed, waited for Render redeploy, re-tested. This is a classic deployment issue that you only discover in integration testing.

### Prompt 3: Polish + About Page

**What it defined:**
- Empty state (headline + subtitle + format pills)
- Error handling (toast with server error messages, not just HTTP codes)
- Mobile responsive layout
- Loading animations (skeleton, fade-in, slide-up)
- Footer: "Built by Mehdi Bargach" (LinkedIn link)
- `/about` page: case study format (Problem → Decisions → Metrics → Improvements)

**The headline decision:**

| Option | Why |
|--------|-----|
| "Upload a document to start asking questions" | Instruction, not value prop |
| "Ask your documents anything." + "Cited answers from any file — in seconds." | Clear problem + differentiator (citations) + speed |

**The About page:**

The About page is not documentation — it's a portfolio case study. It follows the format hiring managers expect from PM candidates: Problem → Decisions → Results → Self-awareness.

Key sections:
- **Key Decisions** — 5 architectural decisions with alternatives rejected. Shows PM thinking, not just engineering.
- **Evaluation Results** — 87.5% accuracy, 0% hallucination. Real metrics from the EVALUATE phase.
- **What I'd Improve** — citation precision, latency, data privacy. Counter-intuitively, showing limitations increases credibility. A PM who says "everything is perfect" is either junior or lying.

---

## 6. What Went Wrong

### Problem 1: CORS Domain Mismatch

**What happened:** Lovable's editor uses `*.lovableproject.com` but we only whitelisted `*.lovable.app`.

**Root cause:** Assumed one domain. Lovable uses two: `lovableproject.com` (editor preview) and `lovable.app` (published).

**Fix:** Regex pattern `r"https://.*\.(lovableproject\.com|lovable\.app)"` covering both domains.

**Lesson:** CORS errors look like network failures in the browser. Always check the console for the actual origin domain. And never test CORS with curl alone — curl doesn't enforce CORS.

### Problem 2: Lovable Mock Mode

**What happened:** Lovable generated a working UI with simulated/mock API responses. It looked functional but wasn't actually calling the backend.

**Fix:** Explicit prompt telling Lovable to remove all mock data and call the real API endpoints.

**Lesson:** AI code generators optimize for "looks like it works" — they'll fake API responses to show a complete demo. Always verify with real API calls, not just visual inspection.

### Problem 3: Error Messages Showing HTTP Codes

**What happened:** Upload errors showed "Upload failed (400)" instead of the actual server message ("Unsupported file format: .docx").

**Root cause:** Lovable's error handling read the HTTP status code but not the response body.

**Fix:** Prompt telling Lovable to read the `detail` field from the JSON error response.

**Lesson:** Backend error messages are useless if the frontend doesn't display them. Always test the full error path end-to-end.

---

## 7. Micro-Test Results — Full Scope 3

### Slice 1 — FastAPI Backend

| # | Test | Result |
|---|------|--------|
| T1 | Health endpoint | **PASS** |
| T2 | Upload PDF (48 chunks) | **PASS** |
| T3 | Query ("$18.5 million") | **PASS** |
| T4 | Upload TXT (3 chunks) | **PASS** |
| T5 | Upload CSV (4 chunks) | **PASS** |

### Slice 2 — Render Deploy

| # | Test | Result |
|---|------|--------|
| T6 | Health (remote) | **PASS** |
| T7 | Upload PDF (remote, 48 chunks) | **PASS** |
| T8 | Query (remote, "$18.5 million") | **PASS** |

### Slice 3 — Lovable Frontend

| # | Test | Result |
|---|------|--------|
| P1-1 | Empty state visible | **PASS** |
| P1-2 | Upload flow + stepper + badge | **PASS** |
| P1-3 | Loading visible during upload | **PASS** |
| P1-4 | Dark/Light toggle | **PASS** |
| P1-5 | Error on .docx upload | **PASS** |
| P2-1 | Query returns "$18.5 million" | **PASS** |
| P2-2 | Citation cards with page numbers | **PASS** |
| P2-3 | Markdown rendered correctly | **PASS** |
| P2-4 | Multi-Q&A + scroll | **PASS** |
| P2-5 | Latency displayed | **PASS** |
| P3-1 | Mobile responsive | **PASS** |
| P3-2 | Error on failed query | **PASS** |
| P3-3 | Animations (skeleton, fade-in) | **PASS** |
| P3-4 | Footer with LinkedIn link | **PASS** |
| P3-5 | Dark/Light on main + About | **PASS** |
| P3-6 | About page navigation | **PASS** |
| P3-7 | Change document button | **PASS** |
| P3-8 | Enter sends / Shift+Enter newline | **PASS** |

**Gate Scope 3: 26/26 PASS.**

---

## 8. Summary of Changes

### Files Created

| File | Purpose |
|------|---------|
| `api.py` | FastAPI app — 3 endpoints, CORS, UploadFile adapter |
| `requirements-api.txt` | Clean dependency list (no legacy packages) |
| `Procfile` | Render start command |
| `render.yaml` | Render infrastructure config |

### Files Modified

| File | What Changed |
|------|-------------|
| `rag/*.py` | **NOTHING.** Zero changes to all 5 RAG modules. |

### External

| Component | Details |
|-----------|---------|
| GitHub | Public repo: `github.com/Mehdibargach/docuquery-ai` |
| Render | Starter tier ($7/mo), auto-deploy from GitHub |
| Lovable | React/Tailwind frontend, dark-first design, `/about` page |

---

## 9. Pipeline Architecture — Final State After Scope 3

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND — Lovable (React + Tailwind)                           │
│ Deployed on lovable.app                                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Upload Zone  │  │  Chat UI     │  │  About Page  │          │
│  │  Drag & drop  │  │  Q&A bubbles │  │  Case study  │          │
│  │  Stepper      │  │  Citations   │  │  Metrics     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘          │
│         │ POST /upload     │ POST /query                        │
└─────────┼──────────────────┼────────────────────────────────────┘
          │    HTTPS (CORS)  │
┌─────────▼──────────────────▼────────────────────────────────────┐
│ BACKEND — FastAPI (api.py)                                       │
│ Deployed on Render ($7/mo)                                       │
│                                                                  │
│  UploadFileAdapter → rag/parser.py → route by extension         │
│                       ├── _parse_txt()                           │
│                       ├── _parse_pdf() + page_map                │
│                       └── _parse_csv() + row grouping            │
│                                                                  │
│  rag/chunker.py → 500 tokens, 100 overlap                       │
│  rag/embedder.py → OpenAI text-embedding-3-small                │
│  rag/store.py → numpy cosine similarity, TOP_K=15               │
│  rag/generator.py → [P1][P2] markers → Claude Sonnet → answer  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. What We Learned

1. **The adapter pattern saves modules from change.** `_UploadFileAdapter` let us connect FastAPI to `parse_file()` without touching the RAG code. Same principle applies to any future frontend: CLI, mobile, another framework — write an adapter, not a rewrite.

2. **CORS is a browser-only concern.** curl ignores CORS. Your backend tests will pass while your frontend fails. Always test cross-origin from the actual browser client. And always check the console for the exact origin domain — don't guess.

3. **AI code generators fake completeness.** Lovable generated mock API responses that made the UI look functional. Without testing against the real backend, we would have shipped a demo that only pretends to work. Always verify with real API calls.

4. **Structured prompting beats mega-prompts.** Three iterative Lovable prompts (structure → functionality → polish), each validated before the next, produced a better result than one massive prompt would have. Same principle as vertical slices in code.

5. **The About page is the real portfolio piece.** The product demos capability. The About page demos thinking — decisions, trade-offs, metrics, self-awareness. A hiring manager can see a hundred RAG demos. They rarely see one with an eval gate framework and honest "What I'd Improve" section.

6. **$7/mo is the cheapest credibility investment.** Cold start on a free tier means a hiring manager waits 30-60 seconds. First impressions are formed in the first 3 seconds. The gap between "free but slow" and "paid but instant" is the gap between "side project" and "portfolio piece."
