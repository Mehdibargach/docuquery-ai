# DocuQuery AI - Architecture

> This is a technical reference document. It describes HOW the system works (components).
> For WHAT we're building and WHY, see the [Builder PM 1-Pager](BUILDER-PM-1-PAGER.md).
> For the BUILD order (vertical slices, not components), see the [BUILD Gameplan](BUILD-GAMEPLAN.md).

## System Design

### High-Level Flow

```
┌─────────────┐
│   User UI   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Upload Service │  ← PDF/TXT/CSV
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Document Parser │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Chunking     │  ← Smart text splitting
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Embeddings    │  ← OpenAI/Cohere
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Vector DB     │  ← ChromaDB
└────────┬────────┘
         │
         │ (Query Time)
         ▼
┌─────────────────┐
│ Semantic Search │  ← Find relevant chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Generator  │  ← GPT-4o-mini
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Answer + Cites  │
└─────────────────┘
```

## Components

### 1. Document Processing Pipeline

**Input**: PDF, TXT, CSV
**Output**: Structured chunks with metadata

**Steps**:
- Extract text from document
- Clean and normalize
- Split into chunks (500 tokens, 100 token overlap)
- Add metadata (page #, doc ID, timestamp)

### 2. Embedding & Indexing

**Embedding Model**: `text-embedding-3-small` (OpenAI)
- Dimension: 1536
- Cost: $0.02 / 1M tokens

**Vector DB**: ChromaDB (local)
- Index type: Cosine similarity
- Top-k retrieval: 5 chunks

### 3. Retrieval System

**Query Process**:
1. User query → Embed query
2. Semantic search in vector DB
3. Retrieve top 5 most relevant chunks
4. Rerank (optional, using cross-encoder)

### 4. Answer Generation

**LLM**: GPT-4o-mini (OpenAI) — switched from Claude Sonnet for cost optimization (~20x cheaper)

**Prompt Template**:
```
You are a helpful AI assistant. Answer the user's question based ONLY on the provided context.

Context:
{retrieved_chunks}

Question: {user_question}

Instructions:
- Answer concisely and accurately
- Cite specific passages using [Source: page X]
- If the answer is not in the context, say "I don't have enough information"

Answer:
```

**Output**: Structured answer with citations

## Tech Stack Rationale

### Why GPT-4o-mini?
- ~20x cheaper than Claude Sonnet ($0.15/$0.60 vs $3/$15 per M tokens)
- Good enough quality for document Q&A with structured prompts
- Same provider as embeddings (OpenAI) = single API key, simpler billing
- Originally Claude Sonnet — switched post-SHIP for cost optimization

### Why ChromaDB only?
- Free, local, no account/API key needed
- Good enough for MVP (single-user, moderate doc volume)
- Reduces infrastructure complexity
- Upgrade path to Pinecone exists if needed post-MVP

### Why FastAPI?
- Async support (important for LLM calls)
- Auto-generated OpenAPI docs
- Type safety with Pydantic

## Performance Considerations

### Latency Breakdown
- Document upload: ~2-5s (depends on size)
- Chunking: ~0.5s
- Embedding: ~1-2s (batch processing)
- Vector search: ~50ms
- LLM generation: ~3-5s
- **Total query time**: ~5-8s

### Optimization Strategies
1. **Cache embeddings** for repeated queries
2. **Batch process** multiple chunks
3. **Streaming responses** from LLM
4. **Parallel retrieval** for multi-doc queries

## Security

- API keys in `.env` (never committed)
- CORS restrictions
- Rate limiting on endpoints
- Document storage: S3 with signed URLs
- No PII in logs

## Future Enhancements

1. **Hybrid Search**: Combine semantic + keyword search
2. **Multi-modal**: Support images/tables in PDFs
3. **Conversational**: Memory across queries
4. **Evaluation**: RAGAS metrics for RAG quality
