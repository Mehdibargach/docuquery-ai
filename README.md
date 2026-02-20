# DocuQuery AI

**Ask your documents anything. Cited answers from any file — in seconds.**

Upload a PDF, TXT, or CSV. Ask questions in natural language. Get answers grounded in your document with exact page and paragraph citations.

**[Try it live](https://query-doc-master.lovable.app)** · [About & Metrics](https://query-doc-master.lovable.app/about)

---

## How it works

```
Upload → Parse → Chunk (500 tokens) → Embed (OpenAI) → Store (NumPy)
                                                              ↓
Question → Embed → Cosine similarity search (top 15) → GPT-4o-mini → Answer + citations
```

1. Your document is parsed and split into 500-token chunks with 100-token overlap
2. Each chunk is embedded using OpenAI `text-embedding-3-small`
3. Your question is matched against chunks using cosine similarity
4. GPT-4o-mini generates an answer grounded only in the top 15 relevant chunks
5. Every claim includes a citation (page, paragraph, or row reference)

## Evaluation results

| Metric | Score |
|--------|-------|
| Factual Accuracy | 87.5% |
| Hallucination Rate | 0% |
| Citation Accuracy | 75% |
| Median Latency | 8.5s |

Evaluated on 8 structured test questions across PDF, TXT, and CSV formats. Full eval report: [`docs/EVAL-REPORT.md`](docs/EVAL-REPORT.md)

## Tech stack

| Component | Technology |
|-----------|-----------|
| LLM | GPT-4o-mini (OpenAI) |
| Embeddings | text-embedding-3-small (OpenAI) |
| Vector store | NumPy cosine similarity (in-memory) |
| Backend | FastAPI (Python) |
| Frontend | React + Tailwind (Lovable) |
| Backend hosting | Render ($7/mo) |

## Local setup

```bash
# Clone and setup
git clone https://github.com/Mehdibargach/docuquery-ai.git
cd docuquery-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-api.txt

# Add API keys
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Run
uvicorn api:app --host 0.0.0.0 --port 8000
```

API endpoints:
- `GET /health` — health check
- `POST /upload` — upload a document (multipart/form-data)
- `POST /query` — ask a question (`{"question": "..."}`)

## Project structure

```
api.py              ← FastAPI backend (3 endpoints)
app.py              ← Streamlit app (original prototype, still works)
rag/
  parser.py         ← File routing: TXT, PDF, CSV
  chunker.py        ← 500-token chunks with page mapping
  embedder.py       ← OpenAI embeddings
  store.py          ← NumPy cosine similarity search
  generator.py      ← GPT-4o-mini answer generation with citations
docs/
  BUILD-WALKTHROUGH-*.md  ← Didactic walkthroughs for each scope
  BUILD-LOG.md            ← Full build log with decisions
  EVAL-REPORT.md          ← Evaluation results and methodology
tests/
  test_sample.pdf   ← 59-page test document
  test_sample.csv   ← 25-row test dataset
  test_doc.txt      ← Text test document
```

## Built by

**Mehdi Bargach** — Senior Product Manager · 10+ years at Disney, TF1+, TotalEnergies

[LinkedIn](https://www.linkedin.com/in/mehdibargach/)
