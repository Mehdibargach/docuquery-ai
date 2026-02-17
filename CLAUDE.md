# DocuQuery AI

## What this project is
RAG-powered Q&A system. Upload documents, ask questions in natural language, get answers with exact citations.

## Architecture Decisions (from 1-Pager)
- **LLM**: Claude Sonnet (Anthropic) — answer generation
- **Embeddings**: text-embedding-3-small (OpenAI) — $0.02/1M tokens
- **Vector Store**: numpy-based in-memory cosine similarity (replaced ChromaDB — SQLite issues on iCloud)
- **Chunking**: 500 tokens, 100 token overlap
- **UI**: Streamlit (Walking Skeleton + Scopes 1-2), Lovable (Scope 3)
- **File types**: TXT (Walking Skeleton), then PDF + CSV (Scope 1)

## Current Phase
BUILD — Walking Skeleton (TXT only, minimal Streamlit UI, end-to-end)

## Riskiest Assumption
"A RAG pipeline with 500-token chunks and cosine similarity search can provide accurate, precisely cited answers from 50+ page documents."

## Anti-patterns
- NEVER decompose into backend → frontend → integration
- Always vertical slices (Walking Skeleton → Scopes)
