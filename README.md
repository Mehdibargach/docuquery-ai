# DocuQuery AI

> RAG-powered Q&A system for document analysis

Ask questions in natural language about your documents and get answers with citations.

## Overview

DocuQuery AI is a Retrieval-Augmented Generation (RAG) system that enables intelligent document querying. Upload PDFs, contracts, or technical documentation and get precise answers backed by source citations.

## Features

- 📄 **Document Upload** - Support for PDF, TXT, DOCX
- 🔍 **Semantic Search** - Vector-based retrieval using embeddings
- 💬 **Natural Language Q&A** - Ask questions conversationally
- 📌 **Source Citations** - Every answer includes relevant passages
- ⚡ **Fast Retrieval** - Optimized chunking and indexing

## Tech Stack

### Backend
- **LLM**: Claude/GPT-4 for answer generation
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: Pinecone / Chroma
- **Framework**: FastAPI (Python)

### Frontend
- **UI**: Built with Lovable
- **Hosting**: Vercel

### Infrastructure
- **Backend Deploy**: Railway / Render
- **Storage**: S3 for document storage

## Architecture

```
Document Upload → Chunking → Embeddings → Vector DB
                                              ↓
User Query → Embedding → Semantic Search → Top K chunks
                                              ↓
                         LLM (with context) → Answer + Citations
```

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- API keys: OpenAI, Anthropic

### Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# Frontend
cd frontend
npm install
cp .env.example .env.local  # Add backend URL
```

### Run Locally

```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

## Usage

1. **Upload Document**: Drop PDF/TXT file in upload zone
2. **Processing**: System chunks document and creates embeddings
3. **Ask Questions**: Type your question in natural language
4. **Get Answers**: Receive answer with highlighted source passages

## Example Queries

- "What are the termination clauses in this contract?"
- "Summarize the key findings from section 3"
- "What is the refund policy?"

## Deployment

### Backend (Railway)
```bash
railway init
railway add
railway up
```

### Frontend (Vercel)
```bash
vercel --prod
```

## Roadmap

- [x] Basic RAG pipeline
- [x] Document upload and chunking
- [x] Semantic search and retrieval
- [x] Answer generation with citations
- [ ] Multi-document support
- [ ] Advanced chunking strategies
- [ ] Query history and caching
- [ ] Support for images/tables in PDFs

## Built With

Part of **The Builder PM** methodology — demonstrating hands-on AI product development.

**Build → Evaluate → Ship**

---

**Author**: Mehdi Bargach | [LinkedIn](https://linkedin.com/in/mehdibargach) | [The Builder PM](https://substack.com/@thebuilderpm)

**License**: MIT
