# DocuQuery AI

## What this project is
RAG-powered Q&A system. Upload documents, ask questions in natural language, get answers with exact citations.

## Architecture Decisions (from 1-Pager)
- **LLM**: GPT-4o-mini (OpenAI) — answer generation (~20x cheaper than Claude Sonnet)
- **Embeddings**: text-embedding-3-small (OpenAI) — $0.02/1M tokens
- **Vector Store**: numpy-based in-memory cosine similarity (replaced ChromaDB — SQLite issues on iCloud)
- **Chunking**: 500 tokens, 100 token overlap
- **UI**: Streamlit (Walking Skeleton + Scopes 1-2), Lovable (Scope 3)
- **File types**: TXT (Walking Skeleton), then PDF + CSV (Scope 1)

## Current Phase
SHIP — Scope 3 complete (FastAPI + Render + Lovable). 26/26 micro-tests PASS. Product deployed and demo-ready.

## Live URLs
- **App**: https://docuqueryai.lovable.app (React/Tailwind, dark-first)
- **Backend**: https://docuquery-ai-5rfb.onrender.com (FastAPI, Render Starter $7/mo)
- **GitHub**: https://github.com/Mehdibargach/docuquery-ai (public)

## Riskiest Assumption
"A RAG pipeline with 500-token chunks and cosine similarity search can provide accurate, precisely cited answers from 50+ page documents."

## Anti-patterns
- NEVER decompose into backend → frontend → integration
- Always vertical slices (Walking Skeleton → Scopes)

## Build Rules (post-Scope 1 retro)

### 1. Micro-test = gate, pas une étape
Ordre obligatoire : Code → Micro-test PASS → Doc (avec résultats) → Commit.
Aucun commit tant que le micro-test n'est pas PASS.

### 2. Le gameplan fait autorité sur les données de test
Si le gameplan dit "50-page PDF", c'est 50 pages. Pas de raccourci sur la taille/réalisme des données de test.

### 3. Checklist qualité walkthrough
Chaque BUILD-WALKTHROUGH doit vérifier TOUS ces critères :
- [ ] Chaque concept nouveau expliqué depuis zéro
- [ ] Code annoté ligne par ligne (pas en blocs)
- [ ] Au moins 3 analogies accessibles pour non-tech
- [ ] Section "What went wrong" (même si rien n'a cassé)
- [ ] Section "Micro-test results" avec tableau PASS/FAIL
- [ ] Diagramme d'architecture complet mis à jour
- [ ] "Why not" explicite pour chaque alternative rejetée

### 4. Pas de mode batch
Exécution séquentielle avec validation à chaque phase (code prêt → micro-test passé → doc écrite). Ne pas tout livrer d'un coup.
