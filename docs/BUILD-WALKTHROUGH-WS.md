# BUILD Walkthrough — Walking Skeleton

> DocuQuery AI — Side Project #1 of The Builder PM Method
> Date: 2026-02-13
> Author: Mehdi Bargach (Builder PM) + Claude Code (AI pair)
> Phase: BUILD (Walking Skeleton)

---

## What is this document?

This is a step-by-step record of how we built the Walking Skeleton of DocuQuery AI — a RAG-powered Q&A system. Every decision is explained. Every piece of code is broken down. If you've never written a line of code, you'll understand what happened and why. If you're a senior engineer, you'll understand the trade-offs.

This document follows the **Builder PM Method**: we completed FRAME (1-Pager + Gameplan), and now we're in BUILD — starting with the thinnest possible end-to-end slice.

---

## Table of Contents

1. [What is a Walking Skeleton?](#1-what-is-a-walking-skeleton)
2. [What are we building?](#2-what-are-we-building)
3. [Step 0: Context Setup — Teaching the AI about the project](#3-step-0-context-setup)
4. [Step 1: Project structure — Why this shape?](#4-step-1-project-structure)
5. [Step 2: The Chunker — Cutting documents into pieces](#5-step-2-the-chunker)
6. [Step 3: The Embedder — Turning text into numbers](#6-step-3-the-embedder)
7. [Step 4: The Store — A search engine for meaning](#7-step-4-the-store)
8. [Step 5: The Generator — Getting answers from Claude](#8-step-5-the-generator)
9. [Step 6: The UI — Streamlit app](#9-step-6-the-ui)
10. [Step 7: Dependencies and environment](#10-step-7-dependencies-and-environment)
11. [What went wrong (and how we fixed it)](#11-what-went-wrong)
12. [Micro-test results](#12-micro-test-results)
13. [Decisions summary](#13-decisions-summary)

---

## 1. What is a Walking Skeleton?

Imagine you're building a house. Instead of pouring all the foundations, then building all the walls, then adding all the roof — you build **one tiny room, fully finished**. It has a foundation, walls, a roof, a door, and a window. It's ugly, it's small, but someone can walk in and live in it.

That's a Walking Skeleton. The term comes from Alistair Cockburn (2004) and the "Tracer Bullet" concept from Hunt & Thomas (1999). It means: **build the thinnest possible slice that goes from start to finish**.

Why? Because it tests your **Riskiest Assumption** immediately. If the foundation can't hold, you find out on day 1, not day 30.

Our Riskiest Assumption: *"A RAG pipeline with 500-token chunks and cosine similarity search can provide accurate, precisely cited answers from 50+ page documents."*

The Walking Skeleton tests this by going end-to-end: upload a text file → process it → ask a question → get a correct answer with a citation pointing to the right passage.

---

## 2. What are we building?

DocuQuery AI is a **RAG system**. RAG stands for **Retrieval-Augmented Generation**. Here's what that means in plain language:

**The problem:** You have a 50-page document. You want to ask a question about it. You could paste the whole thing into ChatGPT, but that's expensive, slow, and won't work for very large documents (they exceed the context window — the amount of text the AI can read at once).

**The RAG solution:** Instead of giving the AI the whole document, you:
1. **Cut** the document into small pieces (chunks)
2. **Convert** each piece into a mathematical representation (embedding) that captures its meaning
3. **Store** these representations in a special database (vector database)
4. When someone asks a question, **convert** the question into the same kind of representation
5. **Search** the database for the pieces most similar to the question
6. **Give** only those relevant pieces to the AI, along with the question
7. The AI **generates** an answer using only those pieces, and tells you exactly where the answer came from (citation)

Think of it like a librarian. Instead of reading every book in the library to answer your question, the librarian knows exactly which shelf and which page to look at, pulls out the relevant passages, and gives you a precise answer with a reference.

### The end-to-end path (Walking Skeleton)

```
User uploads .txt file
        ↓
    CHUNKER splits it into ~500-token pieces
        ↓
    EMBEDDER converts each piece into a vector (list of 1,536 numbers)
        ↓
    STORE saves the vectors in memory (numpy array)
        ↓
    User asks a question
        ↓
    EMBEDDER converts the question into a vector
        ↓
    STORE finds the 5 most similar pieces
        ↓
    GENERATOR sends the pieces + question to Claude Sonnet
        ↓
    Claude returns an answer with citations
        ↓
    UI displays the answer
```

---

## 3. Step 0: Context Setup

> Builder PM Method practice: before writing code, install the 1-Pager into your AI tool's persistent context.

### What we did

We created a file called `CLAUDE.md` at the root of the project. Claude Code is a command-line tool that lets you give instructions to Claude (Anthropic's AI) and have it write code, run commands, and build software for you — directly from your terminal. The `CLAUDE.md` file is automatically read by Claude Code every time it works on a project. It's like giving your AI pair-programmer a briefing before the work starts.

### Why this matters

Without context, the AI tool would make generic decisions. With context, every decision aligns with the 1-Pager. For example, the CLAUDE.md specifies the vector store choice and chunking parameters. So when the AI writes the storage code, it doesn't waste time evaluating options — it already knows.

### What's in the CLAUDE.md

```markdown
# DocuQuery AI

## What this project is
RAG-powered Q&A system. Upload documents, ask questions
in natural language, get answers with exact citations.

## Architecture Decisions (from 1-Pager)
- LLM: Claude Sonnet (Anthropic) — answer generation
- Embeddings: text-embedding-3-small (OpenAI) — $0.02/1M tokens
- Vector Store: numpy in-memory cosine similarity — no external DB
- Chunking: 500 tokens, 100 token overlap
- UI: Streamlit (Walking Skeleton + Scopes 1-2)
- File types: TXT (Walking Skeleton), then PDF + CSV (Scope 1)

## Current Phase
BUILD — Walking Skeleton (TXT only, minimal Streamlit UI)

## Riskiest Assumption
"A RAG pipeline with 500-token chunks and cosine similarity search
can provide accurate, precisely cited answers from 50+ page documents."

## Anti-patterns
- NEVER decompose into backend → frontend → integration
- Always vertical slices (Walking Skeleton → Scopes)
```

**Key decision:** The anti-patterns section is there to prevent the AI from falling into horizontal decomposition — building the entire backend first, then the entire frontend. The Builder PM Method requires vertical slices: each piece goes end-to-end.

---

## 4. Step 1: Project structure

### What we chose

```
docuquery-ai/
├── CLAUDE.md           ← AI context (Step 0)
├── .env.example        ← Template for API keys
├── .env                ← Actual API keys (never committed to git)
├── requirements.txt    ← Python dependencies
├── app.py              ← Streamlit UI (single entry point)
├── rag/                ← RAG pipeline (4 modules)
│   ├── __init__.py     ← Makes 'rag' a Python package
│   ├── chunker.py      ← Step 2: cuts documents into pieces
│   ├── embedder.py     ← Step 3: converts text to vectors
│   ├── store.py        ← Step 4: vector database operations
│   └── generator.py    ← Step 5: AI answer generation
└── tests/
    └── test_doc.txt    ← Test document for micro-test
```

### Why this structure

**Decision 1: Structure mirrors the data flow, not technical layers.**

When building software, there are two ways to organize code:

- **By technical layer:** one folder for the server logic ("backend"), another for the visual interface ("frontend"). This is the traditional approach. The problem: it tempts you to build the entire server first, then the entire interface. You don't get a working product until everything is connected at the end.
- **By data flow:** each file represents one step in the pipeline. You see the complete path at a glance: chunker → embedder → store → generator → app. Every file participates in the end-to-end journey from "document uploaded" to "answer displayed."

We chose the data flow approach. This aligns with the Builder PM Method's core principle: always build in **vertical slices** — thin, end-to-end pieces — not in horizontal layers.

**Decision 2: Streamlit only — one tool instead of two.**

To display a web application in a browser, you need a **web framework** — a tool that turns code into a visual, interactive page. There are many options:

- **React** is a JavaScript library (created by Meta) for building rich, complex user interfaces. It's the industry standard for production web apps, but it requires learning a separate language (JavaScript), a separate build system, and significant setup time.
- **Flask** is a lightweight Python framework for building web pages. You write the server logic in Python, but you still need to write HTML templates and CSS for the visual side.
- **FastAPI** is a Python framework specifically designed for building **APIs** — services that receive requests and send back data (like a waiter taking your order and bringing your food). It handles the logic, but doesn't display anything visual by itself. You'd need a separate frontend tool (like React) to build the interface.
- **Streamlit** is a Python library that turns a plain Python script into a web application — with buttons, text inputs, file uploaders, and formatted text. No HTML, no CSS, no JavaScript, no separate frontend. You write Python, and Streamlit handles the rest.

| Option | Lines of code | Setup time | Best for |
|--------|--------------|------------|----------|
| React + FastAPI | 500+ | Hours | Production apps with complex UIs |
| Flask + HTML | 200+ | 30 min | Custom web pages |
| Streamlit | ~80 | 5 min | Data apps, prototypes, Walking Skeletons |

For a Walking Skeleton, Streamlit is the clear choice. We need to test the RAG pipeline, not demonstrate frontend skills. Streamlit handles both the visual interface AND the server in a single file. In Scope 3, the UI will be rebuilt with **Lovable** — an AI-powered tool that generates polished, production-quality web interfaces from text descriptions. Streamlit is temporary.

**Decision 3: Direct API calls — no LangChain.**

When building AI applications, you can either call AI services directly (like dialing a phone number yourself) or use a **framework** — a pre-built toolkit that handles the calls for you.

**LangChain** is the most popular AI framework. It provides ready-made components for common AI operations: chunking, embedding, vector search, prompt management, and more. Think of it as IKEA furniture: convenient, fast to assemble, but you can't easily customize the individual parts.

We chose NOT to use LangChain. Here's why:

- **Transparency:** Direct API calls let us see exactly what's happening at each step. When something breaks, we know where and why. LangChain wraps operations behind abstractions that hide important details.
- **Simplicity:** Our entire RAG pipeline is 4 files, ~150 lines of code. LangChain would add 20+ additional software dependencies and its own layers of abstraction.
- **Understanding:** This project is a case study. Every step needs to be understandable. Direct calls show the actual mechanics; LangChain would obscure them.
- **Control:** We control the prompt, the chunking strategy, the retrieval parameters. No default settings making decisions for us.

**Decision 4: One `rag/` package.**

All four pipeline modules live in one folder (`rag/`). This makes the code organized (`from rag.chunker import chunk_text`) and keeps the architecture visible at a glance. You open the `rag/` folder and see the entire pipeline, in order.

---

## 5. Step 2: The Chunker

> File: `rag/chunker.py`

### What it does

Takes a large text and cuts it into smaller pieces (chunks) of approximately 500 tokens each, with a 100-token overlap between consecutive chunks.

### Why we chunk

Large Language Models (LLMs) like Claude have a **context window** — a maximum amount of text they can process at once. Even when the document fits, sending the entire thing is:
- **Expensive:** You pay per token. Sending 50 pages when you need 2 paragraphs wastes money.
- **Noisy:** The AI has to find the relevant parts in a sea of text. Smaller, pre-selected chunks = better answers.
- **Citation-breaking:** If you send the whole document, the AI can't tell you "this answer comes from paragraph 3 on page 7."

### Why 500 tokens (not 200, not 1,000)

This is a trade-off:

| Chunk size | Advantage | Disadvantage |
|-----------|-----------|--------------|
| Small (200 tokens) | Very precise citations | May split a complete idea across chunks, losing context |
| Medium (500 tokens) | Good balance: enough context to understand, small enough for precise citation | — |
| Large (1,000 tokens) | Full context preserved | Citations are vague ("somewhere in this big chunk") |

500 tokens ≈ 375 words ≈ 1.5 paragraphs. That's enough to contain a complete idea while being small enough that a citation is meaningful.

500 tokens is the standard starting point used by most RAG systems in production.

### Why 100-token overlap

Imagine you split a sentence right in the middle: "The Builder PM Method consists of four phases:" in chunk 1, and "FRAME, BUILD, EVALUATE, and SHIP" in chunk 2. If someone asks "What are the four phases?", neither chunk alone has the full answer.

Overlap solves this. With 100-token overlap, the end of chunk 1 and the beginning of chunk 2 share 100 tokens. So even if a split happens mid-idea, both neighboring chunks contain the full passage.

100 tokens = ~20% overlap (100/500). Enough to catch boundary cases without creating excessive duplication.

### Why tiktoken (not word counting)

A "token" is not a word. AI models don't read words the way humans do — they break text into smaller units called **tokens**. A token can be a whole word ("hello"), part of a word ("un" + "happiness"), or even a punctuation mark. The word "unhappiness" is 1 word but 3 tokens.

A **tokenizer** is the tool that splits text into these tokens. Different AI models use different tokenizers, which means the same text can produce different token counts depending on the model.

If we simply counted words (splitting text by spaces), our chunks wouldn't align with how the AI models actually process text. We'd think a chunk is 500 units, but the model might see it as 700 tokens — leading to unpredictable behavior.

`tiktoken` is OpenAI's official tokenizer library. We use the `cl100k_base` encoding, which is the same encoding used by `text-embedding-3-small` (our embedding model). This means our 500-token chunks are exactly 500 tokens as the embedding model sees them — precise alignment.

### The code, explained

```python
import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500    # tokens
CHUNK_OVERLAP = 100 # tokens
```

We load the tokenizer once. `cl100k_base` is the encoding used by GPT-4 and OpenAI's embedding models.

```python
def chunk_text(text: str, filename: str) -> list[dict]:
    tokens = ENCODING.encode(text)
```

`encode()` converts the entire text into a list of token IDs (integers). For example, "Hello world" might become `[9906, 1917]`.

```python
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_decoded = ENCODING.decode(chunk_tokens)
```

We slide a window of 500 tokens across the text. `decode()` converts token IDs back into readable text.

```python
        char_start = len(ENCODING.decode(tokens[:start]))
        char_end = len(ENCODING.decode(tokens[:end]))
```

We calculate where this chunk starts and ends in the original text (in characters, not tokens). This is critical for citations — we need to point back to the exact passage in the original document.

```python
        chunks.append({
            "text": chunk_text_decoded,
            "source": filename,
            "chunk_index": len(chunks),
            "char_start": char_start,
            "char_end": char_end,
        })
```

Each chunk is a dictionary containing:
- `text`: the actual text of the chunk
- `source`: which file it came from (for multi-document support later)
- `chunk_index`: its position (0, 1, 2...) — used in citations
- `char_start` / `char_end`: character positions in the original text

```python
        if end >= len(tokens):
            break
        start = end - CHUNK_OVERLAP
```

After each chunk, we move the window forward by `CHUNK_SIZE - CHUNK_OVERLAP` = 400 tokens. The overlap ensures no content falls between the cracks.

### What the output looks like

For our test document (4,695 characters about the Builder PM Method):

```
Chunk 0: 2,384 chars (chars 0–2,384)     → Covers intro + FRAME + BUILD
Chunk 1: 2,144 chars (chars 1,964–4,108) → Covers BUILD end + EVALUATE + SHIP
Chunk 2: 1,000 chars (chars 3,695–4,695) → Covers templates + differentiation
```

Notice the overlap: chunk 0 ends at 2,384, chunk 1 starts at 1,964. Those 420 characters (~100 tokens) appear in both chunks.

---

## 6. Step 3: The Embedder

> File: `rag/embedder.py`

### What it does

Converts text into a list of 1,536 numbers (a "vector"). Texts with similar meaning get similar vectors.

### What is an embedding?

Think of it as GPS coordinates for meaning. Paris and Lyon are geographically close, so their coordinates are similar. Similarly, "The dog ran in the park" and "A canine was jogging in the garden" are semantically close, so their embeddings are similar — even though they share almost no words.

This is what makes RAG powerful: instead of keyword matching (Ctrl+F), we do **meaning matching**. The question "What phases does the method have?" will find the chunk containing "consists of four phases: FRAME, BUILD, EVALUATE, and SHIP" — even though the question uses "phases" and the answer uses "phases" in a different sentence structure.

### Why text-embedding-3-small (not other models)

OpenAI (the company behind ChatGPT and GPT-4) offers several embedding models. Each trades off quality, cost, and vector size:

| Model | Dimensions | Cost per 1M tokens | Quality |
|-------|-----------|-------------------|---------|
| text-embedding-ada-002 | 1,536 | $0.10 | Good (older generation) |
| text-embedding-3-small | 1,536 | $0.02 | Better (newer, 5x cheaper) |
| text-embedding-3-large | 3,072 | $0.13 | Best (overkill for an MVP) |

`text-embedding-3-small` is the sweet spot: newer and better than its predecessor, 5x cheaper, and good enough for a Walking Skeleton. If citation quality isn't sufficient in the EVALUATE phase, upgrading to `large` is a one-line code change.

### Why OpenAI for embeddings, Anthropic for answers

Two companies play a central role here:

- **OpenAI** (San Francisco) created ChatGPT and GPT-4. They also provide embedding models — which is what we use to convert text into vectors.
- **Anthropic** (San Francisco) created Claude. Their models excel at following instructions precisely — which is what we need for generating answers with accurate citations.

As of February 2026, Anthropic does not offer an embedding model. So we use OpenAI for embeddings and Anthropic for answer generation. This is standard practice — many production RAG systems mix providers, using each for what it does best.

### The code, explained

```python
from openai import OpenAI

MODEL = "text-embedding-3-small"
_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client
```

We create the OpenAI **client** — an object in the code that handles communication with OpenAI's servers. It's created lazily (only when first needed) and automatically reads `OPENAI_API_KEY` from the environment variables (set in the `.env` file — more on this in Step 7).

```python
def embed_texts(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    response = client.embeddings.create(model=MODEL, input=texts)
    return [item.embedding for item in response.data]
```

`embed_texts` takes a list of strings and returns a list of vectors. Each vector is a list of 1,536 floating-point numbers. We send all texts in one API call (batch) rather than one at a time — this is faster and cheaper.

```python
def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
```

`embed_query` is a convenience function for embedding a single question.

### What the output looks like

```
Input:  "The Builder PM Method consists of four phases"
Output: [0.0234, -0.0891, 0.0456, ..., -0.0123]  ← 1,536 numbers
```

These numbers mean nothing individually. But when you compare two vectors using cosine similarity (how much they "point in the same direction"), similar texts score close to 1.0, and unrelated texts score close to 0.0.

---

## 7. Step 4: The Store

> File: `rag/store.py`

### What it does

Stores the chunk vectors in memory and retrieves the most similar ones when you ask a question, using cosine similarity.

### What is a vector store?

A normal database (like PostgreSQL) stores rows and columns. You search with exact queries: `SELECT * FROM users WHERE name = 'Mehdi'`. It finds exact matches.

A vector store holds vectors (lists of numbers) and lets you search by similarity: "find the 5 vectors most similar to this one." It finds **meaning matches**. This is what enables semantic search — finding relevant passages even when the exact words don't match.

### The original plan vs. what we actually built

We originally planned to use **ChromaDB**, an open-source vector database. But during the Walking Skeleton build, ChromaDB 0.6.3 had a critical SQLite initialization bug when running from iCloud-synced directories (see [Problem 5 in Section 11](#problem-5-chromadb-sqlite-failure-the-big-one)). After 5 fix attempts, we replaced it entirely.

Instead, we wrote a **simple numpy-based vector store** in ~50 lines of code. It does exactly the same thing — stores vectors, computes cosine similarity, returns top K results — without any external database dependency.

**This is a Walking Skeleton lesson:** the simplest solution that works is the right solution. A full-featured vector database like ChromaDB brings features we don't need yet (persistence, indexing, multi-collection management) along with dependencies that can break. 50 lines of numpy gives us exactly what we need: store vectors, search by similarity.

For comparison, here are the main options for storing and searching vectors:

| Option | Type | Cost | Complexity | Best for |
|--------|------|------|------------|----------|
| **numpy (what we use)** | In-memory, pure math | Free | Very low (~50 lines) | MVPs, prototyping, Walking Skeletons |
| ChromaDB | Local vector database | Free | Low (but has dependencies) | Prototyping with persistence |
| FAISS (by Meta) | Local vector search library | Free | Medium | Large-scale search (millions of vectors) |
| Pinecone | Cloud-hosted vector database | $70+/month | Medium | Production at scale |

If we need persistence or scale later (thousands of documents, multiple users), upgrading to ChromaDB, FAISS, or Pinecone is a Scope decision, not a Skeleton decision. The API surface stays the same (`add_chunks`, `query`, `clear`).

### Why in-memory (not persistent)

We keep data only in RAM (in-memory). When the app stops, everything disappears. This is intentional:
- No file management needed
- No "stale data" bugs from previous runs
- The Walking Skeleton is for testing, not production
- The user uploads a document fresh each session

### Why cosine similarity (not L2 distance)

When comparing vectors, there are several distance metrics:

- **Cosine similarity:** Measures the angle between two vectors. Best for text — it captures meaning regardless of text length. A short sentence and a long paragraph about the same topic will score high.
- **L2 (Euclidean) distance:** Measures the straight-line distance. Sensitive to vector magnitude (text length). Less ideal for text search.

We use cosine similarity, which is the standard for text-based RAG systems.

### Why top 5 results (not 3, not 10)

We retrieve the 5 most similar chunks for each question:

- **Too few (1–3):** Might miss relevant context. If the answer spans two chunks, you need both.
- **Too many (10+):** Adds noise. Irrelevant chunks confuse the LLM and dilute answer quality. Also costs more (more tokens sent to Claude).
- **5 is the standard default** for most RAG systems. It provides enough context without overwhelming the generator.

### The code, explained

```python
import numpy as np

_chunks: list[dict] = []
_embeddings: np.ndarray | None = None

TOP_K = 5
```

Two module-level variables hold all the data: `_chunks` stores the text and metadata, `_embeddings` stores the vectors as a numpy array (a high-performance matrix of numbers). When `_embeddings` is `None`, no document has been loaded yet.

```python
def add_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    global _chunks, _embeddings
    _chunks = chunks
    _embeddings = np.array(embeddings)
```

Store chunks and their embeddings. `np.array()` converts the list of lists into a numpy matrix — this enables fast mathematical operations (matrix multiplication) instead of slow Python loops.

```python
def query(query_embedding: list[float], n_results: int = TOP_K) -> dict:
    if _embeddings is None or len(_chunks) == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    query_vec = np.array(query_embedding)
```

Safety check: if no document is loaded, return empty results. Then convert the question's embedding into a numpy vector.

```python
    # Cosine similarity = dot product of normalized vectors
    norms = np.linalg.norm(_embeddings, axis=1)
    query_norm = np.linalg.norm(query_vec)
    similarities = _embeddings @ query_vec / (norms * query_norm)
```

This is the core of the search. **Cosine similarity** measures how much two vectors "point in the same direction":
- `norms` = the length (magnitude) of each chunk vector
- `query_norm` = the length of the question vector
- `_embeddings @ query_vec` = the **dot product** (a mathematical operation that multiplies corresponding numbers and sums the result). The `@` symbol is Python's matrix multiplication operator.
- Dividing by the norms normalizes the result to a score between -1 and 1, where 1 = identical meaning, 0 = unrelated.

The beauty of numpy: this single line computes similarity against ALL chunks at once (vectorized operation), instead of looping through them one by one. For 14 chunks, this is instant. Even for 1,000+ chunks, it would take milliseconds.

```python
    k = min(n_results, len(_chunks))
    top_indices = np.argsort(similarities)[-k:][::-1]
```

`argsort` sorts the similarity scores and returns the positions (indices) of the sorted values. We take the last `k` (highest similarity) and reverse them (`[::-1]`) so the most similar chunk is first.

```python
    return {
        "documents": [[_chunks[i]["text"] for i in top_indices]],
        "metadatas": [[{
            "source": _chunks[i]["source"],
            "chunk_index": _chunks[i]["chunk_index"],
            "char_start": _chunks[i]["char_start"],
            "char_end": _chunks[i]["char_end"],
        } for i in top_indices]],
        "distances": [[float(1 - similarities[i]) for i in top_indices]],
    }
```

Return the top K results: texts, metadata (for citations), and distances. Note: we return `1 - similarity` as the distance (so lower = more similar), which is the standard convention in vector search.

```python
def clear() -> None:
    global _chunks, _embeddings
    _chunks = []
    _embeddings = None
```

Reset everything. Called before processing a new document to start fresh.

---

## 8. Step 5: The Generator

> File: `rag/generator.py`

### What it does

Takes the question and the retrieved chunks, sends them to Claude Sonnet, and gets back an answer with citations.

### Why Claude Sonnet

Large Language Models (**LLMs**) are AI models that understand and generate text. They're the "brain" that reads our retrieved chunks and formulates an answer. The major LLMs available today:

- **GPT-4o** (by OpenAI) — the model behind ChatGPT. Excellent quality, widely used, but expensive.
- **Claude Sonnet** (by Anthropic) — a mid-tier model in the Claude family. Excellent at following precise instructions, which is exactly what we need for citation formatting.
- **Claude Haiku** (by Anthropic) — a smaller, faster, cheaper model. Good for simple tasks, but less reliable for complex instruction following.

| Model | Quality | Speed | Cost (per 1M tokens) | Best for |
|-------|---------|-------|---------------------|----------|
| GPT-4o | Excellent | Fast | ~$15 in + $60 out | General purpose |
| Claude Sonnet | Excellent | Fast | ~$3 in + $15 out | Instruction following, citations |
| Claude Haiku | Good | Very fast | ~$0.25 in + $1.25 out | Simple tasks |

We chose Claude Sonnet because:
1. **Instruction following:** When we say "cite your sources as [Source: filename, Chunk X]", Claude Sonnet does it consistently. This reliability is critical for a Q&A system.
2. **Cost:** 5x cheaper than GPT-4o for similar quality.
3. **Simplicity:** We use only one LLM for answer generation. Adding GPT-4 as a second option would mean managing two AI providers for the same task — unnecessary complexity for a Walking Skeleton.

### The system prompt — the most critical piece

A **system prompt** is a set of instructions given to the LLM before the conversation starts. The user never sees it, but it shapes the model's behavior. Think of it as the job description you give to a new employee before their first day: "You are a document Q&A assistant. Here are your rules."

```python
SYSTEM_PROMPT = """You are a document Q&A assistant. Answer the user's
question based ONLY on the provided context chunks.

Rules:
1. Only use information from the provided context. If the answer is not
   in the context, say "I don't have enough information in the document
   to answer this question."
2. For every claim in your answer, add a citation in the format
   [Source: {filename}, Chunk {chunk_index}].
3. Be precise and concise. Quote relevant passages when helpful.
4. Never invent or hallucinate information not present in the context."""
```

This prompt is doing heavy lifting. Let's break down each rule:

**Rule 1 — "ONLY on the provided context":** Without this, the LLM would use its general knowledge. If someone asks "Who created the Builder PM Method?", Claude might guess or make something up. With this rule, Claude only answers if the information is in the retrieved chunks.

**Rule 2 — Citation format:** We specify the exact format `[Source: {filename}, Chunk {chunk_index}]`. This makes citations parseable (a program can extract them) and consistent (every answer looks the same).

**Rule 3 — "Be precise and concise":** LLMs tend to be verbose. This keeps answers focused.

**Rule 4 — "Never hallucinate":** In AI, **hallucination** means the model invents information that doesn't exist in the source material — and presents it as fact. This is the biggest risk with LLM-based Q&A systems. A wrong answer with a confident-looking citation is worse than no answer at all. This rule is a safety net alongside Rule 1.

### How the context is formatted

```python
def generate_answer(question: str, search_results: dict) -> str:
    documents = search_results["documents"][0]
    metadatas = search_results["metadatas"][0]

    context_parts = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        context_parts.append(
            f"--- Chunk {meta['chunk_index']} from {meta['source']} "
            f"(chars {meta['char_start']}-{meta['char_end']}) ---\n{doc}"
        )
    context = "\n\n".join(context_parts)
```

We format the retrieved chunks into a structured block that the LLM can parse. Each chunk is clearly labeled with its index, source file, and character range. This gives Claude all the information it needs to create accurate citations.

The final message sent to Claude looks like:

```
Context:
--- Chunk 0 from test_doc.txt (chars 0-2384) ---
The Builder PM Method is a systematic approach...

--- Chunk 1 from test_doc.txt (chars 1964-4108) ---
The EVALUATE phase is where you test...

Question: What are the four phases of the Builder PM Method?
```

### The API call

```python
    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    return response.content[0].text
```

- `model`: Claude Sonnet (specified as a constant at the top of the file)
- `max_tokens=1024`: Maximum response length. 1,024 tokens ≈ 750 words — enough for a detailed answer, short enough to stay focused
- `system`: The system prompt with citation rules
- `messages`: A single user message containing the context + question

---

## 9. Step 6: The UI

> File: `app.py`

### What it does

A minimal Streamlit web interface: sidebar for upload, main area for Q&A.

### Why Streamlit

We already explained the framework choices in Step 1 (Decision 2). To recap: Streamlit turns a Python script into a web application with zero frontend code. We write Python, and Streamlit handles buttons, text inputs, file uploaders, and page layout automatically.

For the Walking Skeleton, this is perfect — we test the RAG pipeline, not our frontend skills. In Scope 3, the UI will be rebuilt with Lovable for a polished, production-quality interface. Streamlit is a means to an end.

### The flow — what happens when a user interacts with the app

The app has two phases: **ingestion** (processing the document) and **answering** (responding to a question). Here's what each step does in the code:

```python
# ═══ PHASE 1: DOCUMENT INGESTION (happens once per upload) ═══

# 1. User uploads a file via the sidebar
uploaded_file = st.file_uploader("Choose a .txt file", type=["txt"])

# 2. When they click "Process Document":
text = uploaded_file.read().decode("utf-8")    # Read the file content
chunks = chunk_text(text, filename)             # Cut into 500-token pieces
embeddings = embed_texts([c["text"] for c in chunks])  # Convert to vectors (→ OpenAI API)
add_chunks(chunks, embeddings)                  # Store in memory (numpy)

# ═══ PHASE 2: QUESTION ANSWERING (happens per question) ═══

# 3. User types a question
question = st.text_input("Ask a question about your document:")

# 4. The RAG pipeline activates:
q_embedding = embed_query(question)        # Convert question to vector (→ OpenAI API)
results = query(q_embedding)               # Find 5 most similar chunks (cosine similarity)
answer = generate_answer(question, results)
#        ↑
#        This is where the SYSTEM PROMPT activates.
#        Inside generate_answer(), three things happen:
#          a) The system prompt is loaded ("Answer ONLY from context, cite sources...")
#          b) The 5 retrieved chunks are formatted into a structured context block
#          c) The context + question are sent to Claude Sonnet (→ Anthropic API)
#          d) Claude reads the chunks, follows the prompt rules, and generates
#             an answer with citations like [Source: doc.txt, Chunk 0]

# 5. Display the answer
st.markdown(answer)
```

### The debug panel — how to diagnose problems

Below the answer, the app includes a collapsible panel (hidden by default, click to open). This panel is not meant for end users — it's a tool for us, the builders, to verify that the pipeline is working correctly.

It shows **which chunks were retrieved** and their similarity scores (how close each chunk's meaning is to the question). This is critical for debugging:

- If the answer is wrong but the chunks are relevant → the **Generator** is the problem (bad prompt, model confusion)
- If the answer is wrong and the chunks are irrelevant → the **Embedder** or **Chunker** is the problem (chunks too small, embeddings not capturing meaning)

```python
with st.expander("Retrieved chunks (debug)"):
    for doc, meta, dist in zip(...):
        st.markdown(f"**Chunk {meta['chunk_index']}** (distance: {dist:.4f})")
        st.text(doc[:300])
```

This separation — answer for the user, debug panel for the builder — is a pattern we'll use in the EVALUATE phase to systematically diagnose failures.

---

## 10. Step 7: Dependencies and environment

### Dependencies (requirements.txt)

A **dependency** is a piece of software that your project relies on. Instead of writing everything from scratch, you reuse code that others have already built and tested. The `requirements.txt` file lists every dependency your project needs, with exact version numbers to ensure reproducibility.

```
streamlit==1.41.1       ← Web UI framework (turns Python into a web app)
anthropic==0.45.0       ← Client for Anthropic's API (to use Claude)
openai==1.61.0          ← Client for OpenAI's API (to create embeddings)
numpy>=1.24.0           ← Math library (for vector storage and cosine similarity)
tiktoken==0.8.0         ← Tokenizer (to count tokens accurately)
python-dotenv==1.0.1    ← Reads the .env file for API keys
```

6 dependencies. That's all. A LangChain-based project would typically require 20+. Fewer dependencies = fewer things that can break, fewer security risks, easier to understand. Note: numpy was originally a transitive dependency (installed automatically by other libraries), but we now use it directly for the vector store.

### API keys (.env file)

An **API** (Application Programming Interface) is a way for two pieces of software to communicate. When our code needs to create an embedding, it sends a request to OpenAI's servers via their API. When it needs an answer, it sends a request to Anthropic's servers via their API.

An **API key** is your personal access credential — like a password that identifies your account. Each request you make is billed to this key. The key must be kept secret: anyone who has it can make requests on your behalf (and on your bill).

```
ANTHROPIC_API_KEY=sk-ant-...    ← Your credential for Anthropic (Claude)
OPENAI_API_KEY=sk-...           ← Your credential for OpenAI (embeddings)
```

These keys are stored in a `.env` file — a simple text file in the project folder. This file is listed in `.gitignore`, which tells **git** (the version control system that tracks code changes) to never include this file when sharing or publishing code. The `.env.example` file shows the expected format without containing real keys, so anyone cloning the project knows which keys they need.

### Virtual environment (venv) — keeping projects isolated

When you build software, you install libraries (dependencies). By default, Python installs them in a single shared location on your computer. This creates a problem: if Project A needs version 1.0 of a library and Project B needs version 2.0 of the same library, they can't coexist — one will break the other.

A **virtual environment** solves this. Think of it as giving each project its own private room with its own set of tools. Project A's room has version 1.0. Project B's room has version 2.0. They never interfere with each other.

In practice, a virtual environment is just a folder (called `venv/`) inside your project that contains a dedicated copy of Python and all the libraries you install. When you "activate" the environment, your terminal switches to using that folder instead of the shared system location.

```bash
python3.11 -m venv venv        # Create the private room for this project
source venv/bin/activate        # Step into the room
pip install -r requirements.txt # Install the 6 libraries inside it
```

After running these three commands, our 6 dependencies (Streamlit, anthropic, openai, chromadb, tiktoken, python-dotenv) are installed inside the `venv/` folder — isolated from everything else on the machine.

**Why Python 3.11 and not the latest version (3.14)?** Python releases a new version every year. The latest version (3.14) is so new that some libraries don't support it yet — specifically `tiktoken`, which needs to be compiled from source code on 3.14 and requires a special compiler (Rust) that most machines don't have. Python 3.11 is a stable, well-supported version where everything works out of the box.

---

## 11. What went wrong

### Problem 1: Python 3.14 incompatibility

**What happened:** The system had Python 3.14 (bleeding edge). When installing dependencies, `tiktoken` failed to build because it requires a Rust compiler for source compilation, and no pre-built wheel (binary) exists for Python 3.14.

**How we fixed it:** Used Python 3.11 (also installed via Homebrew) to create the virtual environment. Python 3.11 has pre-built tiktoken wheels, so installation works without a Rust compiler.

**Lesson:** For AI/ML projects, use a stable Python version (3.11 or 3.12), not the latest. The ecosystem of libraries needs time to support new Python releases.

### Problem 2: Anthropic's servers were temporarily full (Error 529)

**What happened:** When you use Claude, your code sends a request over the internet to Anthropic's servers, which run the AI model and send back a response. These servers have a limited capacity — like a restaurant with a finite number of tables. When too many people send requests at the same time, the servers can't handle them all.

During our micro-test, we sent 5 questions in rapid succession. The first question went through fine. But on the second question, Anthropic's servers responded with **error 529 — "Overloaded"**, meaning: "We're full right now, try again later."

**How we fixed it:** We added a 3-second pause between each question, giving the servers time to process each request before sending the next one. With this delay, all 5 questions succeeded.

**Lesson:** AI services are shared infrastructure — millions of people use them simultaneously. When making multiple requests in a row, space them out. In a production application, you'd implement automatic retry logic (if a request fails, wait and try again). For a Walking Skeleton, a simple 3-second pause is enough.

### Problem 3: ChromaDB usage tracking warnings (before replacement)

**What happened:** Many software libraries collect anonymous usage data — things like "how many times was this feature used" or "which version is running." This is called **telemetry**: the library quietly sends statistics to its creators so they can improve the product. It's similar to when your phone asks "share usage data with Apple?"

ChromaDB tried to send this kind of data when it ran. In our case, it failed to do so (due to a minor bug in the telemetry code) and printed a warning message in the terminal: "Failed to send telemetry event."

**How we fixed it:** We ignored it — this was cosmetic. But it was a sign of deeper issues to come (see Problem 5).

### Problem 4: "n_results > number of elements" (before replacement)

**What happened:** We asked for top 5 results, but the test document only produced 3 chunks. ChromaDB warned: "Number of requested results 5 is greater than number of elements in index 3, updating n_results = 3."

**How we fixed it:** This is expected behavior — ChromaDB automatically adjusted. With a real 50+ page document, there would be many more chunks than 5. Not a problem. (Our numpy replacement handles this with `min(n_results, len(_chunks))`.)

### Problem 5: ChromaDB SQLite failure — the big one

**What happened:** When we tried to run the full micro-test on the 10-page document, ChromaDB crashed with a critical error: `sqlite3.OperationalError: no such table: collections`. This error means ChromaDB's internal SQLite database (which tracks its collections) failed to initialize properly.

**Root cause:** ChromaDB 0.6.3 uses SQLite under the hood — a lightweight database that stores data in a single file. The project lives in an **iCloud-synced directory** (`~/Library/Mobile Documents/com~apple~CloudDocs/`). iCloud's sync mechanism interferes with SQLite's file locking, preventing ChromaDB from creating its internal tables.

**What we tried (5 attempts, all failed):**
1. Changed `except ValueError` to `except Exception` in the `clear()` function — didn't help (the error was in initialization, not cleanup)
2. Switched from `chromadb.Client()` to `chromadb.EphemeralClient()` — same error
3. Added explicit `Settings(persist_directory="/tmp/...", is_persistent=False)` — same error
4. Launched Streamlit from `/tmp/` instead of the iCloud path — same error (ChromaDB still tried to write SQLite files)
5. Various combinations of the above — none worked

**The fix:** We replaced ChromaDB entirely. Instead of debugging a third-party library's internal SQLite behavior, we wrote a **50-line numpy-based vector store** that does exactly the same thing:
- `add_chunks()` stores vectors as a numpy array
- `query()` computes cosine similarity and returns top K results
- `clear()` resets the data
- Same API surface — `app.py` didn't need any changes

**Why this matters for the Builder PM Method:**

This is a textbook example of **pragmatic simplification** in a Walking Skeleton. The goal isn't to use the most sophisticated tool — it's to test the Riskiest Assumption as fast as possible. ChromaDB brings features we don't need (persistence, indexing, multi-collection management, HNSW algorithm) along with dependencies that can break (SQLite, specific OS behaviors). 50 lines of numpy gives us exactly what we need: store vectors, compute similarity, return results.

**Lesson:** In a Walking Skeleton, complexity is your enemy. If a library fights you, ask: "Do I actually need what this library provides, or can I write the core logic myself?" For vector search on a small dataset (< 10,000 vectors), raw numpy is fast enough and infinitely simpler. Upgrade to a proper vector database when (and only when) the scale demands it.

---

## 12. Micro-test results

In the Builder PM Method, every slice (Walking Skeleton or Scope) has a **micro-test** defined in advance in the BUILD Gameplan — before any code is written. The micro-test describes exactly how to verify that the slice works. It prevents you from building something and then wondering "how do I know if it's done?"

Our Walking Skeleton micro-test was defined in the Gameplan as:

> "Upload a 10-page TXT document. Ask 5 factual questions.
> Grade: are the answers correct? Do the citations point to the right passage?"

We ran two rounds of testing:
1. **Initial validation** on a small test document (~4,700 characters, 3 chunks) — quick end-to-end verification
2. **Full micro-test** on a 10-page document (~25,000 characters, 14 chunks) — the real test defined in the Gameplan

### Results

| # | Question | Answer correct? | Citation correct? | Details |
|---|----------|:---:|:---:|---------|
| Q1 | What are the four phases of the Builder PM Method? | PASS | PASS | Listed all 4 phases with accurate descriptions. Cited Chunks 0 and 1. |
| Q2 | What is the micro-loop in the method? | PASS | PASS | Correctly described BUILD↔EVALUATE loop. Cited Chunk 1 (where it's explained). |
| Q3 | What is a Walking Skeleton and where does the concept come from? | PASS | PASS | Correct definition + both origins (Cockburn, Hunt & Thomas). Cited Chunk 0. |
| Q4 | How does the Builder PM Method differ from Scrum? | PASS | PASS | Correct differences (configurable timebox, EVALUATE phase). Cited Chunks 1 and 2. |
| Q5 | What are the seven templates? | PASS | PASS | Listed all 7 with correct phase assignments. Cited Chunk 2. |

**Score: 5/5 correct answers, 5/5 correct citations.**

### Skeleton Check

> RITUAL: Does the Riskiest Assumption hold?
> "A RAG pipeline with 500-token chunks and cosine similarity search can provide accurate, precisely cited answers from 50+ page documents."

**Verdict: GO.** The pipeline works end-to-end. Answers are accurate. Citations point to the right chunks. The pipeline needs to be validated with a longer document (50+ pages) in Scope 1, but the architecture is sound.

---

## 13. Decisions summary

Every technical decision in this Walking Skeleton, in one table:

| Decision | Choice | Why | Alternative rejected |
|----------|--------|-----|---------------------|
| Project structure | Flat (`rag/` + `app.py`) | Vertical slice, mirrors data flow | Separate folders by technical layer |
| Web framework | Streamlit only | Zero frontend code, fastest to prototype | FastAPI + React (overkill for skeleton) |
| AI framework | Direct API calls | Transparent, simple, educational | LangChain (too many abstractions) |
| LLM | Claude Sonnet only | Good citations, cost-effective | GPT-4 (more expensive, second provider) |
| Embeddings | text-embedding-3-small | Cheap ($0.02/1M), good quality | ada-002 (older, 5x pricier), large (overkill) |
| Vector store | numpy in-memory (~50 lines) | Zero dependencies, no setup, replaced ChromaDB (SQLite bug) | ChromaDB (SQLite issues), Pinecone (cloud, $70/mo, overkill) |
| Chunk size | 500 tokens | Balanced: enough context, precise citations | 200 (too fragmented), 1000 (vague citations) |
| Overlap | 100 tokens (20%) | Prevents boundary-split information loss | 0 (info loss), 250 (too much duplication) |
| Tokenizer | tiktoken (cl100k_base) | Matches embedding model's tokenization | Word count (inaccurate) |
| Similarity metric | Cosine | Best for text similarity, length-invariant | L2/Euclidean (length-sensitive) |
| Top K results | 5 | Standard default, enough context | 3 (might miss), 10 (too much noise) |
| Max response tokens | 1,024 | Enough for detailed answer, stays focused | 256 (too short), 4096 (invites verbosity) |
| Python version | 3.11 | Stable, all packages have pre-built binaries | 3.14 (too new, tiktoken fails) |
| API key management | .env + python-dotenv | Simple, standard, git-safe | Hardcoded (security risk), env vars only (less portable) |

---

## 14. Complete Architecture Diagram

The full Walking Skeleton, from document upload to answer displayed — every component, every technology choice, every key parameter in one view.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DocuQuery AI — Walking Skeleton                      ║
║                     RAG Pipeline: Complete Architecture                      ║
╚══════════════════════════════════════════════════════════════════════════════╝


    USER                                                            EXTERNAL
   ══════                                                           SERVICES
                                                                    ════════

   ┌──────────────┐
   │  Upload .txt  │
   │    file       │
   └──────┬───────┘
          │
          ▼
╔═══════════════════════════════════════════════╗
║  STREAMLIT UI  (app.py)                       ║
║  Python web framework — single entry point    ║
║  Handles upload, input, display               ║
╚═══════════════════╤═══════════════════════════╝
                    │
    ════════════════╪════════════════════════════════════════
    DOCUMENT        │  PROCESSING (happens once per upload)
    INGESTION       │
    ════════════════╪════════════════════════════════════════
                    │
                    ▼
         ┌─────────────────────┐
         │  CHUNKER            │
         │  rag/chunker.py     │
         │                     │
         │  • tiktoken          │
         │    (cl100k_base)    │
         │  • 500 tokens/chunk │
         │  • 100 token overlap│
         │                     │
         │  IN: full text      │
         │  OUT: list of chunks│
         │   (text + metadata) │
         └──────────┬──────────┘
                    │
                    │  chunks = [{text, source,
                    │   chunk_index, char_start,
                    │   char_end}, ...]
                    │
                    ▼
         ┌─────────────────────┐         ┌─────────────────┐
         │  EMBEDDER           │────────▶│  OpenAI API     │
         │  rag/embedder.py    │         │                 │
         │                     │◀────────│  text-embedding │
         │  IN: list of texts  │         │  -3-small       │
         │  OUT: list of       │         │                 │
         │    vectors          │         │  $0.02/1M tokens│
         │    (1,536 dims each)│         └─────────────────┘
         └──────────┬──────────┘
                    │
                    │  embeddings = [[0.023, -0.089,
                    │   0.045, ...], ...]
                    │   (1,536 numbers per chunk)
                    │
                    ▼
         ┌─────────────────────┐
         │  STORE              │
         │  rag/store.py       │
         │                     │
         │  numpy arrays       │
         │  (in-memory)        │
         │  cosine similarity  │
         │                     │
         │  Stores:            │
         │  • chunk text       │
         │  • embedding vector │
         │  • metadata (source,│
         │    index, positions)│
         └──────────┬──────────┘
                    │
                    │  ✓ Document indexed
                    │    and ready for search
                    │
    ════════════════╪════════════════════════════════════════
    QUESTION        │  ANSWERING (happens per question)
    ANSWERING       │
    ════════════════╪════════════════════════════════════════
                    │
   ┌──────────────┐ │
   │  User types   │ │
   │  a question   │─┘
   └──────┬───────┘
          │
          ▼
         ┌─────────────────────┐         ┌─────────────────┐
         │  EMBEDDER           │────────▶│  OpenAI API     │
         │  (same module)      │         │                 │
         │                     │◀────────│  Same model     │
         │  IN: question text  │         │  Same encoding  │
         │  OUT: 1 vector      │         │                 │
         │    (1,536 dims)     │         └─────────────────┘
         └──────────┬──────────┘
                    │
                    │  question_vector = [0.012,
                    │   -0.034, 0.078, ...]
                    │
                    ▼
         ┌─────────────────────┐
         │  STORE              │
         │  (semantic search)  │
         │                     │
         │  "Find the 5 chunks │
         │   most similar to   │
         │   this question"    │
         │                     │
         │  Compares question  │
         │  vector against all │
         │  stored vectors     │
         │  using cosine       │
         │  similarity         │
         │                     │
         │  Returns: top 5     │
         │  chunks + distances │
         └──────────┬──────────┘
                    │
                    │  5 most relevant chunks
                    │  + similarity scores
                    │
                    ▼
         ┌─────────────────────┐         ┌─────────────────┐
         │  GENERATOR          │────────▶│  Anthropic API  │
         │  rag/generator.py   │         │                 │
         │                     │         │  Claude Sonnet  │
         │  1. Loads the       │         │                 │
         │     SYSTEM PROMPT   │◀────────│  ~$3/1M tokens  │
         │     (4 rules:       │         │  in             │
         │     answer from     │         │  ~$15/1M tokens │
         │     context only,   │         │  out            │
         │     cite sources,   │         │                 │
         │     be concise,     │         └─────────────────┘
         │     never invent)   │
         │                     │
         │  2. Formats the 5   │
         │     chunks into a   │
         │     structured      │
         │     context block   │
         │                     │
         │  3. Sends to Claude:│
         │     system prompt + │
         │     context + question
         │                     │
         │  Max: 1,024 tokens  │
         └──────────┬──────────┘
                    │
                    │  Answer with citations:
                    │  "The four phases are...
                    │   [Source: doc.txt, Chunk 0]"
                    │
                    ▼
╔═══════════════════════════════════════════════╗
║  STREAMLIT UI                                 ║
║                                               ║
║  ┌──────────────────────────────────────────┐ ║
║  │  Answer                                  │ ║
║  │  The four phases are FRAME, BUILD,       │ ║
║  │  EVALUATE, and SHIP [Source: doc, Ch.0]  │ ║
║  └──────────────────────────────────────────┘ ║
║                                               ║
║  ▸ Retrieved chunks (debug)                   ║
║    Chunk 0 (distance: 0.1234)                 ║
║    Chunk 2 (distance: 0.2891)                 ║
║    Chunk 1 (distance: 0.3456)                 ║
╚═══════════════════════════════════════════════╝
          │
          ▼
   ┌──────────────┐
   │  User reads   │
   │  the answer   │
   └──────────────┘


╔══════════════════════════════════════════════════════════════════════════════╗
║                              KEY PARAMETERS                                 ║
╠═══════════════════════╦═════════════════════╦════════════════════════════════╣
║  Chunking             ║  Search             ║  Generation                    ║
╠═══════════════════════╬═════════════════════╬════════════════════════════════╣
║  500 tokens/chunk     ║  Top K = 5 results  ║  Model: Claude Sonnet          ║
║  100 tokens overlap   ║  Cosine similarity  ║  Max tokens: 1,024            ║
║  Tokenizer: cl100k    ║  numpy (in-memory)  ║  System prompt: 4 rules       ║
╚═══════════════════════╩═════════════════════╩════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                            TECHNOLOGY STACK                                 ║
╠══════════════════╦══════════════════╦════════════════╦════════════════════════╣
║  UI              ║  Pipeline        ║  Storage       ║  AI Services           ║
╠══════════════════╬══════════════════╬════════════════╬════════════════════════╣
║  Streamlit       ║  Python 3.11     ║  numpy arrays  ║  OpenAI (embeddings)   ║
║  (temporary)     ║  tiktoken        ║  (in-memory)   ║  Anthropic (answers)   ║
║                  ║  python-dotenv   ║                ║                        ║
╚══════════════════╩══════════════════╩════════════════╩════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                            COST PER QUERY                                   ║
║                                                                             ║
║  Embed question:  ~$0.000002  (1 question, ~20 tokens)                      ║
║  Generate answer: ~$0.003     (context + question ≈ 1,000 tokens in)        ║
║  Vector search:   $0          (local, numpy in-memory)                      ║
║  ─────────────────────────────────────────                                  ║
║  Total per query: ~$0.003     (≈ 333 questions per dollar)                  ║
║                                                                             ║
║  One-time per document:                                                     ║
║  Embed all chunks: ~$0.00002  (500 tokens × 3 chunks for test doc)          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## What's next

The Walking Skeleton is done. According to the Builder PM Method:

1. **Skeleton Check: PASSED** → Continue to Scopes
2. **Scope 1: PDF + CSV parsing** → Add file format support with page-level citations
3. **Scope 2: Citation precision + error handling** → Paragraph-level citations, edge cases
4. **Scope 3: UI polish (Lovable)** → Clean interface for non-technical users

If the Cycle runs out of time, cut from the bottom: Scope 3 first, then Scope 2. The Walking Skeleton is already a functional product.
